"""Service Level Agreement (SLA) policy models and tracking logs."""

from datetime import timedelta
from django.db import models
from django.utils import timezone
from apps.core.models import TimeStampedModel
from apps.complaints.models import ComplaintPriority, ComplaintSeverity


class SLAPolicy(TimeStampedModel):
    """
    Configurable municipal SLA standard governing target response
    and resolution intervals based on jurisdiction, category, or priority.
    """
    name = models.CharField(max_length=150, unique=True, help_text="Descriptive policy identifier")
    department = models.ForeignKey(
        'departments.Department',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='sla_policies',
        help_text="Optional department scope. If null, applies globally."
    )
    category = models.ForeignKey(
        'complaints.Category',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='sla_policies',
        help_text="Optional category scope."
    )
    priority = models.CharField(
        max_length=20,
        choices=ComplaintPriority.choices,
        null=True,
        blank=True,
        help_text="Target priority tier."
    )
    severity = models.CharField(
        max_length=20,
        choices=ComplaintSeverity.choices,
        null=True,
        blank=True,
        help_text="Target severity level."
    )
    response_time_hours = models.PositiveIntegerField(
        default=4,
        help_text="Required initial review/acknowledgment duration in hours"
    )
    resolution_time_hours = models.PositiveIntegerField(
        default=48,
        help_text="Standard deadline to resolve grievance in hours"
    )
    due_soon_threshold_percent = models.PositiveIntegerField(
        default=75,
        help_text="Percentage of SLA time elapsed before marking 'Due Soon' (e.g. 75%)"
    )
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        verbose_name = 'SLA Policy'
        verbose_name_plural = 'SLA Policies'
        ordering = ['priority', 'resolution_time_hours']

    def __str__(self):
        dept_str = f" [{self.department.code}]" if self.department else " [GLOBAL]"
        prio_str = f" - {self.priority}" if self.priority else ""
        return f"{self.name}{dept_str}{prio_str} ({self.resolution_time_hours}h)"


class SLALog(TimeStampedModel):
    """Individual SLA tracking docket tied to each complaint."""
    STATUS_CHOICES = [
        ('ON_TRACK', 'On Track'),
        ('DUE_SOON', 'Due Soon'),
        ('BREACHED', 'Breached'),
        ('MET_WITHIN_SLA', 'Met Within SLA'),
        ('MET_AFTER_SLA', 'Met After SLA'),
    ]

    complaint = models.OneToOneField(
        'complaints.Complaint',
        on_delete=models.CASCADE,
        related_name='sla_record'
    )
    policy = models.ForeignKey(
        SLAPolicy,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='logged_complaints'
    )
    start_time = models.DateTimeField(default=timezone.now)
    deadline = models.DateTimeField(db_index=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ON_TRACK', db_index=True)
    breached_at = models.DateTimeField(null=True, blank=True)
    actual_hours_taken = models.FloatField(null=True, blank=True)

    class Meta:
        verbose_name = 'SLA Log'
        verbose_name_plural = 'SLA Logs'
        ordering = ['deadline']

    def __str__(self):
        return f"{self.complaint.complaint_number} - SLA: {self.status} (Due: {self.deadline.strftime('%Y-%m-%d %H:%M')})"

    @property
    def remaining_seconds(self):
        """Seconds until deadline. Negative if breached."""
        if self.complaint.resolved_at:
            return 0
        diff = self.deadline - timezone.now()
        return diff.total_seconds()

    @property
    def total_sla_seconds(self):
        return (self.deadline - self.start_time).total_seconds()

    @property
    def percentage_elapsed(self):
        if self.complaint.resolved_at:
            return 100
        total = self.total_sla_seconds
        if total <= 0:
            return 100
        elapsed = (timezone.now() - self.start_time).total_seconds()
        pct = (elapsed / total) * 100
        return min(max(int(pct), 0), 100)
