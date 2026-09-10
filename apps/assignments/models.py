"""Staff assignment and delegation tracking models."""

from django.db import models
from django.conf import settings
from apps.core.models import TimeStampedModel


class AssignmentStatus(models.TextChoices):
    PENDING = 'PENDING', 'Pending Acceptance'
    ACCEPTED = 'ACCEPTED', 'Accepted by Staff'
    REJECTED = 'REJECTED', 'Rejected / Reassigned'
    REASSIGNED = 'REASSIGNED', 'Reassigned by Manager'
    COMPLETED = 'COMPLETED', 'Work Completed'


class Assignment(TimeStampedModel):
    """
    Tracks delegation of a civic complaint to a specific field engineer or officer.
    Maintains complete audit chain of assignments, handovers, and rejections.
    """
    complaint = models.ForeignKey(
        'complaints.Complaint',
        on_delete=models.CASCADE,
        related_name='assignments'
    )
    staff = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='assigned_work_orders',
        help_text="The field officer or technician assigned to perform the resolution"
    )
    assigned_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='delegated_assignments',
        help_text="Manager or administrator who issued this assignment"
    )
    reason = models.TextField(
        blank=True,
        help_text="Instructions, priority rationale, or technical directives"
    )
    status = models.CharField(
        max_length=20,
        choices=AssignmentStatus.choices,
        default=AssignmentStatus.PENDING,
        db_index=True
    )
    rejection_reason = models.TextField(
        blank=True,
        help_text="Reason given by staff if declining assignment"
    )
    accepted_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'Work Assignment'
        verbose_name_plural = 'Work Assignments'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.complaint.complaint_number} -> {self.staff.username} ({self.status})"
