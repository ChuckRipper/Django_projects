from django.contrib import admin

from .models import ReviewLog, ReviewState


@admin.register(ReviewState)
class ReviewStateAdmin(admin.ModelAdmin):
    list_display = ("user", "card", "repetitions", "interval_days", "ease_factor", "lapses", "due_at")
    list_filter = ("user",)
    search_fields = ("card__front", "card__back", "user__username")
    list_select_related = ("user", "card")


@admin.register(ReviewLog)
class ReviewLogAdmin(admin.ModelAdmin):
    list_display = ("reviewed_at", "user", "card", "rating", "interval_before", "interval_after")
    list_filter = ("rating", "user")
    date_hierarchy = "reviewed_at"
    list_select_related = ("user", "card")
