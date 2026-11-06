from rest_framework import permissions


class IsOwnerOrReadOnly(permissions.BasePermission):
    """System decks (owner = None) and other users' content are read-only."""

    message = "Możesz modyfikować tylko własne talie i karty."

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        owner_id = getattr(obj, "owner_id", None)
        if owner_id is None and hasattr(obj, "deck"):
            owner_id = obj.deck.owner_id
        return owner_id is not None and owner_id == request.user.id
