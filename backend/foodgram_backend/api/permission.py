from rest_framework.permissions import BasePermission

class CustomUsersPermission(BasePermission):
    def has_permission(self, request, view):
        if view.action in ['list', 'retrieve']:
            return True
        return request.user and request.user.is_authenticated