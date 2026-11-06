"""Study use cases (Service Layer).

Both the HTML views and the REST API call these functions, so the business
rules - queue building, daily limits, saving an answer - live in one place.
"""

from dataclasses import dataclass
from datetime import timedelta

from django.conf import settings
from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from accounts.models import Profile
from decks.models import Card, Deck

from .models import ReviewLog, ReviewState
from .srs import Rating, SchedulingState, get_strategy


def _start_of_today(now):
    local = timezone.localtime(now)
    return local.replace(hour=0, minute=0, second=0, microsecond=0)


def _cards_for(user, deck=None):
    decks = Deck.objects.visible_to(user)
    if deck is not None:
        decks = decks.filter(pk=deck.pk)
    return Card.objects.filter(deck__in=decks)


def new_cards_left_today(user, now=None):
    now = now or timezone.now()
    profile, _ = Profile.objects.get_or_create(user=user)
    introduced = ReviewState.objects.filter(user=user, introduced_at__gte=_start_of_today(now)).count()
    return max(profile.new_cards_per_day - introduced, 0)


def due_cards(user, deck=None, now=None):
    """Cards already in learning whose review time has come, oldest first."""
    now = now or timezone.now()
    return (
        _cards_for(user, deck)
        .filter(review_states__user=user, review_states__due_at__lte=now)
        .select_related("deck")
        .order_by("review_states__due_at")
    )


def new_cards(user, deck=None):
    """Cards the user has never studied, in deck order."""
    return (
        _cards_for(user, deck)
        .exclude(review_states__user=user)
        .select_related("deck")
        .order_by("deck__owner_id", "deck__order", "deck_id", "order", "id")
    )


def build_queue(user, deck=None, now=None, limit=None):
    """Due reviews first, then new cards up to the daily limit."""
    now = now or timezone.now()
    queue = list(due_cards(user, deck, now))
    new_limit = new_cards_left_today(user, now)
    if new_limit:
        queue += list(new_cards(user, deck)[:new_limit])
    return queue[:limit] if limit else queue


def next_card(user, deck=None, now=None):
    queue = build_queue(user, deck, now, limit=1)
    return queue[0] if queue else None


@transaction.atomic
def submit_review(user, card, rating, response_ms=None, now=None):
    """Apply the configured scheduling strategy and record the answer."""
    now = now or timezone.now()
    rating = Rating(int(rating))
    state, _ = ReviewState.objects.get_or_create(
        user=user, card=card, defaults={"due_at": now, "introduced_at": now}
    )
    interval_before = state.interval_days

    strategy = get_strategy(settings.SRS_ALGORITHM)
    result = strategy.schedule(
        SchedulingState(state.ease_factor, state.interval_days, state.repetitions, state.lapses),
        rating,
    )

    state.ease_factor = result.ease_factor
    state.interval_days = result.interval_days
    state.repetitions = result.repetitions
    state.lapses = result.lapses
    state.due_at = now + timedelta(days=result.interval_days)
    state.last_reviewed_at = now
    state.save()

    ReviewLog.objects.create(
        user=user, card=card, rating=int(rating), reviewed_at=now, response_ms=response_ms,
        interval_before=interval_before, interval_after=result.interval_days, ease_after=result.ease_factor,
    )
    return state


@dataclass
class DeckProgress:
    total: int
    new: int
    learning: int
    mature: int
    due: int

    @property
    def percent_started(self):
        return round(100 * (self.total - self.new) / self.total) if self.total else 0


def deck_progress(user, deck, now=None):
    now = now or timezone.now()
    total = deck.cards.count()
    states = ReviewState.objects.filter(user=user, card__deck=deck)
    mature = states.filter(interval_days__gte=ReviewState.MATURE_INTERVAL_DAYS).count()
    started = states.count()
    return DeckProgress(
        total=total, new=total - started, learning=started - mature, mature=mature,
        due=states.filter(due_at__lte=now).count(),
    )


@dataclass
class StudySummary:
    due_now: int
    new_available: int
    reviews_today: int
    daily_goal: int
    streak_days: int
    accuracy_percent: int | None

    @property
    def goal_percent(self):
        return min(100, round(100 * self.reviews_today / self.daily_goal)) if self.daily_goal else 0


def study_streak(user, now=None):
    """Number of consecutive days with at least one review, ending today or yesterday."""
    now = now or timezone.now()
    days = {
        timezone.localtime(ts).date()
        for ts in ReviewLog.objects.filter(user=user).values_list("reviewed_at", flat=True)
    }
    day = timezone.localtime(now).date()
    if day not in days:
        day -= timedelta(days=1)
    streak = 0
    while day in days:
        streak += 1
        day -= timedelta(days=1)
    return streak


def study_summary(user, now=None):
    now = now or timezone.now()
    profile, _ = Profile.objects.get_or_create(user=user)
    logs_today = ReviewLog.objects.filter(user=user, reviewed_at__gte=_start_of_today(now))
    total_logs = ReviewLog.objects.filter(user=user)
    total = total_logs.count()
    correct = total_logs.filter(~Q(rating=Rating.AGAIN)).count()
    return StudySummary(
        due_now=due_cards(user, now=now).count(),
        new_available=min(new_cards_left_today(user, now), new_cards(user).count()),
        reviews_today=logs_today.count(),
        daily_goal=profile.daily_goal,
        streak_days=study_streak(user, now),
        accuracy_percent=round(100 * correct / total) if total else None,
    )
