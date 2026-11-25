"""Romaji -> hiragana conversion for typed reading answers."""

_T = {
    "a": "あ", "i": "い", "u": "う", "e": "え", "o": "お",
    "ka": "か", "ki": "き", "ku": "く", "ke": "け", "ko": "こ",
    "ga": "が", "gi": "ぎ", "gu": "ぐ", "ge": "げ", "go": "ご",
    "sa": "さ", "si": "し", "shi": "し", "su": "す", "se": "せ", "so": "そ",
    "za": "ざ", "zi": "じ", "ji": "じ", "zu": "ず", "ze": "ぜ", "zo": "ぞ",
    "ta": "た", "ti": "ち", "chi": "ち", "tu": "つ", "tsu": "つ", "te": "て", "to": "と",
    "da": "だ", "di": "ぢ", "du": "づ", "de": "で", "do": "ど",
    "na": "な", "ni": "に", "nu": "ぬ", "ne": "ね", "no": "の",
    "ha": "は", "hi": "ひ", "hu": "ふ", "fu": "ふ", "he": "へ", "ho": "ほ",
    "ba": "ば", "bi": "び", "bu": "ぶ", "be": "べ", "bo": "ぼ",
    "pa": "ぱ", "pi": "ぴ", "pu": "ぷ", "pe": "ぺ", "po": "ぽ",
    "ma": "ま", "mi": "み", "mu": "む", "me": "め", "mo": "も",
    "ya": "や", "yu": "ゆ", "yo": "よ",
    "ra": "ら", "ri": "り", "ru": "る", "re": "れ", "ro": "ろ",
    "la": "ら", "li": "り", "lu": "る", "le": "れ", "lo": "ろ",
    "wa": "わ", "wi": "ゐ", "we": "ゑ", "wo": "を",
    "kya": "きゃ", "kyu": "きゅ", "kyo": "きょ",
    "gya": "ぎゃ", "gyu": "ぎゅ", "gyo": "ぎょ",
    "sha": "しゃ", "shu": "しゅ", "sho": "しょ", "she": "しぇ",
    "sya": "しゃ", "syu": "しゅ", "syo": "しょ",
    "ja": "じゃ", "ju": "じゅ", "jo": "じょ", "je": "じぇ",
    "jya": "じゃ", "jyu": "じゅ", "jyo": "じょ", "zya": "じゃ", "zyu": "じゅ", "zyo": "じょ",
    "cha": "ちゃ", "chu": "ちゅ", "cho": "ちょ", "che": "ちぇ",
    "tya": "ちゃ", "tyu": "ちゅ", "tyo": "ちょ", "cya": "ちゃ", "cyu": "ちゅ", "cyo": "ちょ",
    "nya": "にゃ", "nyu": "にゅ", "nyo": "にょ",
    "hya": "ひゃ", "hyu": "ひゅ", "hyo": "ひょ",
    "bya": "びゃ", "byu": "びゅ", "byo": "びょ",
    "pya": "ぴゃ", "pyu": "ぴゅ", "pyo": "ぴょ",
    "mya": "みゃ", "myu": "みゅ", "myo": "みょ",
    "rya": "りゃ", "ryu": "りゅ", "ryo": "りょ",
    "fa": "ふぁ", "fi": "ふぃ", "fe": "ふぇ", "fo": "ふぉ",
    "xtu": "っ", "xtsu": "っ", "ltu": "っ", "xya": "ゃ", "xyu": "ゅ", "xyo": "ょ",
    "-": "ー",
}
_VOWELS = set("aiueo")
_MACRON = {"ā": "aa", "ī": "ii", "ū": "uu", "ē": "ee", "ō": "ou", "â": "aa", "î": "ii", "û": "uu", "ê": "ee", "ô": "ou"}


def kata2hira(s: str) -> str:
    return "".join(chr(ord(c) - 0x60) if "ァ" <= c <= "ヶ" else c for c in s)


def to_hiragana(text: str) -> str:
    s = kata2hira(text.strip().lower())
    for k, v in _MACRON.items():
        s = s.replace(k, v)
    s = s.replace(" ", "").replace("　", "")
    out, i = [], 0
    while i < len(s):
        c = s[i]
        if not ("a" <= c <= "z" or c == "-" or c == "'"):
            out.append(c)
            i += 1
            continue
        if c == "'":
            i += 1
            continue
        nxt = s[i + 1] if i + 1 < len(s) else ""
        if c == "n":
            if nxt == "n":
                after = s[i + 2] if i + 2 < len(s) else ""
                out.append("ん")
                i += 2 if (not after or after not in _VOWELS and after != "y") else 1
                continue
            if not nxt or (nxt not in _VOWELS and nxt != "y"):
                out.append("ん")
                i += 1
                continue
        if c == nxt and c not in _VOWELS and c != "n" and c.isalpha():
            out.append("っ")
            i += 1
            continue
        if c == "t" and s[i:i + 3] == "tch":  # matcha
            out.append("っ")
            i += 1
            continue
        for ln in (4, 3, 2, 1):
            chunk = s[i:i + ln]
            if chunk in _T:
                out.append(_T[chunk])
                i += ln
                break
        else:
            out.append(c)
            i += 1
    return "".join(out)


def reading_matches(answer: str, reading: str) -> bool:
    a = to_hiragana(answer)
    r = kata2hira(reading)
    if a == r:
        return True
    # tolerate は/わ, を/お, づ/ず, ぢ/じ confusion
    norm = str.maketrans({"を": "お", "づ": "ず", "ぢ": "じ"})
    return a.translate(norm) == r.translate(norm)
