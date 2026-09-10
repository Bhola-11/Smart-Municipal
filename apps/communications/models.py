"""Message timeline and communication models."""

from django.db import models
from django.conf import settings
from apps.core.models import TimeStampedModel


class MessageType(models.TextChoices):
    CITIZEN_UPDATE = 'CITIZEN_UPDATE', 'Citizen Query / Update'
    STAFF_REPLY = 'STAFF_REPLY', 'Municipal Staff Response'
    INTERNAL_NOTE = 'INTERNAL_NOTE', 'Internal Departmental Note'
    OFFICIAL_DIRECTIVE = 'OFFICIAL_DIRECTIVE', 'Managerial Instruction'
    SYSTEM_NOTICE = 'SYSTEM_NOTICE', 'Automated System Notice'


class ComplaintMessage(TimeStampedModel):
    """
    Structured dialogue and timeline messaging between citizen and municipal officers,
    supporting private internal notes restricted to municipal personnel.
    """
    complaint = models.ForeignKey(
        'complaints.Complaint',
        on_delete=models.CASCADE,
        related_name='messages'
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='sent_complaint_messages'
    )
    message_type = models.CharField(
        max_length=30,
        choices=MessageType.choices,
        default=MessageType.CITIZEN_UPDATE,
        db_index=True
    )
    message = models.TextField()
    is_internal_only = models.BooleanField(
        default=False,
        db_index=True,
        help_text="If true, note is visible only to municipal staff and managers."
    )

    class Meta:
        verbose_name = 'Complaint Message'
        verbose_name_plural = 'Complaint Messages'
        ordering = ['created_at']

    def __str__(self):
        return f"{self.complaint.complaint_number} - {self.sender.username}: {self.message[:40]}"
