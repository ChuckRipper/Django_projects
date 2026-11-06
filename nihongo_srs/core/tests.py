from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied, SuspiciousOperation
from django.test import Client, TestCase, override_settings
from django.urls import path

from config.urls import handler400, handler403, handler404, handler500, urlpatterns as project_urls  # noqa: F401


def _raise_bad_request(request):
    raise SuspiciousOperation("test")


def _raise_forbidden(request):
    raise PermissionDenied


def _raise_server_error(request):
    raise RuntimeError("test")


# Test URLconf: the project's URLs plus views that fail on purpose (HTML and API variants).
urlpatterns = [
    path("test/400/", _raise_bad_request),
    path("test/403/", _raise_forbidden),
    path("test/500/", _raise_server_error),
    path("api/test/400/", _raise_bad_request),
    path("api/test/403/", _raise_forbidden),
    path("api/test/500/", _raise_server_error),
    *project_urls,
]


@override_settings(ROOT_URLCONF=__name__)
class ErrorPageTests(TestCase):
    """Every error status gets its own page on the website and a JSON body in the API."""

    def setUp(self):
        self.client = Client(raise_request_exception=False)

    def assert_html_error(self, url, status, text):
        response = self.client.get(url)
        self.assertEqual(response.status_code, status)
        self.assertContains(response, text, status_code=status)
        self.assertContains(response, f"BŁĄD {status}", status_code=status)

    def test_html_error_pages(self):
        self.assert_html_error("/test/400/", 400, "Nieprawidłowe żądanie")
        self.assert_html_error("/test/403/", 403, "Brak dostępu")
        self.assert_html_error("/nie-ma-takiej-strony/", 404, "Strona nie istnieje")
        with self.assertLogs("django.request", "ERROR"):  # 500s are still logged for the admin
            self.assert_html_error("/test/500/", 500, "Coś poszło nie tak")

    def test_api_errors_are_json(self):
        for url, status in (("/api/test/400/", 400), ("/api/test/403/", 403),
                            ("/api/nie-ma/", 404), ("/api/test/500/", 500)):
            with self.assertLogs("django", "WARNING"):
                response = self.client.get(url)
            self.assertEqual(response.status_code, status, url)
            self.assertEqual(response["Content-Type"], "application/json")
            self.assertIn("detail", response.json())

    def test_disallowed_host_gives_400_page(self):
        with self.assertLogs("django.security", "ERROR"):
            response = self.client.get("/", HTTP_HOST="zly-host.example.com")
        self.assertContains(response, "BŁĄD 400", status_code=400)

    def test_csrf_failure_page(self):
        client = Client(enforce_csrf_checks=True)
        response = client.post("/konto/logowanie/", {"username": "x", "password": "y"})
        self.assertContains(response, "Formularz wygasł", status_code=403)

    def test_api_unauthenticated_is_401_json(self):
        response = self.client.get("/api/decks/")
        self.assertEqual(response.status_code, 401)
        self.assertIn("detail", response.json())
        response = self.client.post("/api/auth/token/", {"username": "nikt", "password": "zle"})
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()["detail"], "Nieprawidłowy login lub hasło.")

    def test_web_pages_redirect_anonymous_to_login(self):
        response = self.client.get("/nauka/")
        self.assertRedirects(response, "/konto/logowanie/?next=/nauka/", fetch_redirect_response=False)

    def test_wrong_method_is_405(self):
        get_user_model().objects.create_user("kenji", password="Sakura-2026!")
        self.client.login(username="kenji", password="Sakura-2026!")
        response = self.client.get("/konto/wyloguj/")
        self.assertContains(response, "BŁĄD 405", status_code=405)
        self.assertEqual(response["Allow"], "POST, OPTIONS")
        self.assertEqual(self.client.delete("/api/study/queue/").status_code, 405)
