"""Load the built-in (system) decks. Safe to run repeatedly."""

from django.core.management.base import BaseCommand
from django.db import transaction

from decks.data.kana import kana_decks
from decks.models import Card, Deck


class Command(BaseCommand):
    help = "Ładuje talie systemowe (hiragana i katakana). Można uruchamiać wielokrotnie."

    @transaction.atomic
    def handle(self, *args, **options):
        created_decks = created_cards = 0
        for deck_order, (name, description, entries) in enumerate(kana_decks(), start=1):
            deck, created = Deck.objects.update_or_create(
                owner=None, name=name,
                defaults={"description": description, "kind": Deck.Kind.KANA, "order": deck_order},
            )
            created_decks += created
            for card_order, (kana, romaji) in enumerate(entries, start=1):
                _, created = Card.objects.update_or_create(
                    deck=deck, front=kana, defaults={"back": romaji, "order": card_order},
                )
                created_cards += created
        self.stdout.write(self.style.SUCCESS(
            f"Gotowe: nowe talie {created_decks}, nowe karty {created_cards} "
            f"(łącznie talii systemowych: {Deck.objects.filter(owner=None).count()}, "
            f"kart: {Card.objects.filter(deck__owner=None).count()})."
        ))
