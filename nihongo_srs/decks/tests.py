from io import StringIO

from django.contrib.auth.models import User
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from .models import Card, Deck


class LoadDataTests(TestCase):
    def test_loads_kana_and_is_idempotent(self):
        call_command("load_data", stdout=StringIO())
        call_command("load_data", stdout=StringIO())
        self.assertEqual(Deck.objects.filter(owner=None, kind=Deck.Kind.KANA).count(), 6)
        self.assertEqual(Card.objects.filter(deck__owner=None).count(), 2 * (46 + 25 + 33))
        self.assertTrue(Card.objects.filter(front="ア", back="a").exists())


class DeckPermissionTests(TestCase):
    def setUp(self):
        self.ania = User.objects.create_user("ania", password="Haslo-12345")
        self.bartek = User.objects.create_user("bartek", password="Haslo-12345")
        self.system = Deck.objects.create(name="Systemowa")
        self.own = Deck.objects.create(name="Moja", owner=self.ania)
        self.foreign = Deck.objects.create(name="Bartka", owner=self.bartek)
        self.client.login(username="ania", password="Haslo-12345")

    def test_list_shows_system_and_own_decks_only(self):
        response = self.client.get(reverse("deck_list"))
        names = {d.name for d in response.context["decks"]}
        self.assertEqual(names, {"Systemowa", "Moja"})

    def test_foreign_deck_is_404(self):
        self.assertEqual(self.client.get(reverse("deck_detail", args=[self.foreign.pk])).status_code, 404)

    def test_system_deck_cannot_be_edited(self):
        self.assertEqual(self.client.get(reverse("deck_update", args=[self.system.pk])).status_code, 404)
        self.assertEqual(self.client.get(reverse("card_create", args=[self.system.pk])).status_code, 404)

    def test_create_deck_and_card(self):
        data = {"name": "Słówka", "kind": "vocabulary", "jlpt_level": "N5"}
        response = self.client.post(reverse("deck_create"), data)
        deck = Deck.objects.get(name="Słówka")
        self.assertEqual(deck.owner, self.ania)
        self.assertRedirects(response, reverse("deck_detail", args=[deck.pk]))
        self.client.post(reverse("card_create", args=[deck.pk]), {"front": "猫", "back": "kot", "reading": "ねこ"})
        self.assertTrue(deck.cards.filter(front="猫").exists())

    def test_duplicate_deck_name_rejected(self):
        response = self.client.post(reverse("deck_create"), {"name": "moja", "kind": "vocabulary"})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["form"].errors["name"])

    def test_filter_by_kind(self):
        Deck.objects.create(name="Kanji N5", kind=Deck.Kind.KANJI)
        response = self.client.get(reverse("deck_list"), {"kind": "kanji"})
        self.assertEqual([d.name for d in response.context["decks"]], ["Kanji N5"])
