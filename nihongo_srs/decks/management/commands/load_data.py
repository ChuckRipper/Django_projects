"""Load the built-in (system) decks. Safe to run repeatedly - existing cards are updated."""

from pathlib import Path

from django.core.management.base import BaseCommand
from django.db import transaction

from decks.data.kana import kana_decks
from decks.models import Card, Deck
from decks.services import import_cards
from decks.sources import KANJI_RE, JlptVocabSource, KanjiDataSource

DATA_DIR = Path(__file__).resolve().parents[2] / "data"
KANJI_LEVELS = (("N5", 5), ("N4", 4), ("N3", 3), ("N2", 2), ("N1", 1))
VOCAB_LEVELS = ("N5", "N4", "N3", "N2", "N1")


def kanji_examples(vocab_sources, limit=2):
    """For every kanji, pick up to ``limit`` example words from the vocabulary lists."""
    examples = {}
    for source in vocab_sources:
        for card in source:
            for char in set(KANJI_RE.findall(card.front)):
                words = examples.setdefault(char, [])
                if len(words) < limit:
                    reading = f" ({card.reading})" if card.reading else ""
                    words.append(f"{card.front}{reading} – {card.back.split(' / ')[0]}")
    return {char: "; ".join(words) for char, words in examples.items()}


class Command(BaseCommand):
    help = "Ładuje talie systemowe: kana, kanji i słownictwo JLPT N5–N1. Można uruchamiać wielokrotnie."

    def deck(self, name, kind, order, description, level=""):
        deck, _ = Deck.objects.update_or_create(
            owner=None, name=name,
            defaults={"kind": kind, "order": order, "description": description, "jlpt_level": level},
        )
        return deck

    def report(self, deck, result):
        self.stdout.write(
            f"  {deck.name}: nowe {result.created}, zaktualizowane {result.updated}"
            + (f", błędy {len(result.errors)}" if result.errors else "")
        )

    @transaction.atomic
    def handle(self, *args, **options):
        order = 0
        for order, (name, description, entries) in enumerate(kana_decks(), start=1):
            deck = self.deck(name, Deck.Kind.KANA, order, description)
            created = 0
            for card_order, (kana, romaji) in enumerate(entries, start=1):
                _, was_created = Card.objects.update_or_create(
                    deck=deck, front=kana, defaults={"back": romaji, "order": card_order},
                )
                created += was_created
            self.stdout.write(f"  {deck.name}: nowe {created}")

        # Vocabulary N5 -> N1. A word listed on several levels is taught on the lowest one.
        vocab_sources, taught = {}, set()
        for level in VOCAB_LEVELS:
            translations = DATA_DIR / f"vocab_{level.lower()}_pl.tsv"
            exclude = frozenset() if level in ("N5", "N4") else frozenset(taught)
            source = JlptVocabSource(
                DATA_DIR / f"jlpt_vocab_{level.lower()}.csv",
                translations if translations.exists() else None,
                exclude=exclude,
                clean_notes=level not in ("N5", "N4"),
            )
            vocab_sources[level] = source
            taught.update(card.front for card in source)
        examples = kanji_examples(vocab_sources.values())

        for level, number in KANJI_LEVELS:
            order += 1
            deck = self.deck(
                f"Kanji {level}", Deck.Kind.KANJI, order,
                f"Znaki kanji z poziomu JLPT {level}, od najczęściej używanych.", level,
            )
            data_file = "kanji_n5_n4.json" if number >= 4 else "kanji_n3_n1.json"
            source = KanjiDataSource(DATA_DIR / data_file, number, DATA_DIR / "kanji_pl.tsv", examples)
            self.report(deck, import_cards(deck, source))

        for level in VOCAB_LEVELS:
            order += 1
            deck = self.deck(
                f"Słownictwo {level}", Deck.Kind.VOCABULARY, order,
                f"Słownictwo z poziomu JLPT {level}, znaczenia po polsku.", level,
            )
            self.report(deck, import_cards(deck, vocab_sources[level]))

        self.stdout.write(self.style.SUCCESS(
            f"Gotowe: talie systemowe {Deck.objects.filter(owner=None).count()}, "
            f"karty {Card.objects.filter(deck__owner=None).count()}."
        ))
