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
    path("", include("core.urls")),
]

handler404 = "core.views.page_not_found"
