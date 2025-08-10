from rest_framework import permissions
from rest_framework.permissions import BasePermission


class IsAuthenticatedAuthorOrReadOnly(BasePermission):
    """Права доступа:
     - Безопасные методы (GET, HEAD, OPTIONS) - всем
     - Изменение данных - только автору
     - Остальные действия - только аутентифицированным
    """
    def has_permission(self, request, view):
        if view.action in ['list', 'retrieve']:
            return True
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        return (request.method in permissions.SAFE_METHODS
                or obj.author == request.user)
