"""Scheduling algorithms for spaced repetition (Strategy pattern).

The rest of the application talks only to the ``SchedulingStrategy`` interface,
so the algorithm can be swapped (settings.SRS_ALGORITHM) without touching
services, views or the API. This module is pure Python - no database access -
which keeps it fast to unit-test.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, replace
from enum import IntEnum


class Rating(IntEnum):
    AGAIN = 0
    HARD = 1
    GOOD = 2
    EASY = 3


@dataclass(frozen=True)
class SchedulingState:
    ease_factor: float = 2.5
    interval_days: float = 0.0
    repetitions: int = 0
    lapses: int = 0


# Interval used for a failed card: it comes back in the same session.
RELEARN_INTERVAL_DAYS = 10 / (24 * 60)  # 10 minutes


class SchedulingStrategy(ABC):
    """Common interface of all scheduling algorithms."""

    name: str = ""

    @abstractmethod
    def schedule(self, state: SchedulingState, rating: Rating) -> SchedulingState:
        """Return the new state after the user answered with ``rating``."""


class SM2Strategy(SchedulingStrategy):
    """SuperMemo SM-2 variant with four answer buttons.

    * AGAIN: progress resets, card returns in 10 minutes, ease -0.20.
    * First success: 1 day (EASY: 3 days); second: 6 days (HARD: 4, EASY: 8).
    * Later: HARD = interval x 1.2 (ease -0.15), GOOD = interval x ease,
      EASY = interval x ease x 1.3 (ease +0.15).
    * Ease never drops below 1.3.
    """

    name = "sm2"
    MIN_EASE = 1.3
    EASE_DELTA = {Rating.AGAIN: -0.20, Rating.HARD: -0.15, Rating.GOOD: 0.0, Rating.EASY: 0.15}
    FIRST_INTERVALS = {Rating.HARD: 1.0, Rating.GOOD: 1.0, Rating.EASY: 3.0}
    SECOND_INTERVALS = {Rating.HARD: 4.0, Rating.GOOD: 6.0, Rating.EASY: 8.0}
    HARD_MULTIPLIER = 1.2
    EASY_BONUS = 1.3

    def schedule(self, state: SchedulingState, rating: Rating) -> SchedulingState:
        rating = Rating(rating)
        ease = max(self.MIN_EASE, round(state.ease_factor + self.EASE_DELTA[rating], 2))

        if rating == Rating.AGAIN:
            return replace(
                state, ease_factor=ease, interval_days=RELEARN_INTERVAL_DAYS,
                repetitions=0, lapses=state.lapses + 1,
            )

        if state.repetitions == 0:
            interval = self.FIRST_INTERVALS[rating]
        elif state.repetitions == 1:
            interval = self.SECOND_INTERVALS[rating]
        elif rating == Rating.HARD:
            interval = state.interval_days * self.HARD_MULTIPLIER
        elif rating == Rating.GOOD:
            interval = state.interval_days * ease
        else:
            interval = state.interval_days * ease * self.EASY_BONUS

        # A successful answer must never shorten the interval below one day.
        interval = max(1.0, round(interval, 2))
        return replace(state, ease_factor=ease, interval_days=interval, repetitions=state.repetitions + 1)


class LeitnerStrategy(SchedulingStrategy):
    """Classic Leitner boxes: each correct answer moves the card one box up."""

    name = "leitner"
    BOX_INTERVALS = [1.0, 2.0, 4.0, 8.0, 16.0, 32.0]

    def schedule(self, state: SchedulingState, rating: Rating) -> SchedulingState:
        rating = Rating(rating)
        if rating == Rating.AGAIN:
            return replace(state, interval_days=RELEARN_INTERVAL_DAYS, repetitions=0, lapses=state.lapses + 1)
        advance = {Rating.HARD: 0, Rating.GOOD: 1, Rating.EASY: 2}[rating]
        repetitions = min(max(1, state.repetitions + advance), len(self.BOX_INTERVALS))
        return replace(state, interval_days=self.BOX_INTERVALS[repetitions - 1], repetitions=repetitions)


_STRATEGIES = {cls.name: cls for cls in (SM2Strategy, LeitnerStrategy)}


def get_strategy(name: str = "sm2") -> SchedulingStrategy:
    try:
        return _STRATEGIES[name]()
    except KeyError as exc:
        raise ValueError(f"Unknown SRS algorithm: {name!r}") from exc
