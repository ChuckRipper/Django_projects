"""Tests of the scheduling algorithms and the study service layer."""

from datetime import timedelta

from django.contrib.auth.models import User
from django.test import SimpleTestCase, TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from decks.models import Card, Deck

from . import services
from .models import ReviewLog, ReviewState
from .srs import RELEARN_INTERVAL_DAYS, LeitnerStrategy, Rating, SchedulingState, SM2Strategy, get_strategy


class SM2StrategyTests(SimpleTestCase):
    def setUp(self):
        self.sm2 = SM2Strategy()

    def test_first_and_second_success_intervals(self):
        first = self.sm2.schedule(SchedulingState(), Rating.GOOD)
        self.assertEqual((first.interval_days, first.repetitions), (1.0, 1))
        second = self.sm2.schedule(first, Rating.GOOD)
        self.assertEqual((second.interval_days, second.repetitions), (6.0, 2))

    def test_third_good_multiplies_by_ease(self):
        state = SchedulingState(ease_factor=2.5, interval_days=6.0, repetitions=2)
        self.assertEqual(self.sm2.schedule(state, Rating.GOOD).interval_days, 15.0)

    def test_easy_adds_bonus_and_raises_ease(self):
        state = SchedulingState(ease_factor=2.5, interval_days=6.0, repetitions=2)
        result = self.sm2.schedule(state, Rating.EASY)
        self.assertAlmostEqual(result.ease_factor, 2.65)
        self.assertAlmostEqual(result.interval_days, round(6 * 2.65 * 1.3, 2))

    def test_hard_grows_slowly_and_lowers_ease(self):
        state = SchedulingState(ease_factor=2.5, interval_days=10.0, repetitions=3)
        result = self.sm2.schedule(state, Rating.HARD)
        self.assertEqual(result.interval_days, 12.0)
        self.assertAlmostEqual(result.ease_factor, 2.35)

    def test_again_resets_progress(self):
        state = SchedulingState(ease_factor=2.5, interval_days=30.0, repetitions=5, lapses=1)
        result = self.sm2.schedule(state, Rating.AGAIN)
        self.assertEqual(result.repetitions, 0)
        self.assertEqual(result.lapses, 2)
        self.assertEqual(result.interval_days, RELEARN_INTERVAL_DAYS)
        self.assertAlmostEqual(result.ease_factor, 2.3)

    def test_ease_never_below_minimum(self):
        state = SchedulingState(ease_factor=1.35)
        for _ in range(5):
            state = self.sm2.schedule(state, Rating.AGAIN)
        self.assertEqual(state.ease_factor, SM2Strategy.MIN_EASE)

    def test_success_interval_is_at_least_one_day(self):
        state = SchedulingState(ease_factor=1.3, interval_days=0.5, repetitions=3)
        self.assertGreaterEqual(self.sm2.schedule(state, Rating.HARD).interval_days, 1.0)


class LeitnerStrategyTests(SimpleTestCase):
    def test_moves_up_one_box_and_resets_on_again(self):
        leitner = LeitnerStrategy()
        state = leitner.schedule(SchedulingState(), Rating.GOOD)
        state = leitner.schedule(state, Rating.GOOD)
        self.assertEqual((state.repetitions, state.interval_days), (2, 2.0))
        state = leitner.schedule(state, Rating.AGAIN)
        self.assertEqual(state.repetitions, 0)

    def test_get_strategy(self):
        self.assertIsInstance(get_strategy("sm2"), SM2Strategy)
        self.assertIsInstance(get_strategy("leitner"), LeitnerStrategy)
        with self.assertRaises(ValueError):
            get_strategy("unknown")


class StudyServiceTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("ania", password="Haslo-12345")
        self.user.profile.new_cards_per_day = 3
        self.user.profile.save()
        self.deck = Deck.objects.create(name="Hiragana test", kind=Deck.Kind.KANA)
        self.cards = [Card.objects.create(deck=self.deck, front=f"k{i}", back=f"r{i}", order=i) for i in range(5)]

    def test_profile_created_by_signal(self):
        self.assertTrue(hasattr(User.objects.create_user("nowy"), "profile"))

    def test_queue_respects_daily_new_card_limit(self):
        self.assertEqual(len(services.build_queue(self.user)), 3)

    def test_introduced_cards_reduce_remaining_limit(self):
        services.submit_review(self.user, self.cards[0], Rating.GOOD)
        self.assertEqual(services.new_cards_left_today(self.user), 2)
        # card 0 is due tomorrow, so only 2 new cards are offered now
        self.assertEqual([c.front for c in services.build_queue(self.user)], ["k1", "k2"])

    def test_due_cards_come_before_new_cards(self):
        now = timezone.now()
        services.submit_review(self.user, self.cards[4], Rating.GOOD, now=now - timedelta(days=2))
        queue = services.build_queue(self.user, now=now)
        self.assertEqual(queue[0].front, "k4")

    def test_failed_card_comes_back_in_same_session(self):
        now = timezone.now()
        services.submit_review(self.user, self.cards[0], Rating.AGAIN, now=now)
        queue = services.build_queue(self.user, now=now + timedelta(minutes=11))
        self.assertEqual(queue[0].front, "k0")

    def test_submit_review_saves_state_and_log(self):
        state = services.submit_review(self.user, self.cards[0], Rating.GOOD, response_ms=1500)
        self.assertEqual(state.repetitions, 1)
        log = ReviewLog.objects.get()
        self.assertEqual((log.rating, log.response_ms, log.interval_after), (Rating.GOOD, 1500, 1.0))

    @override_settings(SRS_ALGORITHM="leitner")
    def test_algorithm_is_configurable(self):
        state = services.submit_review(self.user, self.cards[0], Rating.EASY)
        self.assertEqual(state.interval_days, LeitnerStrategy.BOX_INTERVALS[1])

    def test_other_users_private_decks_are_not_in_queue(self):
        other = User.objects.create_user("obcy")
        private = Deck.objects.create(name="Prywatna", owner=other)
        Card.objects.create(deck=private, front="x", back="y")
        fronts = {c.front for c in services.new_cards(self.user)}
        self.assertNotIn("x", fronts)

    def test_summary_and_streak(self):
        now = timezone.now()
        services.submit_review(self.user, self.cards[0], Rating.GOOD, now=now - timedelta(days=1))
        services.submit_review(self.user, self.cards[1], Rating.AGAIN, now=now)
        summary = services.study_summary(self.user, now=now)
        self.assertEqual(summary.streak_days, 2)
        self.assertEqual(summary.reviews_today, 1)
        self.assertEqual(summary.accuracy_percent, 50)

    def test_deck_progress(self):
        services.submit_review(self.user, self.cards[0], Rating.GOOD)
        ReviewState.objects.create(
            user=self.user, card=self.cards[1], interval_days=30, due_at=timezone.now() + timedelta(days=30)
        )
        progress = services.deck_progress(self.user, self.deck)
        self.assertEqual((progress.total, progress.new, progress.learning, progress.mature), (5, 3, 1, 1))


class StudyViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("ania", password="Haslo-12345")
        self.deck = Deck.objects.create(name="Kana", kind=Deck.Kind.KANA)
        self.card = Card.objects.create(deck=self.deck, front="あ", back="a")
        self.client.login(username="ania", password="Haslo-12345")

    def test_session_shows_card_and_saves_rating(self):
        response = self.client.get(reverse("study"))
        self.assertContains(response, "あ")
        response = self.client.post(reverse("study"), {"card_id": self.card.pk, "rating": 2, "response_ms": 900})
        self.assertRedirects(response, reverse("study"))
        self.assertEqual(ReviewState.objects.get().repetitions, 1)

    def test_done_page_when_queue_empty(self):
        services.submit_review(self.user, self.card, Rating.GOOD)
        self.assertContains(self.client.get(reverse("study")), "Na teraz to wszystko")

    def test_invalid_rating_rejected(self):
        response = self.client.post(reverse("study"), {"card_id": self.card.pk, "rating": 9})
        self.assertEqual(response.status_code, 400)

    def test_study_requires_login(self):
        self.client.logout()
        self.assertEqual(self.client.get(reverse("study")).status_code, 302)
