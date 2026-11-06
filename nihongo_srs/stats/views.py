from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView

from study.services import study_summary

from . import services

WEEKDAYS = ["pon", "wt", "śr", "czw", "pt", "sob", "ndz"]


class StatsView(LoginRequiredMixin, TemplateView):
    template_name = "stats/stats.html"

    def get_context_data(self, **kwargs):
        user = self.request.user
        daily = services.daily_reviews(user, days=30)
        upcoming = services.upcoming_reviews(user)
        peak = max((u["count"] for u in upcoming), default=0)
        for item in upcoming:
            item["percent"] = round(100 * item["count"] / peak) if peak else 0
        return {
            **super().get_context_data(**kwargs),
            "summary": study_summary(user),
            "daily": daily,
            "daily_chart": {
                "labels": [d["date"].strftime("%d.%m") for d in daily],
                "correct": [d["correct"] for d in daily],
                "again": [d["again"] for d in daily],
            },
            "daily_total": sum(d["correct"] + d["again"] for d in daily),
            "heatmap": services.heatmap(user, weeks=20),
            "weekdays": WEEKDAYS,
            "ratings": services.rating_breakdown(user),
            "stages": services.card_stages(user),
            "decks": services.deck_accuracy(user),
            "upcoming": upcoming,
        }
