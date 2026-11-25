"""Build data/cards.json from data/src/*.txt.

Source line format (pipe separated):
  level|word|reading|pos|meaning_en|meaning_sv|sentence|translation_en|translation_sv

In the sentence, wrap the target word's surface form in [brackets].
Use {漢字|よみ} to force a reading where auto-furigana gets it wrong.

Furigana is generated with fugashi + unidic-lite (dev-only dependency):
  pip install fugashi unidic-lite
"""
import json
import re
import sys
from pathlib import Path

import fugashi

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "data" / "src"
OUT = ROOT / "data" / "cards.json"

KANJI = re.compile(r"[㐀-鿿々]")  # includes 々
tagger = fugashi.Tagger()


def kata2hira(s: str) -> str:
    return "".join(chr(ord(c) - 0x60) if "ァ" <= c <= "ヶ" else c for c in s)


def align(surface: str, reading: str):
    """Split a surface+reading pair into segments, putting furigana only over kanji runs."""
    if not KANJI.search(surface) or not reading:
        return [{"t": surface}]
    reading = kata2hira(reading)
    # Strip shared kana prefix / suffix (okurigana, honorific お etc.)
    pre = 0
    while pre < len(surface) and pre < len(reading) and not KANJI.match(surface[pre]) and kata2hira(surface[pre]) == reading[pre]:
        pre += 1
    suf = 0
    while (suf < len(surface) - pre and suf < len(reading) - pre
           and not KANJI.match(surface[-1 - suf]) and kata2hira(surface[-1 - suf]) == reading[-1 - suf]):
        suf += 1
    core_s = surface[pre:len(surface) - suf]
    core_r = reading[pre:len(reading) - suf]
    segs = []
    if pre:
        segs.append({"t": surface[:pre]})
    # Try to split a core like 食べ物 (kanji-kana-kanji) on its inner kana
    inner = re.split(r"([^㐀-鿿々]+)", core_s)
    if len(inner) == 3 and inner[1] and kata2hira(inner[1]) in core_r[1:]:
        k1, kana, k2 = inner
        i = core_r.find(kata2hira(kana), 1)
        segs += [{"t": k1, "r": core_r[:i]}, {"t": kana}, {"t": k2, "r": core_r[i + len(kana):]}]
    else:
        segs.append({"t": core_s, "r": core_r} if core_r else {"t": core_s})
    if suf:
        segs.append({"t": surface[len(surface) - suf:]})
    return segs


def auto_segments(text: str):
    segs = []
    for w in tagger(text):
        kana = getattr(w.feature, "kana", None)
        segs += align(w.surface, kana or "")
    return segs


TOKEN = re.compile(r"\{([^|}]+)\|([^}]+)\}")


def parse_part(text: str):
    """Text possibly containing {漢字|よみ} overrides."""
    segs, pos = [], 0
    for m in TOKEN.finditer(text):
        if m.start() > pos:
            segs += auto_segments(text[pos:m.start()])
        segs.append({"t": m.group(1), "r": m.group(2)})
        pos = m.end()
    if pos < len(text):
        segs += auto_segments(text[pos:])
    return segs


def merge(segs):
    out = []
    for s in segs:
        if out and "r" not in s and "r" not in out[-1] and s.get("x") == out[-1].get("x"):
            out[-1]["t"] += s["t"]
        else:
            out.append(dict(s))
    return out


# Readings the tagger gets wrong in these contexts -> forced overrides
FIXES = [
    ("誕生日", "{誕生日|たんじょうび}"), ("日曜日", "{日曜日|にちようび}"), ("何曜日", "{何曜日|なんようび}"),
    ("富士山", "{富士山|ふじさん}"), ("一日で", "{一日|いちにち}で"), ("一日三回", "{一日|いちにち}三回"),
    ("四つ", "{四|よっ}つ"), ("洗濯物", "{洗濯物|せんたくもの}"), ("九時", "{九時|くじ}"),
    ("四人", "{四人|よにん}"), ("箱", "{箱|はこ}"), ("角", "{角|かど}"), ("十分[遅", "{十分|じゅっぷん}[遅"),
    ("私", "{私|わたし}"), ("日本", "{日本|にほん}"), ("明日", "{明日|あした}"), ("世界中", "{世界中|せかいじゅう}"),
    ("深い", "{深|ふか}い"), ("辛い", "{辛|から}い"), ("空き", "{空|す}き"),
]


def apply_fixes(sentence: str) -> str:
    for a, b in FIXES:
        sentence = sentence.replace(a, b)
    return sentence


def build_sentence(sentence: str):
    sentence = apply_fixes(sentence)
    m =re.match(r"^(.*?)\[(.+?)\](.*)$", sentence)
    if not m:
        raise ValueError("no [target] in: " + sentence)
    before, target, after = m.groups()
    segs = parse_part(before)
    tseg = parse_part(target)
    for s in tseg:
        s["x"] = 1  # marks target
    segs += tseg + parse_part(after)
    plain = re.sub(TOKEN, r"\1", sentence).replace("[", "").replace("]", "")
    return merge(segs), re.sub(TOKEN, r"\1", target), plain


def main():
    cards, warnings = [], []
    cid = 0
    for f in sorted(SRC.glob("*.txt")):
        for line in f.read_text(encoding="utf-8").splitlines():
            if not line.strip() or line.startswith("#"):
                continue
            p = line.split("|")
            if len(p) != 9:
                sys.exit(f"bad line in {f.name}: {line}")
            level, word, reading, pos, men, msv, sentence, ten, tsv = [x.strip() for x in p]
            segs, surface, plain = build_sentence(sentence)
            cid += 1
            word_segs = merge(align(word, reading)) if KANJI.search(word) else [{"t": word}]
            cards.append({
                "id": cid, "level": level, "word": word, "reading": reading, "pos": pos,
                "meaning": {"en": men, "sv": msv},
                "sentence": segs, "surface": surface, "plain": plain,
                "translation": {"en": ten, "sv": tsv},
                "word_furi": word_segs,
                "has_kanji": bool(KANJI.search(word)),
            })
            # sanity: target reading from tagger should start like the dictionary reading
            tr = "".join(s.get("r", s["t"]) for s in segs if s.get("x"))
            if KANJI.search(surface) and tr[:1] != reading[:1]:
                warnings.append(f"{word}: target reading '{tr}' vs '{reading}'")
    OUT.write_text(json.dumps(cards, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"wrote {len(cards)} cards -> {OUT}")
    for w in warnings:
        print("WARN", w)


if __name__ == "__main__":
    main()
