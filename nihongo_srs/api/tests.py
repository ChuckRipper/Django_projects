from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework.test import APITestCase

from decks.models import Card, Deck
from study.models import ReviewState


class ApiTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user("ania", password="Haslo-12345")
        self.other = User.objects.create_user("bartek", password="Haslo-12345")
        self.system = Deck.objects.create(name="Hiragana", kind=Deck.Kind.KANA)
        self.card = Card.objects.create(deck=self.system, front="あ", back="a")
        self.foreign = Deck.objects.create(name="Bartka", owner=self.other)

    def authenticate(self):
        response = self.client.post(reverse("token_obtain_pair"), {"username": "ania", "password": "Haslo-12345"})
        self.assertEqual(response.status_code, 200)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {response.data['access']}")

    def test_endpoints_require_authentication(self):
        self.assertEqual(self.client.get("/api/decks/").status_code, 401)

    def test_wrong_password_gives_no_token(self):
        response = self.client.post(reverse("token_obtain_pair"), {"username": "ania", "password": "zle"})
        self.assertEqual(response.status_code, 401)

    def test_register(self):
        response = self.client.post(reverse("api-register"), {
            "username": "kenji", "email": "kenji@example.com", "password": "Sakura-2026!",
        })
        self.assertEqual(response.status_code, 201)
        self.assertNotIn("password", response.data)

    def test_deck_list_hides_foreign_decks(self):
        self.authenticate()
        names = [d["name"] for d in self.client.get("/api/decks/").data["results"]]
        self.assertEqual(names, ["Hiragana"])

    def test_system_deck_is_read_only(self):
        self.authenticate()
        response = self.client.patch(f"/api/decks/{self.system.pk}/", {"name": "Hack"})
        self.assertEqual(response.status_code, 403)

    def test_create_own_deck_and_card(self):
        self.authenticate()
        deck = self.client.post("/api/decks/", {"name": "Moja", "kind": "vocabulary"}).data
        response = self.client.post("/api/cards/", {"deck": deck["id"], "front": "猫", "back": "kot"})
        self.assertEqual(response.status_code, 201)
        response = self.client.post("/api/cards/", {"deck": self.system.pk, "front": "x", "back": "y"})
        self.assertEqual(response.status_code, 400)

    def test_queue_and_review(self):
        self.authenticate()
        queue = self.client.get("/api/study/queue/").data
        self.assertEqual(queue[0]["front"], "あ")
        response = self.client.post("/api/study/review/", {"card": self.card.pk, "rating": 2})
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["repetitions"], 1)
        self.assertTrue(ReviewState.objects.filter(user=self.user, card=self.card).exists())

    def test_review_of_invisible_card_is_404(self):
        self.authenticate()
        hidden = Card.objects.create(deck=self.foreign, front="x", back="y")
        self.assertEqual(self.client.post("/api/study/review/", {"card": hidden.pk, "rating": 2}).status_code, 404)

    def test_summary(self):
        self.authenticate()
        data = self.client.get("/api/stats/summary/").data
        self.assertEqual(data["new_available"], 1)

    def test_swagger_and_schema_available(self):
        self.assertEqual(self.client.get("/api/schema/").status_code, 200)
        self.assertEqual(self.client.get("/api/docs/").status_code, 200)
