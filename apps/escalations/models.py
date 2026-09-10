"""Escalation ledger and hierarchical intervention models."""

from django.db import models
from django.conf import settings
from django.utils import timezone
from apps.core.models import TimeStampedModel


class EscalationReason(models.TextChoices):
    SLA_BREACH = 'SLA_BREACH', 'SLA Target Expired'
    SLA_APPROACHING = 'SLA_APPROACHING', 'SLA Deadline Imminent'
    CITIZEN_REJECTION = 'CITIZEN_REJECTION', 'Citizen Rejected Inadequate Resolution'
    PROLONGED_INACTIVITY = 'PROLONGED_INACTIVITY', 'No Progress for 48+ Hours'
    MANAGER_OVERRIDE = 'MANAGER_OVERRIDE', 'Manager Administrative Intervention'
    PUBLIC_HAZARD = 'PUBLIC_HAZARD', 'Immediate Hazard / Safety Emergency'


class Escalation(TimeStampedModel):
    """
    Formal escalation record elevating unresolved complaints
    to higher executive tiers.
    """
    complaint = models.ForeignKey(
        'complaints.Complaint',
        on_delete=models.CASCADE,
        related_name='escalation_records'
    )
    level = models.PositiveIntegerField(
        default=1,
        help_text="Escalation Tier (1=Supervisor, 2=Dept Head, 3=Commissioner)"
    )
    reason = models.CharField(
        max_length=40,
        choices=EscalationReason.choices,
        default=EscalationReason.SLA_BREACH,
        db_index=True
    )
    description = models.TextField(
        help_text="Detailed justification or root-cause description for escalation"
    )
    previous_owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='escalations_from_me'
    )
    escalated_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='escalations_assigned_to_me',
        help_text="Higher officer assigned to review the escalation"
    )
    is_resolved = models.BooleanField(default=False, db_index=True)
    resolution_notes = models.TextField(blank=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'Escalation'
        verbose_name_plural = 'Escalations'
        ordering = ['-created_at']

    def __str__(self):
        return f"Level {self.level} Escalation: {self.complaint.complaint_number} ({self.get_reason_display()})"

    def mark_resolved(self, notes=''):
        self.is_resolved = True
        self.resolution_notes = notes
        self.resolved_at = timezone.now()
        self.save()
