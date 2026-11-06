from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from . import views

router = DefaultRouter()
router.register("decks", views.DeckViewSet, basename="api-deck")
router.register("cards", views.CardViewSet, basename="api-card")

urlpatterns = [
    path("auth/register/", views.RegisterView.as_view(), name="api-register"),
    path("auth/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("auth/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("study/queue/", views.StudyQueueView.as_view(), name="api-study-queue"),
    path("study/review/", views.ReviewView.as_view(), name="api-study-review"),
    path("stats/summary/", views.SummaryView.as_view(), name="api-stats-summary"),
    path("stats/daily/", views.DailyReviewsView.as_view(), name="api-stats-daily"),
    path("schema/", SpectacularAPIView.as_view(), name="schema"),
    path("docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
    path("", include(router.urls)),
]
