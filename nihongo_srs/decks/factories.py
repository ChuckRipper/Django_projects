"""Building Card objects for a given deck type (Factory Method pattern).

Each deck kind has its own factory that knows which fields make sense and how
to validate them; callers use ``CardFactory.for_deck(deck).build(data)`` and
never branch on the deck type themselves.
"""

from abc import ABC, abstractmethod

from django.core.exceptions import ValidationError

from .models import Card, Deck
from .sources import CardData


class CardFactory(ABC):
    def __init__(self, deck: Deck):
        self.deck = deck

    @classmethod
    def for_deck(cls, deck: Deck) -> "CardFactory":
        factories = {
            Deck.Kind.KANA: KanaCardFactory,
            Deck.Kind.VOCABULARY: VocabularyCardFactory,
            Deck.Kind.KANJI: KanjiCardFactory,
        }
        return factories[deck.kind](deck)

    def build(self, data: CardData) -> Card:
        self.validate(data)
        return Card(deck=self.deck, **self.fields(data))

    def validate(self, data: CardData) -> None:
        if not data.front.strip() or not data.back.strip():
            raise ValidationError("Karta musi mieć przód i tył.")
        if len(data.front) > Card._meta.get_field("front").max_length:
            raise ValidationError("Przód karty jest za długi.")

    @abstractmethod
    def fields(self, data: CardData) -> dict:
        """Model field values for this kind of card."""


class KanaCardFactory(CardFactory):
    def fields(self, data):
        return {"front": data.front, "back": data.back}


class VocabularyCardFactory(CardFactory):
    def fields(self, data):
        return {
            "front": data.front, "back": data.back[:255], "reading": data.reading,
            "example": data.example, "meaning_en": data.meaning_en[:255],
        }


class KanjiCardFactory(CardFactory):
    def validate(self, data):
        super().validate(data)
        if len(data.front) != 1:
            raise ValidationError(f"Karta kanji musi zawierać dokładnie jeden znak („{data.front}”).")

    def fields(self, data):
        return {
            "front": data.front, "back": data.back[:255], "reading": data.reading,
            "example": data.example[:255], "onyomi": data.onyomi[:100], "kunyomi": data.kunyomi[:100],
            "stroke_count": data.stroke_count, "meaning_en": data.meaning_en[:255],
        }
