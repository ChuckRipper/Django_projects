from django.urls import path

from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("o-aplikacji/", views.about, name="about"),
]
