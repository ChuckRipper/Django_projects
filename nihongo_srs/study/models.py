"""Per-user learning progress and review history."""

from django.conf import settings
from django.db import models
from django.utils import timezone

from decks.models import Card


class ReviewState(models.Model):
    """Scheduling state of one card for one user."""

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="review_states")
    card = models.ForeignKey(Card, on_delete=models.CASCADE, related_name="review_states")
    ease_factor = models.FloatField(default=2.5)
    interval_days = models.FloatField(default=0)
    repetitions = models.PositiveIntegerField(default=0)
    lapses = models.PositiveIntegerField(default=0)
    due_at = models.DateTimeField(db_index=True)
    introduced_at = models.DateTimeField(default=timezone.now)
    last_reviewed_at = models.DateTimeField(null=True, blank=True)

    MATURE_INTERVAL_DAYS = 21

    class Meta:
        verbose_name = "Stan nauki karty"
        verbose_name_plural = "Stany nauki kart"
        constraints = [
            models.UniqueConstraint(fields=["user", "card"], name="unique_review_state_per_user_card"),
        ]
        indexes = [models.Index(fields=["user", "due_at"])]

    def __str__(self):
        return f"{self.user} · {self.card.front} (due {self.due_at:%Y-%m-%d %H:%M})"

    @property
    def is_mature(self):
        return self.interval_days >= self.MATURE_INTERVAL_DAYS


class ReviewLog(models.Model):
    """One answer given during study - the source for statistics."""

    class Rating(models.IntegerChoices):
        AGAIN = 0, "Znów"
        HARD = 1, "Trudne"
        GOOD = 2, "Dobre"
        EASY = 3, "Łatwe"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="review_logs")
    card = models.ForeignKey(Card, on_delete=models.CASCADE, related_name="review_logs")
    rating = models.PositiveSmallIntegerField(choices=Rating.choices)
    reviewed_at = models.DateTimeField(db_index=True)
    response_ms = models.PositiveIntegerField(null=True, blank=True)
    interval_before = models.FloatField()
    interval_after = models.FloatField()
    ease_after = models.FloatField()

    class Meta:
        verbose_name = "Wpis powtórki"
        verbose_name_plural = "Historia powtórek"
        ordering = ["-reviewed_at"]
        indexes = [models.Index(fields=["user", "reviewed_at"])]

    def __str__(self):
        return f"{self.user} · {self.card.front} · {self.get_rating_display()}"
