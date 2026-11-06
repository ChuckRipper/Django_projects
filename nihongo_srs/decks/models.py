"""Decks and cards - the learning material."""

from django.conf import settings
from django.db import models
from django.db.models import Q


class DeckQuerySet(models.QuerySet):
    def visible_to(self, user):
        """System decks plus the user's own decks."""
        if user is None or not user.is_authenticated:
            return self.filter(owner__isnull=True)
        return self.filter(Q(owner__isnull=True) | Q(owner=user))


class Deck(models.Model):
    class Kind(models.TextChoices):
        KANA = "kana", "Kana"
        VOCABULARY = "vocabulary", "Słownictwo"
        KANJI = "kanji", "Kanji"

    class JlptLevel(models.TextChoices):
        N5 = "N5", "N5"
        N4 = "N4", "N4"

    name = models.CharField("Nazwa", max_length=120)
    description = models.TextField("Opis", blank=True)
    kind = models.CharField("Typ", max_length=20, choices=Kind.choices, default=Kind.VOCABULARY)
    jlpt_level = models.CharField(
        "Poziom JLPT", max_length=2, choices=JlptLevel.choices, blank=True
    )
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True,
        related_name="decks", verbose_name="Właściciel",
        help_text="Puste = talia systemowa, dostępna dla wszystkich (tylko do odczytu).",
    )
    order = models.PositiveIntegerField("Kolejność", default=0)
    created_at = models.DateTimeField("Utworzono", auto_now_add=True)

    objects = DeckQuerySet.as_manager()

    class Meta:
        verbose_name = "Talia"
        verbose_name_plural = "Talie"
        ordering = ["owner_id", "order", "name"]
        constraints = [
            models.UniqueConstraint(fields=["owner", "name"], name="unique_deck_name_per_owner"),
        ]

    def __str__(self):
        return self.name

    @property
    def is_system(self):
        return self.owner_id is None

    def can_edit(self, user):
        return user.is_authenticated and self.owner_id == user.id


class Card(models.Model):
    deck = models.ForeignKey(Deck, on_delete=models.CASCADE, related_name="cards", verbose_name="Talia")
    front = models.CharField("Przód", max_length=100)
    back = models.CharField("Tył (znaczenie)", max_length=255)
    meaning_en = models.CharField(
        "Znaczenie (ang.)", max_length=255, blank=True,
        help_text="Oryginalne znaczenie ze słownika źródłowego.",
    )
    reading = models.CharField("Odczyt", max_length=100, blank=True)
    example = models.CharField("Przykład", max_length=255, blank=True)
    onyomi = models.CharField("On'yomi", max_length=100, blank=True)
    kunyomi = models.CharField("Kun'yomi", max_length=100, blank=True)
    stroke_count = models.PositiveSmallIntegerField("Liczba kresek", null=True, blank=True)
    order = models.PositiveIntegerField("Kolejność", default=0)

    class Meta:
        verbose_name = "Karta"
        verbose_name_plural = "Karty"
        ordering = ["deck_id", "order", "id"]
        constraints = [
            models.UniqueConstraint(fields=["deck", "front"], name="unique_card_front_per_deck"),
        ]

    def __str__(self):
        return f"{self.front} – {self.back}"
