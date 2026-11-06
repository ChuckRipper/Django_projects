from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse


class AccountTests(TestCase):
    def test_register_logs_in_and_creates_profile(self):
        response = self.client.post(reverse("register"), {
            "username": "kenji", "email": "kenji@example.com",
            "password1": "Sakura-2026!", "password2": "Sakura-2026!",
        })
        self.assertRedirects(response, reverse("home"))
        user = User.objects.get(username="kenji")
        self.assertEqual(user.profile.new_cards_per_day, 10)
        self.assertEqual(int(self.client.session["_auth_user_id"]), user.pk)

    def test_register_rejects_duplicate_email(self):
        User.objects.create_user("a", email="a@example.com")
        response = self.client.post(reverse("register"), {
            "username": "b", "email": "A@example.com", "password1": "Sakura-2026!", "password2": "Sakura-2026!",
        })
        self.assertTrue(response.context["form"].errors["email"])

    def test_profile_update(self):
        User.objects.create_user("kenji", password="Sakura-2026!")
        self.client.login(username="kenji", password="Sakura-2026!")
        self.client.post(reverse("profile"), {"new_cards_per_day": 25, "daily_goal": 50})
        self.assertEqual(User.objects.get(username="kenji").profile.new_cards_per_day, 25)

    def test_profile_validation(self):
        User.objects.create_user("kenji", password="Sakura-2026!")
        self.client.login(username="kenji", password="Sakura-2026!")
        response = self.client.post(reverse("profile"), {"new_cards_per_day": 0, "daily_goal": 0})
        self.assertEqual(set(response.context["form"].errors), {"new_cards_per_day", "daily_goal"})

    def test_pages_render(self):
        for name in ("home", "login", "register"):
            self.assertEqual(self.client.get(reverse(name)).status_code, 200)
        self.assertEqual(self.client.get("/nie-ma-takiej-strony/").status_code, 404)

    def test_about_page(self):
        response = self.client.get(reverse("about"))
        self.assertContains(response, "SM-2")
        self.assertContains(response, "KANJIDIC")

    def test_favicon(self):
        response = self.client.get("/favicon.ico")
        self.assertRedirects(response, "/static/img/favicon.ico", status_code=301, fetch_redirect_response=False)
        self.assertContains(self.client.get("/"), "img/favicon.svg")


class CaseInsensitiveLoginTests(TestCase):
    def setUp(self):
        User.objects.create_user("Czarodziej", password="Sakura-2026!")

    def test_login_ignores_letter_case(self):
        for name in ("czarodziej", "CZARODZIEJ", "CzaroDziej"):
            self.assertTrue(self.client.login(username=name, password="Sakura-2026!"), name)
            self.client.logout()

    def test_wrong_password_still_rejected(self):
        self.assertFalse(self.client.login(username="czarodziej", password="zle-haslo"))

    def test_registration_rejects_case_variant(self):
        response = self.client.post(reverse("register"), {
            "username": "czarodziej", "email": "c@example.com",
            "password1": "Sakura-2026!", "password2": "Sakura-2026!",
        })
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["form"].errors["username"])
