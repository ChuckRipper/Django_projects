from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import BadRequest
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.http import url_has_allowed_host_and_scheme
from django.views import View

from accounts.models import Profile
from decks.models import Card, Deck

from . import services
from .forms import ReviewForm
from .typing import typing_task


class StudyView(LoginRequiredMixin, View):
    """One card at a time: GET shows the next card, POST saves the answer (Post/Redirect/Get)."""

    template_name = "study/session.html"

    def get_deck(self):
        deck_pk = self.kwargs.get("deck_pk")
        if deck_pk is None:
            return None
        return get_object_or_404(Deck.objects.visible_to(self.request.user), pk=deck_pk)

    def get(self, request, deck_pk=None):
        deck = self.get_deck()
        queue = services.build_queue(request.user, deck)
        if not queue:
            return render(request, "study/done.html", {
                "deck": deck, "summary": services.study_summary(request.user),
            })
        card = queue[0]
        is_new = not card.review_states.filter(user=request.user).exists()
        type_mode = request.user.profile.answer_mode == Profile.AnswerMode.TYPE
        task = typing_task(card) if type_mode else None
        return render(request, self.template_name, {
            "type_mode": type_mode,
            "typing": task,
            "typing_answers": task.answers if task else [],
            "deck": deck,
            "card": card,
            "is_new": is_new,
            "remaining": len(queue),
            "ratings": services.Rating,
            "form": ReviewForm(initial={"card_id": card.pk}),
        })

    def post(self, request, deck_pk=None):
        deck = self.get_deck()
        form = ReviewForm(request.POST)
        if not form.is_valid():
            raise BadRequest("Nieprawidłowa ocena.")
        visible = Card.objects.filter(deck__in=Deck.objects.visible_to(request.user))
        try:
            card = visible.get(pk=form.cleaned_data["card_id"])
        except Card.DoesNotExist as exc:
            raise Http404("Nie znaleziono karty.") from exc
        services.submit_review(
            request.user, card, form.cleaned_data["rating"], form.cleaned_data.get("response_ms"),
        )
        if deck is not None:
            return redirect("study_deck", deck_pk=deck.pk)
        return redirect("study")


class AnswerModeToggleView(LoginRequiredMixin, View):
    """Switch between revealing and typing answers (button on the study page)."""

    def post(self, request):
        profile = request.user.profile
        profile.answer_mode = (
            Profile.AnswerMode.REVEAL if profile.answer_mode == Profile.AnswerMode.TYPE
            else Profile.AnswerMode.TYPE
        )
        profile.save(update_fields=["answer_mode"])
        next_url = request.POST.get("next", "")
        if not url_has_allowed_host_and_scheme(next_url, {request.get_host()}, request.is_secure()):
            next_url = "study"
        return redirect(next_url)
