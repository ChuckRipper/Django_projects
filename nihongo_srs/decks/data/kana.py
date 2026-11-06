"""Hiragana and katakana tables (generated, no external data needed).

Each entry: (kana, romaji). Katakana is derived from hiragana by the fixed
Unicode offset between both blocks (U+3041..U+3096 -> U+30A1..U+30F6).
"""

BASIC = [
    ("あ", "a"), ("い", "i"), ("う", "u"), ("え", "e"), ("お", "o"),
    ("か", "ka"), ("き", "ki"), ("く", "ku"), ("け", "ke"), ("こ", "ko"),
    ("さ", "sa"), ("し", "shi"), ("す", "su"), ("せ", "se"), ("そ", "so"),
    ("た", "ta"), ("ち", "chi"), ("つ", "tsu"), ("て", "te"), ("と", "to"),
    ("な", "na"), ("に", "ni"), ("ぬ", "nu"), ("ね", "ne"), ("の", "no"),
    ("は", "ha"), ("ひ", "hi"), ("ふ", "fu"), ("へ", "he"), ("ほ", "ho"),
    ("ま", "ma"), ("み", "mi"), ("む", "mu"), ("め", "me"), ("も", "mo"),
    ("や", "ya"), ("ゆ", "yu"), ("よ", "yo"),
    ("ら", "ra"), ("り", "ri"), ("る", "ru"), ("れ", "re"), ("ろ", "ro"),
    ("わ", "wa"), ("を", "wo"), ("ん", "n"),
]

DAKUTEN = [
    ("が", "ga"), ("ぎ", "gi"), ("ぐ", "gu"), ("げ", "ge"), ("ご", "go"),
    ("ざ", "za"), ("じ", "ji"), ("ず", "zu"), ("ぜ", "ze"), ("ぞ", "zo"),
    ("だ", "da"), ("ぢ", "ji (di)"), ("づ", "zu (du)"), ("で", "de"), ("ど", "do"),
    ("ば", "ba"), ("び", "bi"), ("ぶ", "bu"), ("べ", "be"), ("ぼ", "bo"),
    ("ぱ", "pa"), ("ぴ", "pi"), ("ぷ", "pu"), ("ぺ", "pe"), ("ぽ", "po"),
]

YOON = [
    ("きゃ", "kya"), ("きゅ", "kyu"), ("きょ", "kyo"),
    ("しゃ", "sha"), ("しゅ", "shu"), ("しょ", "sho"),
    ("ちゃ", "cha"), ("ちゅ", "chu"), ("ちょ", "cho"),
    ("にゃ", "nya"), ("にゅ", "nyu"), ("にょ", "nyo"),
    ("ひゃ", "hya"), ("ひゅ", "hyu"), ("ひょ", "hyo"),
    ("みゃ", "mya"), ("みゅ", "myu"), ("みょ", "myo"),
    ("りゃ", "rya"), ("りゅ", "ryu"), ("りょ", "ryo"),
    ("ぎゃ", "gya"), ("ぎゅ", "gyu"), ("ぎょ", "gyo"),
    ("じゃ", "ja"), ("じゅ", "ju"), ("じょ", "jo"),
    ("びゃ", "bya"), ("びゅ", "byu"), ("びょ", "byo"),
    ("ぴゃ", "pya"), ("ぴゅ", "pyu"), ("ぴょ", "pyo"),
]

_HIRAGANA_TO_KATAKANA = {code: code + 0x60 for code in range(0x3041, 0x3097)}


def to_katakana(text: str) -> str:
    return text.translate(_HIRAGANA_TO_KATAKANA)


# (deck name, description, entries) - order defines the learning order of decks.
def kana_decks():
    groups = [
        ("podstawowe znaki", "46 znaków podstawowych (gojūon).", BASIC),
        ("dakuten i handakuten", "Znaki z udźwięcznieniem (゛) i znakiem ゜.", DAKUTEN),
        ("połączenia (yōon)", "Sylaby z małymi ゃ, ゅ, ょ.", YOON),
    ]
    decks = []
    for script, convert in (("Hiragana", lambda s: s), ("Katakana", to_katakana)):
        for title, description, entries in groups:
            decks.append((
                f"{script} – {title}",
                f"{script}: {description}",
                [(convert(kana), romaji) for kana, romaji in entries],
            ))
    return decks
