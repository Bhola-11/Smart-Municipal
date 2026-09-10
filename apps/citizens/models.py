"""Citizen profile extensions and verification records."""

from django.db import models
from django.conf import settings
from apps.core.models import TimeStampedModel
from apps.core.utils import sanitize_filename


class CitizenVerification(TimeStampedModel):
    """Citizen identity proof and municipal resident verification record."""
    STATUS_CHOICES = [
        ('PENDING', 'Verification Pending'),
        ('VERIFIED', 'Identity Verified'),
        ('REJECTED', 'Verification Rejected'),
    ]
    DOCUMENT_TYPES = [
        ('NATIONAL_ID', 'National Identity Card'),
        ('PASSPORT', 'Passport'),
        ('DRIVERS_LICENSE', 'Driving License'),
        ('UTILITY_BILL', 'Municipal Utility Bill'),
        ('PROPERTY_TAX', 'Property Tax Receipt'),
    ]

    citizen = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='verification_record'
    )
    document_type = models.CharField(max_length=50, choices=DOCUMENT_TYPES)
    document_number = models.CharField(max_length=100)
    document_file = models.FileField(upload_to=sanitize_filename)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING', db_index=True)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_verifications'
    )
    rejection_reason = models.TextField(blank=True)
    verified_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'Citizen Verification'
        verbose_name_plural = 'Citizen Verifications'

    def __str__(self):
        return f"{self.citizen.username} - {self.get_document_type_display()} ({self.status})"
