"""Evidence and file attachment models with lifecycle stages."""

import os
from django.db import models
from django.conf import settings
from apps.core.models import TimeStampedModel
from apps.core.utils import sanitize_filename


class AttachmentStage(models.TextChoices):
    SUBMISSION = 'SUBMISSION', 'Citizen Initial Evidence'
    BEFORE_WORK = 'BEFORE_WORK', 'Before Work Inspection'
    DURING_WORK = 'DURING_WORK', 'Work In Progress Evidence'
    AFTER_RESOLUTION = 'AFTER_RESOLUTION', 'Post-Resolution Proof'
    OFFICIAL_REPORT = 'OFFICIAL_REPORT', 'Technical Departmental Report'


class Attachment(TimeStampedModel):
    """
    Evidence file linked to a complaint, categorized by operational stage
    (initial evidence, before work, during repair, completed state).
    """
    complaint = models.ForeignKey(
        'complaints.Complaint',
        on_delete=models.CASCADE,
        related_name='attachments'
    )
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='uploaded_attachments'
    )
    file = models.FileField(upload_to=sanitize_filename)
    caption = models.CharField(max_length=255, blank=True, help_text="Short description of photo or document")
    stage = models.CharField(
        max_length=30,
        choices=AttachmentStage.choices,
        default=AttachmentStage.SUBMISSION,
        db_index=True
    )
    file_size = models.PositiveIntegerField(default=0, help_text="Size in bytes")
    file_type = models.CharField(max_length=50, blank=True)
    is_internal_only = models.BooleanField(
        default=False,
        help_text="If true, visible only to municipal personnel, not citizen."
    )

    class Meta:
        verbose_name = 'Attachment'
        verbose_name_plural = 'Attachments'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.complaint.complaint_number} - {self.get_stage_display()} ({self.caption or self.file.name})"

    @property
    def is_image(self):
        ext = os.path.splitext(self.file.name)[1].lower()
        return ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp']

    def save(self, *args, **kwargs):
        if self.file and not self.file_size:
            try:
                self.file_size = self.file.size
            except Exception:
                pass
        super().save(*args, **kwargs)
