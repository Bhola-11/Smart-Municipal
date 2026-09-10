from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from apps.accounts.models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'role', 'department', 'ward', 'is_active')
    list_filter = ('role', 'department', 'is_active', 'is_verified_citizen')
    search_fields = ('username', 'email', 'first_name', 'last_name', 'employee_id')
    fieldsets = UserAdmin.fieldsets + (
        ('Municipal Affiliation', {
            'fields': ('role', 'department', 'ward', 'designation', 'employee_id', 'phone_number', 'alt_phone', 'address', 'is_verified_citizen', 'profile_image')
        }),
    )
