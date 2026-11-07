"""Typed-answer mode: decides which cards can be answered by typing and what is accepted.

The browser compares answers after converting both sides with WanaKana's toHiragana,
so "shi" and "si", or katakana and hiragana, count as the same answer.
"""

import re
from dataclasses import dataclass, field

from decks.models import Card, Deck

ROMAJI_RE = re.compile(r"[a-z]+")
READING_SEPARATORS = re.compile(r"[;；、,，/]")
NOT_KANA_RE = re.compile(r"[^ぁ-ゖァ-ヺー]")


@dataclass
class TypingTask:
    prompt: str
    placeholder: str
    answers: list[str] = field(default_factory=list)
    kana_input: bool = False  # convert romaji to kana while typing (WanaKana IME mode)


def typing_task(card: Card) -> TypingTask | None:
    """Return what to ask for when the card is answered by typing, or None (reveal instead)."""
    kind = card.deck.kind
    if kind == Deck.Kind.KANA:
        romaji = ROMAJI_RE.findall(card.back.lower())  # "ji (di)" -> ["ji", "di"]
        return TypingTask("Wpisz zapis w romaji", "np. ka", [card.front, *romaji])
    if kind == Deck.Kind.VOCABULARY and card.reading:
        variants = [NOT_KANA_RE.sub("", part) for part in READING_SEPARATORS.split(card.reading)]
        answers = [variant for variant in variants if variant]
        if answers:
            return TypingTask(
                "Wpisz odczyt", "np. neko → ねこ", answers, kana_input=True,
            )
    return None  # kanji, and words written only in kana (nothing to read): reveal
