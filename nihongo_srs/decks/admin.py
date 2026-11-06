from django.contrib import admin

from .models import Card, Deck


class CardInline(admin.TabularInline):
    model = Card
    extra = 0
    fields = ("order", "front", "back", "reading")


@admin.register(Deck)
class DeckAdmin(admin.ModelAdmin):
    list_display = ("name", "kind", "jlpt_level", "owner", "order", "created_at")
    list_filter = ("kind", "jlpt_level", ("owner", admin.EmptyFieldListFilter))
    search_fields = ("name", "description")
    list_select_related = ("owner",)
    inlines = [CardInline]


@admin.register(Card)
class CardAdmin(admin.ModelAdmin):
    list_display = ("front", "back", "reading", "deck", "order")
    list_filter = ("deck__kind", "deck__jlpt_level", "deck")
    search_fields = ("front", "back", "reading")
    list_select_related = ("deck",)
    list_per_page = 100
