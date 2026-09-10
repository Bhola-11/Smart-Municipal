"""Municipal geographic models (Zone -> Ward -> Area)."""

from django.db import models
from django.conf import settings
from apps.core.models import TimeStampedModel


class Zone(TimeStampedModel):
    """Broad geographic division of the municipality (e.g. North Zone, Central Zone)."""
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=20, unique=True)
    description = models.TextField(blank=True)

    class Meta:
        verbose_name = 'Zone'
        verbose_name_plural = 'Zones'
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.code})"


class Ward(TimeStampedModel):
    """Specific administrative ward under a municipal zone."""
    zone = models.ForeignKey(Zone, on_delete=models.CASCADE, related_name='wards')
    ward_number = models.PositiveIntegerField(unique=True, db_index=True)
    name = models.CharField(max_length=150)
    ward_officer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_wards',
        help_text="Designated Ward Councilor or Executive Officer"
    )
    population = models.PositiveIntegerField(default=0, help_text="Estimated resident population")
    office_address = models.CharField(max_length=255, blank=True)
    contact_phone = models.CharField(max_length=30, blank=True)

    class Meta:
        verbose_name = 'Ward'
        verbose_name_plural = 'Wards'
        ordering = ['ward_number']

    def __str__(self):
        return f"Ward {self.ward_number}: {self.name}"

    @property
    def total_areas_count(self):
        return self.areas.count()


class Area(TimeStampedModel):
    """Specific neighborhood, block, or locality within a ward."""
    ward = models.ForeignKey(Ward, on_delete=models.CASCADE, related_name='areas')
    name = models.CharField(max_length=150)
    postal_code = models.CharField(max_length=20, db_index=True)
    landmark = models.CharField(max_length=255, blank=True, help_text="Prominent landmark")
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)

    class Meta:
        verbose_name = 'Area'
        verbose_name_plural = 'Areas'
        unique_together = ('ward', 'name')
        ordering = ['ward__ward_number', 'name']

    def __str__(self):
        return f"{self.name}, {self.ward.name} ({self.postal_code})"
