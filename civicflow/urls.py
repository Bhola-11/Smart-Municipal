"""CivicFlow URL Configuration."""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('apps.dashboard.urls')),
    path('accounts/', include('apps.accounts.urls')),
    path('citizens/', include('apps.citizens.urls')),
    path('departments/', include('apps.departments.urls')),
    path('wards/', include('apps.wards.urls')),
    path('complaints/', include('apps.complaints.urls')),
    path('assignments/', include('apps.assignments.urls')),
    path('workflow/', include('apps.workflow.urls')),
    path('sla/', include('apps.sla.urls')),
    path('escalations/', include('apps.escalations.urls')),
    path('attachments/', include('apps.attachments.urls')),
    path('communications/', include('apps.communications.urls')),
    path('feedback/', include('apps.feedback.urls')),
    path('notifications/', include('apps.notifications.urls')),
    path('audit/', include('apps.audit.urls')),
    path('analytics/', include('apps.analytics.urls')),
    path('reports/', include('apps.reports.urls')),
]

# Custom error handlers
handler400 = 'apps.core.views.error_400'
handler403 = 'apps.core.views.error_403'
handler404 = 'apps.core.views.error_404'
handler500 = 'apps.core.views.error_500'

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
