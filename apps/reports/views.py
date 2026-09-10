"""Reports generation, printable views, and CSV export."""

import csv
from django.shortcuts import render
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from apps.accounts.permissions import manager_required
from apps.complaints.models import Complaint
from apps.analytics.services import get_city_wide_metrics, get_department_performance


@login_required
@manager_required
def report_center_view(request):
    """Central reporting hub."""
    metrics = get_city_wide_metrics()
    dept_performance = get_department_performance()
    return render(request, 'reports/report_center.html', {
        'metrics': metrics,
        'dept_performance': dept_performance,
        'title': 'Municipal Reports & Disclosures'
    })


@login_required
@manager_required
def export_complaints_csv(request):
    """Export complaint registry to CSV format."""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="civicflow_complaints_export.csv"'

    writer = csv.writer(response)
    writer.writerow([
        'Docket Number', 'Title', 'Citizen', 'Category', 'Department',
        'Ward', 'Priority', 'Severity', 'Status', 'SLA Deadline',
        'Resolved At', 'Closed At', 'Escalated', 'Created At'
    ])

    complaints = Complaint.objects.select_related(
        'citizen', 'category', 'department', 'ward'
    ).all().order_by('-created_at')

    for c in complaints:
        writer.writerow([
            c.complaint_number,
            c.title,
            c.citizen.get_full_name() or c.citizen.username,
            c.category.name,
            c.department.name,
            f"Ward {c.ward.ward_number}",
            c.priority,
            c.severity,
            c.status,
            c.expected_resolution_date.strftime('%Y-%m-%d %H:%M') if c.expected_resolution_date else '',
            c.resolved_at.strftime('%Y-%m-%d %H:%M') if c.resolved_at else '',
            c.closed_at.strftime('%Y-%m-%d %H:%M') if c.closed_at else '',
            'Yes' if c.is_escalated else 'No',
            c.created_at.strftime('%Y-%m-%d %H:%M')
        ])

    return response


@login_required
@manager_required
def printable_executive_report(request):
    """Print-ready executive summary for municipal commissioner."""
    metrics = get_city_wide_metrics()
    dept_performance = get_department_performance()
    urgent_complaints = Complaint.objects.filter(is_escalated=True).order_by('-escalation_level', '-created_at')[:20]

    return render(request, 'reports/printable_report.html', {
        'metrics': metrics,
        'dept_performance': dept_performance,
        'urgent_complaints': urgent_complaints,
        'title': 'Executive Grievance Redressal Audit Report'
    })
