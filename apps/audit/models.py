"""Immutable audit logging models."""

from django.db import models
from django.conf import settings
from apps.core.models import TimeStampedModel


class AuditLog(TimeStampedModel):
    """
    Immutable ledger of all security, operational, and lifecycle events
    within the municipal platform.
    """
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='audit_records',
        help_text="User who initiated the action (null if automated system event)."
    )
    action = models.CharField(
        max_length=100,
        db_index=True,
        help_text="Standardized action code (e.g. COMPLAINT_CREATED, STATUS_TRANSITION, SLA_BREACHED)."
    )
    target_model = models.CharField(
        max_length=100,
        db_index=True,
        help_text="Name of the affected domain model (e.g. Complaint, Assignment, Escalation)."
    )
    target_id = models.CharField(
        max_length=100,
        db_index=True,
        help_text="Primary key or reference identifier of the affected record."
    )
    details = models.TextField(
        blank=True,
        help_text="Detailed payload, before/after differences, or description of change."
    )
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        help_text="Client IP address where the request originated."
    )
    user_agent = models.CharField(
        max_length=255,
        blank=True,
        help_text="Browser user agent string."
    )

    class Meta:
        verbose_name = 'Audit Log'
        verbose_name_plural = 'Audit Logs'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['action', 'created_at']),
            models.Index(fields=['target_model', 'target_id']),
        ]

    def __str__(self):
        actor_name = self.actor.username if self.actor else 'SYSTEM'
        return f"[{self.created_at.strftime('%Y-%m-%d %H:%M:%S')}] {actor_name} -> {self.action} on {self.target_model}:{self.target_id}"
