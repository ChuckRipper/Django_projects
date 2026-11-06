from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.views.generic import CreateView, DeleteView, DetailView, FormView, ListView, UpdateView

from study.services import deck_progress

from . import services
from .forms import CardForm, CardImportForm, DeckForm
from .mixins import OwnedCardMixin, OwnedDeckMixin, get_owned_deck_or_404
from .models import Card, Deck
from .sources import CsvCardSource


class DeckListView(LoginRequiredMixin, ListView):
    template_name = "decks/deck_list.html"
    context_object_name = "decks"

    def get_queryset(self):
        user = self.request.user
        now = timezone.now()
        decks = Deck.objects.visible_to(user)
        q = self.request.GET.get("q", "").strip()
        kind = self.request.GET.get("kind", "")
        level = self.request.GET.get("level", "")
        if q:
            decks = decks.filter(Q(name__icontains=q) | Q(description__icontains=q))
        if kind in Deck.Kind.values:
            decks = decks.filter(kind=kind)
        if level in Deck.JlptLevel.values:
            decks = decks.filter(jlpt_level=level)
        # One query with aggregates instead of N+1 queries per deck.
        return decks.annotate(
            card_count=Count("cards", distinct=True),
            started_count=Count(
                "cards__review_states", filter=Q(cards__review_states__user=user), distinct=True
            ),
            due_count=Count(
                "cards__review_states",
                filter=Q(cards__review_states__user=user, cards__review_states__due_at__lte=now),
                distinct=True,
            ),
        ).order_by("owner_id", "order", "name")  # Meta.ordering is ignored in GROUP BY queries

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            q=self.request.GET.get("q", ""),
            kind=self.request.GET.get("kind", ""),
            level=self.request.GET.get("level", ""),
            kinds=Deck.Kind.choices,
            levels=Deck.JlptLevel.choices,
        )
        return context


class DeckDetailView(LoginRequiredMixin, DetailView):
    template_name = "decks/deck_detail.html"
    context_object_name = "deck"

    def get_queryset(self):
        return Deck.objects.visible_to(self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["cards"] = self.object.cards.all()
        context["progress"] = deck_progress(self.request.user, self.object)
        context["can_edit"] = self.object.can_edit(self.request.user)
        return context


class DeckCreateView(LoginRequiredMixin, CreateView):
    form_class = DeckForm
    template_name = "decks/deck_form.html"

    def get_form_kwargs(self):
        return {**super().get_form_kwargs(), "owner": self.request.user}

    def form_valid(self, form):
        form.instance.owner = self.request.user
        messages.success(self.request, f"Utworzono talię „{form.instance.name}”.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("deck_detail", args=[self.object.pk])


class DeckUpdateView(LoginRequiredMixin, OwnedDeckMixin, UpdateView):
    form_class = DeckForm
    template_name = "decks/deck_form.html"

    def get_form_kwargs(self):
        return {**super().get_form_kwargs(), "owner": self.request.user}

    def form_valid(self, form):
        messages.success(self.request, "Zapisano zmiany w talii.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("deck_detail", args=[self.object.pk])


class DeckDeleteView(LoginRequiredMixin, OwnedDeckMixin, DeleteView):
    template_name = "decks/confirm_delete.html"
    success_url = reverse_lazy("deck_list")

    def form_valid(self, form):
        messages.success(self.request, f"Usunięto talię „{self.object.name}”.")
        return super().form_valid(form)


class CardCreateView(LoginRequiredMixin, CreateView):
    form_class = CardForm
    template_name = "decks/card_form.html"

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            self.deck = get_owned_deck_or_404(request.user, kwargs["deck_pk"])
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        return {**super().get_form_kwargs(), "deck": self.deck}

    def get_context_data(self, **kwargs):
        return {**super().get_context_data(**kwargs), "deck": self.deck}

    def form_valid(self, form):
        form.instance.deck = self.deck
        form.instance.order = self.deck.cards.count() + 1
        messages.success(self.request, f"Dodano kartę „{form.instance.front}”.")
        return super().form_valid(form)

    def get_success_url(self):
        if "save_and_add" in self.request.POST:
            return reverse("card_create", args=[self.deck.pk])
        return reverse("deck_detail", args=[self.deck.pk])


class CardUpdateView(LoginRequiredMixin, OwnedCardMixin, UpdateView):
    model = Card
    form_class = CardForm
    template_name = "decks/card_form.html"

    def get_context_data(self, **kwargs):
        return {**super().get_context_data(**kwargs), "deck": self.object.deck}

    def form_valid(self, form):
        messages.success(self.request, "Zapisano kartę.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("deck_detail", args=[self.object.deck_id])


class CardDeleteView(LoginRequiredMixin, OwnedCardMixin, DeleteView):
    model = Card
    template_name = "decks/confirm_delete.html"

    def get_success_url(self):
        return reverse("deck_detail", args=[self.object.deck_id])

    def form_valid(self, form):
        messages.success(self.request, f"Usunięto kartę „{self.object.front}”.")
        return super().form_valid(form)


class CardImportView(LoginRequiredMixin, FormView):
    form_class = CardImportForm
    template_name = "decks/import.html"

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            self.deck = get_owned_deck_or_404(request.user, kwargs["pk"])
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        return {**super().get_context_data(**kwargs), "deck": self.deck}

    def form_valid(self, form):
        source = CsvCardSource.from_upload(form.cleaned_data["file"])
        report = services.import_cards(self.deck, source, form.cleaned_data["update_existing"])
        if report.created or report.updated:
            messages.success(
                self.request, f"Import zakończony: nowe karty {report.created}, zaktualizowane {report.updated}."
            )
        elif not report.errors:
            messages.info(self.request, f"Brak zmian: wszystkie karty już są w talii (pominięte: {report.skipped}).")
        if report.errors:
            return self.render_to_response(self.get_context_data(form=form, report=report))
        return redirect("deck_detail", pk=self.deck.pk)


@login_required
def deck_export(request, pk):
    """Download a deck (own or system) as CSV - the same format the import accepts."""
    deck = get_object_or_404(Deck.objects.visible_to(request.user), pk=pk)
    response = HttpResponse(services.export_csv(deck), content_type="text/csv; charset=utf-8")
    filename = f"talia-{deck.pk}.csv"
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response
