"""Case-insensitive login: "Czarodziej", "czarodziej" and "CzaroDziej" are the same user."""

from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend


class CaseInsensitiveModelBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        user_model = get_user_model()
        if username is None:
            username = kwargs.get(user_model.USERNAME_FIELD)
        if username is None or password is None:
            return None
        users = user_model._default_manager.filter(**{f"{user_model.USERNAME_FIELD}__iexact": username})
        # Accounts created before this backend may differ only by letter case: prefer the exact match.
        user = users.filter(**{user_model.USERNAME_FIELD: username}).first() or users.first()
        if user is None:
            user_model().set_password(password)  # equalise timing with the "user exists" path
            return None
        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None
