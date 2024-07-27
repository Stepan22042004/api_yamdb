from rest_framework.permissions import BasePermission, SAFE_METHODS

from api.constants import ADMIN, MODERATOR


class IsAuthor(BasePermission):
    def has_object_permission(self, request, view, obj):
        return request.method in SAFE_METHODS or (
            request.user.is_authenticated
            and (obj.author == request.user
                 or request.user.role == ADMIN
                 or request.user.role == MODERATOR))


class IsAuthorOrReadOnly(BasePermission):
    def has_object_permission(self, request, view, obj):
        return request.method in SAFE_METHODS or (
            obj.author == request.user or (
                request.user.role == ADMIN) or (
                    request.user.role == MODERATOR))


class IsAdminUser(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and (
            request.user.role == ADMIN
            or request.user.is_staff)


class IsAdminOrReadOnly(BasePermission):
    def has_permission(self, request, view):
        return request.method in SAFE_METHODS or (
            request.user.is_authenticated and request.user.role == ADMIN)


class IsAdminOrModeratorUser(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and (
            request.user.role == ADMIN
            or request.user.role == MODERATOR)
