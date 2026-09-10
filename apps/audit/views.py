"""Audit log viewer for municipal administrators."""

from django.shortcuts import render
from django.core.paginator import Paginator
from apps.accounts.permissions import admin_required
from apps.audit.models import AuditLog


@admin_required
def audit_log_view(request):
    """Filterable audit log ledger view."""
    logs = AuditLog.objects.select_related('actor').all()

    action = request.GET.get('action')
    if action:
        logs = logs.filter(action__icontains=action)

    model_name = request.GET.get('model')
    if model_name:
        logs = logs.filter(target_model__icontains=model_name)

    query = request.GET.get('q')
    if query:
        logs = logs.filter(details__icontains=query)

    paginator = Paginator(logs, 30)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'management/audit_logs.html', {
        'page_obj': page_obj,
        'title': 'Municipal Audit Trail & Security Ledger'
    })
