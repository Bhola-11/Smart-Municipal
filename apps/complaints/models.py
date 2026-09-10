"""Core Complaint models, categories, and priority metrics."""

from django.db import models
from django.conf import settings
from django.utils import timezone
from django.urls import reverse
from apps.core.models import TimeStampedModel
from apps.core.utils import generate_complaint_reference


class ComplaintPriority(models.TextChoices):
    LOW = 'LOW', 'Low'
    MEDIUM = 'MEDIUM', 'Medium'
    HIGH = 'HIGH', 'High'
    CRITICAL = 'CRITICAL', 'Critical / Emergency'


class ComplaintSeverity(models.TextChoices):
    MINOR = 'MINOR', 'Minor Inconvenience'
    MODERATE = 'MODERATE', 'Moderate Civic Issue'
    SEVERE = 'SEVERE', 'Severe Disruption'
    HAZARDOUS = 'HAZARDOUS', 'Public Hazard / Threat'


class ComplaintStatus(models.TextChoices):
    SUBMITTED = 'SUBMITTED', 'Submitted'
    UNDER_REVIEW = 'UNDER_REVIEW', 'Under Review'
    VERIFIED = 'VERIFIED', 'Verified'
    ASSIGNED = 'ASSIGNED', 'Assigned'
    INVESTIGATION = 'INVESTIGATION', 'Investigation'
    WORK_IN_PROGRESS = 'WORK_IN_PROGRESS', 'Work In Progress'
    RESOLVED = 'RESOLVED', 'Resolved'
    CITIZEN_VERIFICATION = 'CITIZEN_VERIFICATION', 'Citizen Verification'
    CLOSED = 'CLOSED', 'Closed'
    REJECTED = 'REJECTED', 'Rejected'
    DUPLICATE = 'DUPLICATE', 'Duplicate'
    MORE_INFO_REQUIRED = 'MORE_INFO_REQUIRED', 'More Information Required'
    ON_HOLD = 'ON_HOLD', 'On Hold'
    ESCALATED = 'ESCALATED', 'Escalated'
    REOPENED = 'REOPENED', 'Reopened'


class Category(TimeStampedModel):
    """Civic complaint category (e.g. Water Supply, Road Damage, Street Light)."""
    name = models.CharField(max_length=150, unique=True)
    code = models.CharField(max_length=50, unique=True, db_index=True)
    default_department = models.ForeignKey(
        'departments.Department',
        on_delete=models.CASCADE,
        related_name='categories',
        help_text="Target department automatically responsible for this category."
    )
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, default='fa-exclamation-circle', help_text="FontAwesome or Lucide icon name")
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        verbose_name = 'Category'
        verbose_name_plural = 'Categories'
        ordering = ['name']

    def __str__(self):
        return self.name


class SubCategory(TimeStampedModel):
    """Specific sub-issue under a primary civic category."""
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='subcategories')
    name = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    default_priority = models.CharField(max_length=20, choices=ComplaintPriority.choices, default=ComplaintPriority.MEDIUM)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Subcategory'
        verbose_name_plural = 'Subcategories'
        unique_together = ('category', 'name')
        ordering = ['category__name', 'name']

    def __str__(self):
        return f"{self.category.name} -> {self.name}"


class Complaint(TimeStampedModel):
    """
    Central civic grievance docket tracking full lifecycle from
    submission to investigation, resolution, and citizen sign-off.
    """
    complaint_number = models.CharField(
        max_length=50,
        unique=True,
        db_index=True,
        editable=False,
        help_text="Unique docket tracking number (CF-YYYYMMDD-XXXX)"
    )
    citizen = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='filed_complaints',
        help_text="Citizen who registered this issue"
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name='complaints'
    )
    subcategory = models.ForeignKey(
        SubCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='complaints'
    )
    department = models.ForeignKey(
        'departments.Department',
        on_delete=models.PROTECT,
        related_name='complaints',
        help_text="Responsible municipal department"
    )
    ward = models.ForeignKey(
        'wards.Ward',
        on_delete=models.PROTECT,
        related_name='complaints',
        help_text="Municipal ward where issue is located"
    )
    area = models.ForeignKey(
        'wards.Area',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='complaints',
        help_text="Neighborhood locality"
    )
    specific_address = models.TextField(
        help_text="Exact street, house number, or geographic description"
    )
    landmark = models.CharField(
        max_length=255,
        blank=True,
        help_text="Nearby recognizable civic landmark"
    )
    latitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
        help_text="GPS Latitude"
    )
    longitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
        help_text="GPS Longitude"
    )
    title = models.CharField(
        max_length=255,
        help_text="Concise summary of the civic grievance"
    )
    description = models.TextField(
        help_text="Comprehensive details of the problem"
    )
    priority = models.CharField(
        max_length=20,
        choices=ComplaintPriority.choices,
        default=ComplaintPriority.MEDIUM,
        db_index=True
    )
    severity = models.CharField(
        max_length=20,
        choices=ComplaintSeverity.choices,
        default=ComplaintSeverity.MODERATE,
        db_index=True
    )
    status = models.CharField(
        max_length=30,
        choices=ComplaintStatus.choices,
        default=ComplaintStatus.SUBMITTED,
        db_index=True
    )
    assigned_staff = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_complaints',
        help_text="Municipal engineer or inspector currently assigned"
    )
    expected_resolution_date = models.DateTimeField(
        null=True,
        blank=True,
        db_index=True,
        help_text="Target SLA resolution deadline"
    )
    resolved_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Timestamp when work was marked resolved"
    )
    closed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Timestamp when citizen accepted or docket auto-closed"
    )
    resolution_summary = models.TextField(
        blank=True,
        help_text="Technical explanation of actions taken to resolve the grievance"
    )
    rejection_reason = models.TextField(
        blank=True,
        help_text="Administrative justification if rejected or marked duplicate"
    )
    is_escalated = models.BooleanField(
        default=False,
        db_index=True,
        help_text="Whether this complaint has been escalated due to breach or severity"
    )
    escalation_level = models.PositiveIntegerField(
        default=0,
        help_text="Current escalation tier (0: Normal, 1: Officer, 2: Manager, 3: Commissioner)"
    )
    reopen_count = models.PositiveIntegerField(
        default=0,
        help_text="Number of times reopened by citizen"
    )

    class Meta:
        verbose_name = 'Complaint'
        verbose_name_plural = 'Complaints'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'priority']),
            models.Index(fields=['department', 'status']),
            models.Index(fields=['ward', 'status']),
        ]

    def save(self, *args, **kwargs):
        if not self.complaint_number:
            self.complaint_number = generate_complaint_reference()
            # Ensure unique in rare collision
            while Complaint.objects.filter(complaint_number=self.complaint_number).exists():
                self.complaint_number = generate_complaint_reference()

        # Automatically assign department if not explicitly set
        if not self.department_id and self.category_id:
            self.department = self.category.default_department

        super().save(*args, **kwargs)

    def __str__(self):
        return f"[{self.complaint_number}] {self.title} - {self.get_status_display()}"

    def get_absolute_url(self):
        return reverse('complaints:detail', kwargs={'complaint_number': self.complaint_number})

    @property
    def is_closed(self):
        return self.status in [ComplaintStatus.CLOSED, ComplaintStatus.REJECTED, ComplaintStatus.DUPLICATE]

    @property
    def is_active(self):
        return not self.is_closed

    @property
    def is_overdue(self):
        if self.expected_resolution_date and not self.resolved_at:
            return timezone.now() > self.expected_resolution_date
        return False
