from django.contrib.auth import views as auth_views
from django.urls import path

from . import views

urlpatterns = [
    path("rejestracja/", views.RegisterView.as_view(), name="register"),
    path("logowanie/", auth_views.LoginView.as_view(), name="login"),
    path("wyloguj/", auth_views.LogoutView.as_view(), name="logout"),
    path("profil/", views.ProfileView.as_view(), name="profile"),
    # Password reset by e-mail (built-in views, Polish templates in templates/registration/).
    path("haslo/reset/", auth_views.PasswordResetView.as_view(
        email_template_name="registration/password_reset_email.txt",
        html_email_template_name="registration/password_reset_email.html",
        subject_template_name="registration/password_reset_subject.txt",
    ), name="password_reset"),
    path("haslo/reset/wyslano/", auth_views.PasswordResetDoneView.as_view(), name="password_reset_done"),
    path("haslo/reset/<uidb64>/<token>/", auth_views.PasswordResetConfirmView.as_view(), name="password_reset_confirm"),
    path("haslo/reset/gotowe/", auth_views.PasswordResetCompleteView.as_view(), name="password_reset_complete"),
    # Password change for a logged-in user.
    path("haslo/zmiana/", auth_views.PasswordChangeView.as_view(), name="password_change"),
    path("haslo/zmiana/gotowe/", auth_views.PasswordChangeDoneView.as_view(), name="password_change_done"),
]
