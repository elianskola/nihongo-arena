import json
import random
from pathlib import Path

CARDS_PATH = Path(__file__).resolve().parent.parent / "data" / "cards.json"
LEVELS = ["N5", "N4", "N3"]

CARDS = {c["id"]: c for c in json.loads(CARDS_PATH.read_text(encoding="utf-8"))}
BY_LEVEL = {lv: [c for c in CARDS.values() if c["level"] == lv] for lv in LEVELS}
QTYPES = ["meaning", "cloze", "reading", "translate"]


def level_for_rating(r: float) -> str:
    if r < 1000:
        return "N5"
    if r < 1300:
        return "N4"
    return "N3"


def furi_tier(r: float) -> str:
    """How much furigana a player sees: full -> target only -> hover to reveal."""
    if r < 1000:
        return "full"
    if r < 1400:
        return "target"
    return "hover"


def _distractors(card, n, key, same_pos=True):
    """Pick n other cards whose `key` text differs from the target's."""
    lv_idx = LEVELS.index(card["level"])
    pools = [BY_LEVEL[card["level"]]] + [BY_LEVEL[LEVELS[i]] for i in range(len(LEVELS)) if i != lv_idx]
    seen = {key(card)}
    out = []
    for pos_filter in ([True, False] if same_pos else [False]):
        for pool in pools:
            cand = [c for c in pool if c["id"] != card["id"] and (not pos_filter or c["pos"] == card["pos"])]
            random.shuffle(cand)
            for c in cand:
                k = key(c)
                if k not in seen:
                    seen.add(k)
                    out.append(c)
                    if len(out) == n:
                        return out
    return out


def make_question(card, qtype=None):
    if qtype is None:
        types = QTYPES if card["has_kanji"] else [t for t in QTYPES if t != "reading"]
        qtype = random.choice(types)
    q = {"t": qtype, "c": card["id"]}
    if qtype == "meaning":
        opts = [card] + _distractors(card, 3, lambda c: c["meaning"]["en"])
    elif qtype == "cloze":
        opts = [card] + _distractors(card, 3, lambda c: c["word"])
    elif qtype == "translate":
        opts = [card] + _distractors(card, 3, lambda c: c["translation"]["en"], same_pos=False)
    else:
        return q
    ids = [c["id"] for c in opts]
    random.shuffle(ids)
    q["o"] = ids
    return q


def build_question_set(avg_rating: float, count: int):
    level = level_for_rating(avg_rating)
    li = LEVELS.index(level)
    main = BY_LEVEL[level][:]
    lower = [c for lv in LEVELS[:li] for c in BY_LEVEL[lv]]
    random.shuffle(main)
    random.shuffle(lower)
    picked = []
    while len(picked) < count:
        if lower and random.random() < 0.2:
            picked.append(lower.pop())
        elif main:
            picked.append(main.pop())
        elif lower:
            picked.append(lower.pop())
        else:  # exhausted: refill
            main = BY_LEVEL[level][:]
            random.shuffle(main)
    # avoid long runs of the same type: cycle through a shuffled bag
    bag = []
    qs = []
    for c in picked:
        if not bag:
            bag = QTYPES[:]
            random.shuffle(bag)
        t = bag.pop()
        if t == "reading" and not c["has_kanji"]:
            t = random.choice(["meaning", "cloze", "translate"])
        qs.append(make_question(c, t))
    return level, qs


def _sentence(card, mode, hide_target_furi=False):
    segs = []
    for s in card["sentence"]:
        if mode == "cloze" and s.get("x"):
            if not segs or segs[-1].get("blank") is None:
                segs.append({"blank": True})
            continue
        d = {"t": s["t"]}
        if "r" in s and not (hide_target_furi and s.get("x")):
            d["r"] = s["r"]
        if s.get("x"):
            d["x"] = 1
        segs.append(d)
    return segs


def render_question(q, lang: str, tier: str):
    """Player-facing view of a question (never contains the answer)."""
    card = CARDS[q["c"]]
    t = q["t"]
    out = {"type": t, "tier": tier, "level": card["level"]}
    if t == "meaning":
        out["sentence"] = _sentence(card, "normal")
        out["word"] = card["word"]
        out["options"] = [CARDS[i]["meaning"][lang] for i in q["o"]]
    elif t == "cloze":
        out["sentence"] = _sentence(card, "cloze")
        out["hint"] = card["translation"][lang]
        out["options"] = [CARDS[i]["word"] for i in q["o"]]
    elif t == "translate":
        out["sentence"] = _sentence(card, "normal")
        out["options"] = [CARDS[i]["translation"][lang] for i in q["o"]]
    else:  # reading
        out["sentence"] = _sentence(card, "normal", hide_target_furi=True)
        out["word"] = card["word"]
    return out


def card_reveal(card_id, lang):
    c = CARDS[card_id]
    return {
        "id": c["id"], "level": c["level"], "word": c["word"], "reading": c["reading"],
        "word_furi": c["word_furi"], "meaning": c["meaning"][lang],
        "sentence": c["sentence"], "translation": c["translation"][lang], "pos": c["pos"],
    }


def correct_answer_text(q, lang):
    card = CARDS[q["c"]]
    return {"meaning": card["meaning"][lang], "cloze": card["word"],
            "translate": card["translation"][lang], "reading": card["reading"]}[q["t"]]
