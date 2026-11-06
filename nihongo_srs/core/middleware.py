"""Fill Django's empty 405 responses with a proper page (the website) or JSON (the API)."""

from django.http import JsonResponse
from django.template.loader import render_to_string


class MethodNotAllowedPageMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if response.status_code != 405 or response.content:
            return response  # DRF already returns a JSON body for 405
        allowed = response.get("Allow", "")
        if request.path.startswith("/api/"):
            replacement = JsonResponse({"detail": f"Niedozwolona metoda \"{request.method}\"."}, status=405)
        else:
            replacement = response.__class__(allowed.split(", ") if allowed else [],
                                             render_to_string("405.html", request=request))
        if allowed:
            replacement["Allow"] = allowed
        return replacement
