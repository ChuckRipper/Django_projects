"""Statistics built from the review history (ReviewLog) - read-only aggregations."""

from dataclasses import dataclass
from datetime import date, timedelta

from django.db.models import Avg, Count, Q
from django.db.models.functions import TruncDate
from django.utils import timezone

from decks.models import Card, Deck
from study.models import ReviewLog, ReviewState
from study.srs import Rating


def _today(now=None):
    return timezone.localtime(now or timezone.now()).date()


def daily_reviews(user, days=30, now=None):
    """Answers per day for the last ``days`` days (oldest first), split into correct / again."""
    today = _today(now)
    start = today - timedelta(days=days - 1)
    rows = (
        ReviewLog.objects.filter(user=user, reviewed_at__date__gte=start)
        .annotate(day=TruncDate("reviewed_at", tzinfo=timezone.get_current_timezone()))
        .values("day")
        .annotate(total=Count("id"), again=Count("id", filter=Q(rating=Rating.AGAIN)))
    )
    by_day = {row["day"]: row for row in rows}
    result = []
    for offset in range(days):
        day = start + timedelta(days=offset)
        row = by_day.get(day, {"total": 0, "again": 0})
        result.append({"date": day, "correct": row["total"] - row["again"], "again": row["again"]})
    return result


@dataclass
class HeatmapCell:
    date: date
    count: int
    level: int  # 0..4


def heatmap(user, weeks=20, now=None):
    """Calendar grid (columns = weeks Monday-Sunday) of daily review counts with 5 intensity levels."""
    today = _today(now)
    start = today - timedelta(days=today.weekday() + 7 * (weeks - 1))
    counts = {
        row["day"]: row["n"]
        for row in ReviewLog.objects.filter(user=user, reviewed_at__date__gte=start)
        .annotate(day=TruncDate("reviewed_at", tzinfo=timezone.get_current_timezone()))
        .values("day")
        .annotate(n=Count("id"))
    }
    peak = max(counts.values(), default=0)

    def level(count):
        if not count:
            return 0
        return min(4, 1 + int(3 * count / peak)) if peak else 0

    columns = []
    for week in range(weeks):
        column = []
        for weekday in range(7):
            day = start + timedelta(days=7 * week + weekday)
            if day > today:
                column.append(None)
            else:
                count = counts.get(day, 0)
                column.append(HeatmapCell(day, count, level(count)))
        columns.append(column)
    return columns


def rating_breakdown(user):
    counts = dict(ReviewLog.objects.filter(user=user).values_list("rating").annotate(n=Count("id")))
    total = sum(counts.values())
    return [
        {
            "label": label, "value": value, "count": counts.get(value, 0),
            "percent": round(100 * counts.get(value, 0) / total) if total else 0,
        }
        for value, label in ReviewLog.Rating.choices
    ]


def card_stages(user):
    states = ReviewState.objects.filter(user=user)
    mature = states.filter(interval_days__gte=ReviewState.MATURE_INTERVAL_DAYS).count()
    started = states.count()
    total = Card.objects.filter(deck__in=Deck.objects.visible_to(user)).count()
    return {"new": total - started, "learning": started - mature, "mature": mature, "total": total}


def deck_accuracy(user):
    """Per-deck review count, accuracy and average answer time (only decks with reviews)."""
    rows = (
        ReviewLog.objects.filter(user=user)
        .values("card__deck__id", "card__deck__name")
        .annotate(
            total=Count("id"),
            again=Count("id", filter=Q(rating=Rating.AGAIN)),
            avg_ms=Avg("response_ms"),
        )
        .order_by("-total")
    )
    return [
        {
            "deck_id": row["card__deck__id"],
            "deck": row["card__deck__name"],
            "total": row["total"],
            "accuracy": round(100 * (row["total"] - row["again"]) / row["total"]),
            "avg_seconds": round(row["avg_ms"] / 1000, 1) if row["avg_ms"] else None,
        }
        for row in rows
    ]


def upcoming_reviews(user, days=7, now=None):
    """How many reviews fall due on each of the next ``days`` days (today includes overdue)."""
    today = _today(now)
    end = today + timedelta(days=days)
    rows = dict(
        ReviewState.objects.filter(user=user, due_at__date__lt=end)
        .annotate(day=TruncDate("due_at", tzinfo=timezone.get_current_timezone()))
        .values_list("day")
        .annotate(n=Count("id"))
    )
    overdue = sum(n for day, n in rows.items() if day < today)
    upcoming = []
    for offset in range(days):
        day = today + timedelta(days=offset)
        upcoming.append({"date": day, "count": rows.get(day, 0) + (overdue if offset == 0 else 0)})
    return upcoming
