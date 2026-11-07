"""User profile with study preferences."""

from django.conf import settings
from django.db import models


class Profile(models.Model):
    """Per-user study settings. Created automatically for every user (see signals.py)."""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile"
    )
    new_cards_per_day = models.PositiveSmallIntegerField(
        "Nowe karty dziennie", default=10,
        help_text="Ile nowych kart może pojawić się w nauce jednego dnia.",
    )
    daily_goal = models.PositiveSmallIntegerField(
        "Cel dzienny (powtórki)", default=30,
    )

    class AnswerMode(models.TextChoices):
        REVEAL = "reveal", "Odsłanianie odpowiedzi"
        TYPE = "type", "Wpisywanie odpowiedzi"

    answer_mode = models.CharField(
        "Tryb odpowiedzi", max_length=10, choices=AnswerMode.choices, default=AnswerMode.REVEAL,
        help_text="W trybie wpisywania przy kartach kana podajesz zapis w romaji, a przy słówkach "
                  "odczyt (romaji zamienia się w kanę w trakcie pisania). Karty kanji zawsze się odsłania.",
    )

    class Meta:
        verbose_name = "Profil"
        verbose_name_plural = "Profile"

    def __str__(self):
        return f"Profil: {self.user.username}"
