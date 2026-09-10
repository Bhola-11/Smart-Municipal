"""Workflow transition history models."""

from django.db import models
from django.conf import settings
from apps.core.models import TimeStampedModel


class WorkflowTransition(TimeStampedModel):
    """
    Immutable historical audit log of every lifecycle state transition
    a complaint undergoes, capturing actor, rationale, and timestamps.
    """
    complaint = models.ForeignKey(
        'complaints.Complaint',
        on_delete=models.CASCADE,
        related_name='workflow_transitions'
    )
    from_status = models.CharField(max_length=30)
    to_status = models.CharField(max_length=30)
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='initiated_transitions'
    )
    notes = models.TextField(
        blank=True,
        help_text="Operational explanation or citizen feedback accompanying this state change"
    )
    reason = models.CharField(
        max_length=150,
        blank=True,
        help_text="Coded reason (e.g. SLABreach, InsufficientDetails, CitizenVerified, WorkDone)"
    )

    class Meta:
        verbose_name = 'Workflow Transition'
        verbose_name_plural = 'Workflow Transitions'
        ordering = ['-created_at']

    def __str__(self):
        actor_title = self.actor.username if self.actor else 'SYSTEM'
        return f"{self.complaint.complaint_number}: {self.from_status} -> {self.to_status} by {actor_title}"
