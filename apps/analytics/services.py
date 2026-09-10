"""Analytics aggregation engine."""

from datetime import timedelta
from django.utils import timezone
from django.db.models import Count, Avg, F, Q
from apps.complaints.models import Complaint, ComplaintStatus, Category
from apps.departments.models import Department
from apps.wards.models import Ward
from apps.sla.models import SLALog


def get_city_wide_metrics(date_from=None, date_to=None):
    """Calculates city-wide executive civic KPIs."""
    qs = Complaint.objects.all()
    if date_from:
        qs = qs.filter(created_at__gte=date_from)
    if date_to:
        qs = qs.filter(created_at__lte=date_to)

    total = qs.count()
    if total == 0:
        return {
            'total': 0, 'open': 0, 'in_progress': 0, 'resolved': 0,
            'closed': 0, 'escalated': 0, 'resolution_rate': 0.0,
            'sla_compliance_rate': 100.0, 'avg_resolution_hours': 0.0
        }

    resolved_or_closed = qs.filter(status__in=[ComplaintStatus.RESOLVED, ComplaintStatus.CLOSED]).count()
    open_count = qs.filter(status__in=[ComplaintStatus.SUBMITTED, ComplaintStatus.UNDER_REVIEW, ComplaintStatus.VERIFIED, ComplaintStatus.ASSIGNED]).count()
    in_progress = qs.filter(status__in=[ComplaintStatus.INVESTIGATION, ComplaintStatus.WORK_IN_PROGRESS, ComplaintStatus.ON_HOLD]).count()
    escalated_count = qs.filter(is_escalated=True).count()
    resolution_rate = round((resolved_or_closed / total) * 100, 1)

    # SLA Compliance
    sla_records = SLALog.objects.filter(complaint__in=qs)
    total_sla = sla_records.count()
    breached_sla = sla_records.filter(status__in=['BREACHED', 'MET_AFTER_SLA']).count()
    sla_compliance = round(((total_sla - breached_sla) / total_sla * 100), 1) if total_sla > 0 else 100.0

    # Average Resolution Hours
    avg_hours = sla_records.filter(actual_hours_taken__isnull=False).aggregate(avg=Avg('actual_hours_taken'))['avg'] or 0.0

    return {
        'total': total,
        'open': open_count,
        'in_progress': in_progress,
        'resolved': qs.filter(status=ComplaintStatus.RESOLVED).count(),
        'closed': qs.filter(status=ComplaintStatus.CLOSED).count(),
        'escalated': escalated_count,
        'resolution_rate': resolution_rate,
        'sla_compliance_rate': sla_compliance,
        'avg_resolution_hours': round(avg_hours, 1)
    }


def get_department_performance():
    """Rank departments by volume, resolution velocity, and SLA adherence."""
    results = []
    for dept in Department.objects.filter(is_active=True):
        dept_complaints = dept.complaints.all()
        total = dept_complaints.count()
        if total == 0:
            continue
        resolved = dept_complaints.filter(status__in=[ComplaintStatus.RESOLVED, ComplaintStatus.CLOSED]).count()
        overdue = dept_complaints.filter(
            expected_resolution_date__lt=timezone.now(),
            resolved_at__isnull=True
        ).count()
        escalated = dept_complaints.filter(is_escalated=True).count()
        res_rate = round((resolved / total) * 100, 1)

        results.append({
            'department': dept,
            'total': total,
            'resolved': resolved,
            'overdue': overdue,
            'escalated': escalated,
            'resolution_rate': res_rate
        })
    results.sort(key=lambda x: x['resolution_rate'], reverse=True)
    return results


def get_category_breakdown():
    """Category distribution statistics."""
    return Category.objects.filter(is_active=True).annotate(
        count=Count('complaints')
    ).filter(count__gt=0).order_by('-count')


def get_ward_distribution():
    """Ward complaint density."""
    return Ward.objects.annotate(
        count=Count('complaints')
    ).order_by('-count')[:15]
