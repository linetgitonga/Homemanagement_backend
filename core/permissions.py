from rest_framework import permissions

class IsAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_staff or request.user.is_superuser

class IsHomeowner(permissions.BasePermission):
    def has_permission(self, request, view):
        membership = request.user.householdmembership_set.filter(role='homeowner').first()
        if membership:
            view.household = membership.household
            return True
        return False

class IsHelperInHousehold(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.household.membership_set.filter(user=request.user, role='helper').exists()

class IsViewerInHousehold(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.household.membership_set.filter(user=request.user, role='viewer').exists() and request.method in permissions.SAFE_METHODS

class IsOwnerOrAdmin(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.recorded_by == request.user or request.user.is_staff