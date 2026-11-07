from django.urls import path

from . import views

urlpatterns = [
    path("", views.StudyView.as_view(), name="study"),
    path("talia/<int:deck_pk>/", views.StudyView.as_view(), name="study_deck"),
    path("tryb/", views.AnswerModeToggleView.as_view(), name="answer_mode_toggle"),
]
