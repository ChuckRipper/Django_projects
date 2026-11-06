from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .models import Profile


class RegisterForm(UserCreationForm):
    email = forms.EmailField(label="E-mail", required=True)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "email")

    def clean_username(self):
        username = super().clean_username()
        if User.objects.filter(username__iexact=username).exists():
            raise forms.ValidationError("Ta nazwa użytkownika jest już zajęta (wielkość liter nie ma znaczenia).")
        return username

    def clean_email(self):
        email = self.cleaned_data["email"].lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("Konto z tym adresem e-mail już istnieje.")
        return email


class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ("new_cards_per_day", "daily_goal")
        widgets = {
            "new_cards_per_day": forms.NumberInput(attrs={"min": 1, "max": 100}),
            "daily_goal": forms.NumberInput(attrs={"min": 1, "max": 500}),
        }

    def clean_new_cards_per_day(self):
        value = self.cleaned_data["new_cards_per_day"]
        if not 1 <= value <= 100:
            raise forms.ValidationError("Podaj wartość od 1 do 100.")
        return value
