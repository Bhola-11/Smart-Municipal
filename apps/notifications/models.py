"""Internal notification and alert models."""

from django.db import models
from django.conf import settings
from django.utils import timezone
from apps.core.models import TimeStampedModel


class NotificationPriority(models.TextChoices):
    NORMAL = 'NORMAL', 'Standard Update'
    HIGH = 'HIGH', 'High Priority Alert'
    URGENT = 'URGENT', 'Urgent Escalation'


class Notification(TimeStampedModel):
    """
    In-app alert informing citizens and municipal officials of
    status updates, assignments, queries, and SLA breaches.
    """
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications'
    )
    title = models.CharField(max_length=200)
    message = models.TextField()
    notification_type = models.CharField(
        max_length=50,
        default='SYSTEM',
        db_index=True,
        help_text="STATUS, ASSIGNMENT, SLA_ALERT, ESCALATION, MESSAGE, FEEDBACK"
    )
    priority = models.CharField(
        max_length=20,
        choices=NotificationPriority.choices,
        default=NotificationPriority.NORMAL
    )
    related_complaint = models.ForeignKey(
        'complaints.Complaint',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='associated_notifications'
    )
    is_read = models.BooleanField(default=False, db_index=True)
    read_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'Notification'
        verbose_name_plural = 'Notifications'
        ordering = ['-created_at']

    def __str__(self):
        return f"To {self.recipient.username}: {self.title} ({'Read' if self.is_read else 'Unread'})"

    def mark_as_read(self):
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save(update_fields=['is_read', 'read_at'])
