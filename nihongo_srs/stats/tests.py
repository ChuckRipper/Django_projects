from datetime import timedelta

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from decks.models import Card, Deck
from study.services import submit_review
from study.srs import Rating

from . import services


class StatsTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("ania", password="Haslo-12345")
        deck = Deck.objects.create(name="Kana", kind=Deck.Kind.KANA)
        self.cards = [Card.objects.create(deck=deck, front=f"k{i}", back="x", order=i) for i in range(4)]
        self.now = timezone.now()
        submit_review(self.user, self.cards[0], Rating.GOOD, response_ms=1000, now=self.now)
        submit_review(self.user, self.cards[1], Rating.AGAIN, response_ms=3000, now=self.now)
        submit_review(self.user, self.cards[2], Rating.EASY, now=self.now - timedelta(days=3))

    def test_daily_reviews(self):
        daily = services.daily_reviews(self.user, days=7, now=self.now)
        self.assertEqual(len(daily), 7)
        self.assertEqual((daily[-1]["correct"], daily[-1]["again"]), (1, 1))
        self.assertEqual(daily[-4]["correct"], 1)

    def test_heatmap_levels(self):
        cells = [cell for column in services.heatmap(self.user, weeks=2, now=self.now) for cell in column if cell]
        today = [c for c in cells if c.date == timezone.localtime(self.now).date()][0]
        self.assertEqual((today.count, today.level), (2, 4))
        self.assertTrue(any(c.level == 0 for c in cells))

    def test_breakdown_stages_and_decks(self):
        ratings = {r["label"]: r["count"] for r in services.rating_breakdown(self.user)}
        self.assertEqual(ratings, {"Znów": 1, "Trudne": 0, "Dobre": 1, "Łatwe": 1})
        self.assertEqual(services.card_stages(self.user), {"new": 1, "learning": 3, "mature": 0, "total": 4})
        deck = services.deck_accuracy(self.user)[0]
        self.assertEqual((deck["total"], deck["accuracy"], deck["avg_seconds"]), (3, 67, 2.0))

    def test_upcoming_reviews_include_overdue_today(self):
        upcoming = services.upcoming_reviews(self.user, days=7, now=self.now + timedelta(days=2))
        self.assertGreaterEqual(upcoming[0]["count"], 2)

    def test_stats_page(self):
        self.client.login(username="ania", password="Haslo-12345")
        response = self.client.get(reverse("stats"))
        self.assertContains(response, "daily-data")
        self.assertContains(response, "hm hm-4")

    def test_stats_page_for_new_user(self):
        User.objects.create_user("nowy", password="Haslo-12345")
        self.client.login(username="nowy", password="Haslo-12345")
        self.assertContains(self.client.get(reverse("stats")), "Brak powtórek")
