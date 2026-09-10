"""Citizen feedback and satisfaction rating models."""

from django.db import models
from django.conf import settings
from apps.core.models import TimeStampedModel


class SatisfactionLevel(models.TextChoices):
    VERY_SATISFIED = 'VERY_SATISFIED', 'Very Satisfied'
    SATISFIED = 'SATISFIED', 'Satisfied'
    NEUTRAL = 'NEUTRAL', 'Neutral'
    DISSATISFIED = 'DISSATISFIED', 'Dissatisfied'
    VERY_DISSATISFIED = 'VERY_DISSATISFIED', 'Very Dissatisfied'


class Feedback(TimeStampedModel):
    """
    Citizen satisfaction evaluation submitted upon complaint resolution.
    Acceptance closes docket; rejection reopens docket or escalates.
    """
    complaint = models.OneToOneField(
        'complaints.Complaint',
        on_delete=models.CASCADE,
        related_name='feedback'
    )
    citizen = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='submitted_feedbacks'
    )
    rating = models.PositiveSmallIntegerField(
        choices=[(i, f"{i} Stars") for i in range(1, 6)],
        default=5,
        help_text="1 to 5 Star Rating"
    )
    satisfaction = models.CharField(
        max_length=30,
        choices=SatisfactionLevel.choices,
        default=SatisfactionLevel.SATISFIED
    )
    resolution_accepted = models.BooleanField(
        default=True,
        help_text="True if citizen verifies resolution; False if rejected as unsatisfactory"
    )
    comments = models.TextField(blank=True, help_text="Detailed feedback or remarks")
    rejection_reason = models.TextField(blank=True, help_text="Specific grievance if work rejected")

    class Meta:
        verbose_name = 'Citizen Feedback'
        verbose_name_plural = 'Citizen Feedbacks'
        ordering = ['-created_at']

    def __str__(self):
        verdict = "Accepted" if self.resolution_accepted else "Rejected"
        return f"{self.complaint.complaint_number} - {self.rating}★ ({verdict})"
