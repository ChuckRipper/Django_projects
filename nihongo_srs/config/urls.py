"""Root URL configuration."""

from django.contrib import admin
from django.templatetags.static import static
from django.urls import include, path
from django.views.generic import RedirectView

urlpatterns = [
    path("favicon.ico", RedirectView.as_view(url=static("img/favicon.ico"), permanent=True)),
    path("admin/", admin.site.urls),
    path("api/", include("api.urls")),
    path("konto/", include("accounts.urls")),
    path("talie/", include("decks.urls")),
    path("nauka/", include("study.urls")),
    path("statystyki/", include("stats.urls")),
    path("", include("core.urls")),
]

handler400 = "core.errors.bad_request"
handler403 = "core.errors.permission_denied"
handler404 = "core.errors.page_not_found"
handler500 = "core.errors.server_error"
