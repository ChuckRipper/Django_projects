from django.contrib import admin

from .models import Profile


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "new_cards_per_day", "daily_goal")
    search_fields = ("user__username", "user__email")
