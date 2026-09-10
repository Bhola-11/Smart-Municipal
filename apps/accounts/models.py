"""User identity and authorization models for CivicFlow."""

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _
from apps.core.utils import sanitize_filename


class UserRole(models.TextChoices):
    CITIZEN = 'CITIZEN', _('Citizen')
    STAFF = 'STAFF', _('Municipal Staff / Field Officer')
    MANAGER = 'MANAGER', _('Department Manager / Ward Head')
    ADMIN = 'ADMIN', _('System Administrator')


class User(AbstractUser):
    """
    Custom user model representing all platform actors.
    Distinguished by Role and organizational relationships.
    """
    role = models.CharField(
        max_length=20,
        choices=UserRole.choices,
        default=UserRole.CITIZEN,
        db_index=True,
        help_text=_("Administrative role determining portal interface and access permissions.")
    )
    phone_number = models.CharField(
        max_length=20,
        blank=True,
        db_index=True,
        help_text=_("Primary contact number for SMS updates and notifications.")
    )
    alt_phone = models.CharField(
        max_length=20,
        blank=True,
        help_text=_("Secondary or emergency contact number.")
    )
    address = models.TextField(
        blank=True,
        help_text=_("Residential or office address.")
    )
    ward = models.ForeignKey(
        'wards.Ward',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='users',
        help_text=_("Primary resident ward for citizens, or assigned jurisdiction for officers.")
    )
    department = models.ForeignKey(
        'departments.Department',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='staff_members',
        help_text=_("Municipal department affiliation for staff and managers.")
    )
    designation = models.CharField(
        max_length=100,
        blank=True,
        help_text=_("Official job title (e.g. Junior Engineer, Sanitary Inspector, Zonal Commissioner).")
    )
    employee_id = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        unique=True,
        help_text=_("Official municipal employee registration code.")
    )
    is_verified_citizen = models.BooleanField(
        default=False,
        help_text=_("Whether citizen identity has been verified via national ID or utility bill.")
    )
    profile_image = models.ImageField(
        upload_to=sanitize_filename,
        null=True,
        blank=True,
        help_text=_("User avatar / staff identification portrait.")
    )

    class Meta:
        verbose_name = _('User')
        verbose_name_plural = _('Users')
        ordering = ['-date_joined']

    def __str__(self):
        full_name = self.get_full_name()
        if full_name:
            return f"{full_name} ({self.get_role_display()})"
        return f"{self.username} ({self.get_role_display()})"

    @property
    def is_citizen(self):
        return self.role == UserRole.CITIZEN

    @property
    def is_staff_member(self):
        return self.role == UserRole.STAFF or self.is_superuser

    @property
    def is_manager(self):
        return self.role == UserRole.MANAGER or self.is_superuser

    @property
    def is_admin_user(self):
        return self.role == UserRole.ADMIN or self.is_superuser

    def get_role_badge_class(self):
        mapping = {
            UserRole.CITIZEN: 'bg-emerald-100 text-emerald-800',
            UserRole.STAFF: 'bg-blue-100 text-blue-800',
            UserRole.MANAGER: 'bg-purple-100 text-purple-800',
            UserRole.ADMIN: 'bg-rose-100 text-rose-800 font-bold',
        }
        return mapping.get(self.role, 'bg-gray-100 text-gray-800')
