"""Authentication, registration, and user management views."""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib import messages
from apps.accounts.forms import CitizenRegistrationForm, CustomLoginForm, UserProfileForm, StaffCreationForm
from apps.accounts.models import User, UserRole
from apps.accounts.permissions import manager_required, admin_required
from apps.audit.utils import record_audit_log


def register_view(request):
    """Citizen registration view."""
    if request.user.is_authenticated:
        return redirect('dashboard:index')

    if request.method == 'POST':
        form = CitizenRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            record_audit_log(
                actor=user,
                action='CITIZEN_REGISTRATION',
                target_model='accounts.User',
                target_id=str(user.id),
                details=f"New citizen registered: {user.username}",
                request=request
            )
            messages.success(request, f"Welcome to CivicFlow, {user.first_name}! Your citizen account has been established.")
            return redirect('dashboard:index')
        else:
            messages.error(request, "Please review the highlighted errors in your registration.")
    else:
        form = CitizenRegistrationForm()

    return render(request, 'accounts/register.html', {'form': form, 'title': 'Citizen Portal Registration'})


def login_view(request):
    """Unified authentication view with redirection based on role."""
    if request.user.is_authenticated:
        return redirect('dashboard:index')

    if request.method == 'POST':
        form = CustomLoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            record_audit_log(
                actor=user,
                action='USER_LOGIN',
                target_model='accounts.User',
                target_id=str(user.id),
                details=f"User logged in with role {user.role}",
                request=request
            )
            messages.info(request, f"Welcome back, {user.get_full_name() or user.username}.")
            next_url = request.GET.get('next')
            if next_url:
                return redirect(next_url)
            return redirect('dashboard:index')
        else:
            messages.error(request, "Invalid username or password. Please verify your civic credentials.")
    else:
        form = CustomLoginForm()

    return render(request, 'accounts/login.html', {'form': form, 'title': 'CivicFlow Portal Authentication'})


def logout_view(request):
    """Safe user logout."""
    if request.user.is_authenticated:
        record_audit_log(
            actor=request.user,
            action='USER_LOGOUT',
            target_model='accounts.User',
            target_id=str(request.user.id),
            details=f"User {request.user.username} logged out",
            request=request
        )
        logout(request)
        messages.success(request, "You have been securely logged out of CivicFlow.")
    return redirect('accounts:login')


@login_required
def profile_view(request):
    """User profile management."""
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            record_audit_log(
                actor=request.user,
                action='PROFILE_UPDATE',
                target_model='accounts.User',
                target_id=str(request.user.id),
                details="User profile information updated",
                request=request
            )
            messages.success(request, "Your profile details have been saved successfully.")
            return redirect('accounts:profile')
    else:
        form = UserProfileForm(instance=request.user)

    return render(request, 'accounts/profile.html', {
        'form': form,
        'title': 'My Municipal Profile',
        'user': request.user
    })


@login_required
def password_change_view(request):
    """Password update view."""
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            record_audit_log(
                actor=request.user,
                action='PASSWORD_CHANGE',
                target_model='accounts.User',
                target_id=str(request.user.id),
                details="User password changed",
                request=request
            )
            messages.success(request, "Your security password has been updated.")
            return redirect('accounts:profile')
    else:
        form = PasswordChangeForm(request.user)

    return render(request, 'accounts/change_password.html', {'form': form, 'title': 'Update Security Password'})


@admin_required
def staff_management_view(request):
    """List and manage all municipal personnel."""
    staff_list = User.objects.exclude(role=UserRole.CITIZEN).select_related('department', 'ward').order_by('department__name', 'username')
    return render(request, 'management/staff_list.html', {
        'staff_list': staff_list,
        'title': 'Municipal Personnel Directory'
    })


@admin_required
def create_staff_view(request):
    """Create a new staff or manager user."""
    if request.method == 'POST':
        form = StaffCreationForm(request.POST)
        if form.is_valid():
            new_staff = form.save()
            record_audit_log(
                actor=request.user,
                action='STAFF_CREATED',
                target_model='accounts.User',
                target_id=str(new_staff.id),
                details=f"Created staff account {new_staff.username} ({new_staff.role})",
                request=request
            )
            messages.success(request, f"Personnel account for {new_staff.get_full_name() or new_staff.username} created.")
            return redirect('accounts:staff_list')
    else:
        form = StaffCreationForm()

    return render(request, 'management/create_staff.html', {
        'form': form,
        'title': 'Onboard Municipal Officer'
    })
