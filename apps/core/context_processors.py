"""Context processors for CivicFlow application."""

from django.conf import settings
from django.utils import timezone


def municipal_settings(request):
    """Expose municipal settings and system configuration across all templates."""
    return {
        'MUNICIPALITY_NAME': getattr(settings, 'MUNICIPALITY_NAME', 'Metropolis Municipal Corporation'),
        'MUNICIPALITY_SHORT': getattr(settings, 'MUNICIPALITY_SHORT', 'MMC'),
        'MUNICIPALITY_PORTAL_TITLE': getattr(settings, 'MUNICIPALITY_PORTAL_TITLE', 'CivicFlow Civic Administration'),
        'MUNICIPALITY_HOTLINE': getattr(settings, 'MUNICIPALITY_HOTLINE', '1800-CIVIC-MMC'),
        'MUNICIPALITY_EMAIL': getattr(settings, 'MUNICIPALITY_EMAIL', 'grievances@civicflow.gov'),
        'CURRENT_YEAR': timezone.now().year,
        'SYSTEM_VERSION': '1.0.0-PROD',
    }
