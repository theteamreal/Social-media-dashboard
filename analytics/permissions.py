from rest_framework import permissions

class IsOwner(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if hasattr(obj, 'user'):
            return obj.user == request.user
        elif hasattr(obj, 'social_account'):
            return obj.social_account.user == request.user
        elif hasattr(obj, 'post'):
            return obj.post.social_account.user == request.user
        return False