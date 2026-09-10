"""Role-tailored dashboards and public transparency portal views."""

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from apps.accounts.models import User, UserRole
from apps.accounts.permissions import citizen_required, staff_required, manager_required, admin_required
from apps.complaints.models import Complaint, ComplaintStatus, Category
from apps.departments.models import Department
from apps.wards.models import Ward
from apps.assignments.models import Assignment, AssignmentStatus
from apps.escalations.models import Escalation
from apps.analytics.services import get_city_wide_metrics, get_department_performance, get_category_breakdown, get_ward_distribution


def index_view(request):
    """Routing hub: sends authenticated users to their specific dashboard, or public landing."""
    if not request.user.is_authenticated:
        return public_transparency_view(request)

    role = request.user.role
    if role == UserRole.CITIZEN:
        return redirect('dashboard:citizen')
    elif role == UserRole.STAFF:
        return redirect('dashboard:staff')
    elif role == UserRole.MANAGER:
        return redirect('dashboard:manager')
    elif role == UserRole.ADMIN:
        return redirect('dashboard:admin')

    return redirect('dashboard:citizen')


@login_required
@citizen_required
def citizen_dashboard_view(request):
    """Citizen command center."""
    user = request.user
    complaints = user.filed_complaints.select_related('category', 'ward', 'department', 'sla_record').order_by('-created_at')

    total = complaints.count()
    active = complaints.exclude(status__in=[ComplaintStatus.CLOSED, ComplaintStatus.REJECTED, ComplaintStatus.DUPLICATE]).count()
    resolved = complaints.filter(status=ComplaintStatus.RESOLVED).count()
    closed = complaints.filter(status=ComplaintStatus.CLOSED).count()
    escalated = complaints.filter(is_escalated=True).count()

    recent_complaints = complaints[:6]
    recent_notifications = user.notifications.all()[:5]

    return render(request, 'dashboard/citizen.html', {
        'total': total,
        'active': active,
        'resolved': resolved,
        'closed': closed,
        'escalated': escalated,
        'recent_complaints': recent_complaints,
        'recent_notifications': recent_notifications,
        'title': 'Citizen Civic Dashboard'
    })


@login_required
@staff_required
def staff_dashboard_view(request):
    """Field Officer & Staff work execution workspace."""
    user = request.user
    assigned_complaints = Complaint.objects.select_related(
        'citizen', 'category', 'ward', 'sla_record'
    ).filter(assigned_staff=user).order_by('-created_at')

    total_assigned = assigned_complaints.count()
    in_progress = assigned_complaints.filter(status=ComplaintStatus.WORK_IN_PROGRESS).count()
    investigation = assigned_complaints.filter(status=ComplaintStatus.INVESTIGATION).count()
    overdue = assigned_complaints.filter(
        expected_resolution_date__lt=timezone.now(),
        resolved_at__isnull=True
    ).count()

    pending_assignments = Assignment.objects.select_related('complaint').filter(
        staff=user,
        status=AssignmentStatus.PENDING
    )

    return render(request, 'dashboard/staff.html', {
        'assigned_complaints': assigned_complaints[:15],
        'pending_assignments': pending_assignments,
        'total_assigned': total_assigned,
        'in_progress': in_progress,
        'investigation': investigation,
        'overdue': overdue,
        'title': 'Field Officer Operations Workspace'
    })


@login_required
@manager_required
def manager_dashboard_view(request):
    """Department Head & Manager operational console."""
    user = request.user
    dept = user.department if not user.is_superuser else None

    qs = Complaint.objects.select_related('citizen', 'category', 'ward', 'assigned_staff', 'sla_record')
    if dept:
        qs = qs.filter(department=dept)

    total = qs.count()
    open_count = qs.exclude(status__in=[ComplaintStatus.CLOSED, ComplaintStatus.REJECTED, ComplaintStatus.DUPLICATE]).count()
    resolved_count = qs.filter(status__in=[ComplaintStatus.RESOLVED, ComplaintStatus.CLOSED]).count()
    escalated_count = qs.filter(is_escalated=True).count()
    overdue_count = qs.filter(expected_resolution_date__lt=timezone.now(), resolved_at__isnull=True).count()

    resolution_rate = round((resolved_count / total * 100), 1) if total > 0 else 0.0

    unassigned_complaints = qs.filter(assigned_staff__isnull=True).exclude(status__in=[ComplaintStatus.CLOSED, ComplaintStatus.REJECTED])[:8]
    escalated_complaints = qs.filter(is_escalated=True).order_by('-escalation_level')[:8]

    return render(request, 'dashboard/manager.html', {
        'department': dept,
        'total': total,
        'open_count': open_count,
        'resolved_count': resolved_count,
        'escalated_count': escalated_count,
        'overdue_count': overdue_count,
        'resolution_rate': resolution_rate,
        'unassigned_complaints': unassigned_complaints,
        'escalated_complaints': escalated_complaints,
        'title': f"{dept.name if dept else 'Municipal'} Management Center"
    })


@login_required
@admin_required
def admin_dashboard_view(request):
    """System Administrator portal."""
    metrics = get_city_wide_metrics()
    total_users = User.objects.count()
    total_citizens = User.objects.filter(role=UserRole.CITIZEN).count()
    total_staff = User.objects.exclude(role=UserRole.CITIZEN).count()
    total_departments = Department.objects.count()
    total_wards = Ward.objects.count()
    recent_audit_logs = request.user.audit_records.model.objects.select_related('actor').all()[:10]

    return render(request, 'dashboard/admin.html', {
        'metrics': metrics,
        'total_users': total_users,
        'total_citizens': total_citizens,
        'total_staff': total_staff,
        'total_departments': total_departments,
        'total_wards': total_wards,
        'recent_audit_logs': recent_audit_logs,
        'title': 'Municipal System Administration'
    })


def public_transparency_view(request):
    """
    Public-facing transparency portal without PII.
    Displays municipal grievance redressal indices, category stats, and ward resolution metrics.
    """
    metrics = get_city_wide_metrics()
    dept_performance = get_department_performance()
    category_breakdown = get_category_breakdown()
    ward_distribution = get_ward_distribution()

    return render(request, 'public/transparency.html', {
        'metrics': metrics,
        'dept_performance': dept_performance,
        'category_breakdown': category_breakdown,
        'ward_distribution': ward_distribution,
        'title': 'Civic Transparency Portal'
    })
