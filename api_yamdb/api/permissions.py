from rest_framework.permissions import BasePermission, SAFE_METHODS

USER = 'user'
ADMIN = 'admin'
MODERATOR = 'moderator'


class IsAuthor(BasePermission):
    def has_object_permission(self, request, view, obj):
        return request.method in SAFE_METHODS or (
            request.user and obj.author == request.user) or (
                request.user and request.user.role == ADMIN) or (
                    request.user and request.user.role == MODERATOR)


class IsAuthorOrReadOnly(BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in ['POST', 'PATCH', 'DELETE']:
            return obj.author == request.user or (
                request.user.role == ADMIN) or (
                    request.user.role == MODERATOR)
        return True


class IsAdminUser(BasePermission):
    def has_permission(self, request, view):
        return request.user and (request.user.role == ADMIN
                                 or request.user.is_staff)


class IsAdminOrReadOnly(BasePermission):
    def has_permission(self, request, view):
        return request.method in SAFE_METHODS or (
            request.user and request.user.role == ADMIN)


class IsAdminOrModeratorUser(BasePermission):
    def has_permission(self, request, view):
        return request.user and (request.user.role == ADMIN
                                 or request.user.role == MODERATOR)
