from django.urls import path

from . import views

urlpatterns = [
    path("", views.DeckListView.as_view(), name="deck_list"),
    path("nowa/", views.DeckCreateView.as_view(), name="deck_create"),
    path("<int:pk>/", views.DeckDetailView.as_view(), name="deck_detail"),
    path("<int:pk>/edytuj/", views.DeckUpdateView.as_view(), name="deck_update"),
    path("<int:pk>/usun/", views.DeckDeleteView.as_view(), name="deck_delete"),
    path("<int:deck_pk>/karty/nowa/", views.CardCreateView.as_view(), name="card_create"),
    path("karty/<int:pk>/edytuj/", views.CardUpdateView.as_view(), name="card_update"),
    path("karty/<int:pk>/usun/", views.CardDeleteView.as_view(), name="card_delete"),
]
