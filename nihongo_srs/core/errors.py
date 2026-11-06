"""Custom error handlers: HTML pages for the website, JSON for the REST API.

Django calls these instead of its built-in pages when DEBUG is False
(``handler400``/``403``/``404``/``500`` in ``config.urls``, ``CSRF_FAILURE_VIEW`` in settings).
400 and 500 pages are rendered without the request context on purpose: they must work even
when the request is malformed or the database is unavailable.
"""

from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.template.loader import render_to_string

API_MESSAGES = {
    400: "Nieprawidłowe żądanie.",
    403: "Brak uprawnień do tego zasobu.",
    404: "Nie znaleziono.",
    500: "Wewnętrzny błąd serwera.",
}


def _is_api(request) -> bool:
    return request.path.startswith("/api/")


def _api_error(status: int) -> JsonResponse:
    return JsonResponse({"detail": API_MESSAGES[status]}, status=status)


def bad_request(request, exception):
    if _is_api(request):
        return _api_error(400)
    return HttpResponse(render_to_string("400.html"), status=400)


def permission_denied(request, exception):
    if _is_api(request):
        return _api_error(403)
    return render(request, "403.html", status=403)


def page_not_found(request, exception):
    if _is_api(request):
        return _api_error(404)
    return render(request, "404.html", status=404)


def server_error(request):
    if _is_api(request):
        return _api_error(500)
    return HttpResponse(render_to_string("500.html"), status=500)


def csrf_failure(request, reason=""):
    if _is_api(request):
        return JsonResponse({"detail": "Błąd weryfikacji CSRF."}, status=403)
    return render(request, "403_csrf.html", status=403)
