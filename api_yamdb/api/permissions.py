from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsAuthor(BasePermission):
    def has_object_permission(self, request, view, obj):
        return request.method in SAFE_METHODS or obj.author == request.user or request.user.role == 'admin' or request.user.role == 'moderator'


class IsAuthorOrReadOnly(BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in ['POST', 'PATCH', 'DELETE']:
            return request.method in SAFE_METHODS or obj.author == request.user or request.user.role == 'admin' or request.user.role == 'moderator'
        return True


class IsAdminUser(BasePermission):
    def has_permission(self, request, view):
        return request.user and (request.user.role == 'admin'
                                 or request.user.is_staff)


class IsAdminOrReadOnly(BasePermission):
    def has_permission(self, request, view):
        if request.method in ['POST', 'PATCH', 'DELETE']:
            return request.user and request.user.role == 'admin'
        return True


class IsAdminOrModeratorUser(BasePermission):
    def has_permission(self, request, view):
        return request.user and (request.user.role == 'admin'
                                 or request.user.role == 'moderator')
