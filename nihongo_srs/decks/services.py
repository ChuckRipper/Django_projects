"""Deck use cases: importing cards from any CardSource and exporting a deck to CSV."""

import csv
import io
from collections.abc import Iterable
from dataclasses import dataclass, field

from django.core.exceptions import ValidationError
from django.db import transaction

from .factories import CardFactory
from .models import Card, Deck
from .sources import CardData, CardSource, SourceError

EXPORT_COLUMNS = ["front", "back", "reading", "example", "onyomi", "kunyomi", "stroke_count", "meaning_en"]


@dataclass
class ImportReport:
    created: int = 0
    updated: int = 0
    skipped: int = 0
    errors: list[SourceError] = field(default_factory=list)

    @property
    def ok(self):
        return not self.errors


@transaction.atomic
def import_cards(deck: Deck, source: Iterable[CardData] | CardSource, update_existing: bool = True) -> ImportReport:
    """Create (or update) cards in ``deck`` from any source adapter (or a plain list of CardData)."""
    report = ImportReport()
    factory = CardFactory.for_deck(deck)
    existing = {card.front: card for card in deck.cards.all()}
    next_order = max((card.order for card in existing.values()), default=0) + 1
    to_create = []

    for position, data in enumerate(source, start=1):
        try:
            card = factory.build(data)
        except ValidationError as exc:
            report.errors.append(SourceError(data.line or position, "; ".join(exc.messages)))
            continue
        current = existing.get(card.front) or next((c for c in to_create if c.front == card.front), None)
        if current is not None:
            if not update_existing or current.pk is None:
                report.skipped += 1
                continue
            for name in EXPORT_COLUMNS:
                setattr(current, name, getattr(card, name))
            current.save()
            report.updated += 1
        else:
            card.order = next_order
            next_order += 1
            to_create.append(card)

    Card.objects.bulk_create(to_create)
    report.created = len(to_create)
    report.errors = sorted(list(getattr(source, "errors", [])) + report.errors, key=lambda error: error.line)
    return report


def export_csv(deck: Deck) -> str:
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(EXPORT_COLUMNS)
    for card in deck.cards.all():
        writer.writerow(["" if getattr(card, name) is None else getattr(card, name) for name in EXPORT_COLUMNS])
    return buffer.getvalue()
