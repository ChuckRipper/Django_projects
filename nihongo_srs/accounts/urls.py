from django.contrib.auth import views as auth_views
from django.urls import path

from . import views

urlpatterns = [
    path("rejestracja/", views.RegisterView.as_view(), name="register"),
    path("logowanie/", auth_views.LoginView.as_view(), name="login"),
    path("wyloguj/", auth_views.LogoutView.as_view(), name="logout"),
    path("profil/", views.ProfileView.as_view(), name="profile"),
]
