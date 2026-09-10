"""Role-based authorization decorators and mixins."""

from functools import wraps
from django.contrib.auth.mixins import AccessMixin
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
from django.contrib import messages
from apps.accounts.models import UserRole


def role_required(allowed_roles):
    """Decorator for views requiring one of the specified roles."""
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('accounts:login')
            if request.user.is_superuser or request.user.role in allowed_roles:
                return view_func(request, *args, **kwargs)
            messages.error(request, "Access denied. You do not hold permissions for this municipal portal area.")
            raise PermissionDenied
        return _wrapped_view
    return decorator


def citizen_required(view_func):
    return role_required([UserRole.CITIZEN])(view_func)


def staff_required(view_func):
    return role_required([UserRole.STAFF, UserRole.MANAGER, UserRole.ADMIN])(view_func)


def manager_required(view_func):
    return role_required([UserRole.MANAGER, UserRole.ADMIN])(view_func)


def admin_required(view_func):
    return role_required([UserRole.ADMIN])(view_func)


class RoleRequiredMixin(AccessMixin):
    """CBV mixin verifying that current user holds appropriate role."""
    allowed_roles = []

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if not (request.user.is_superuser or request.user.role in self.allowed_roles):
            messages.error(request, "You are not authorized to view this administrative resource.")
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)


class CitizenRequiredMixin(RoleRequiredMixin):
    allowed_roles = [UserRole.CITIZEN]


class StaffRequiredMixin(RoleRequiredMixin):
    allowed_roles = [UserRole.STAFF, UserRole.MANAGER, UserRole.ADMIN]


class ManagerRequiredMixin(RoleRequiredMixin):
    allowed_roles = [UserRole.MANAGER, UserRole.ADMIN]


class AdminRequiredMixin(RoleRequiredMixin):
    allowed_roles = [UserRole.ADMIN]
