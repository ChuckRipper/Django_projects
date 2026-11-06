from django.http import Http404

from .models import Deck


class OwnedDeckMixin:
    """Restricts object access to decks owned by the current user (system decks are read-only)."""

    def get_queryset(self):
        return Deck.objects.filter(owner=self.request.user)


class OwnedCardMixin:
    def get_queryset(self):
        return super().get_queryset().filter(deck__owner=self.request.user).select_related("deck")


def get_owned_deck_or_404(user, pk):
    try:
        return Deck.objects.get(pk=pk, owner=user)
    except Deck.DoesNotExist as exc:
        raise Http404("Nie znaleziono talii.") from exc
