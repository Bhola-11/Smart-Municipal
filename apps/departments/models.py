"""Municipal department structure models."""

from django.db import models
from django.conf import settings
from apps.core.models import TimeStampedModel


class Department(TimeStampedModel):
    """
    Municipal administrative division (e.g. Public Works, Sanitation, Water Supply).
    Complaints are mapped and routed to departments based on category.
    """
    name = models.CharField(max_length=150, unique=True, help_text="Department title")
    code = models.CharField(max_length=20, unique=True, db_index=True, help_text="Short code e.g. PWD, SWM, WSS")
    description = models.TextField(blank=True, help_text="Operational mandate and civic scope")
    head_officer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='headed_departments',
        help_text="Chief engineer or administrative head"
    )
    email = models.EmailField(blank=True, help_text="Official department desk email")
    phone = models.CharField(max_length=30, blank=True, help_text="Helpdesk telephone number")
    office_location = models.CharField(max_length=255, blank=True, help_text="Municipal HQ room / office address")
    default_sla_hours = models.PositiveIntegerField(
        default=48,
        help_text="Standard baseline SLA duration in hours for this department"
    )
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        verbose_name = 'Department'
        verbose_name_plural = 'Departments'
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.code})"

    @property
    def total_staff_count(self):
        return self.staff_members.count()

    @property
    def active_complaint_count(self):
        return self.complaints.exclude(status__in=['CLOSED', 'REJECTED', 'DUPLICATE']).count()
