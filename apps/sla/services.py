"""SLA calculation, policy resolution, and deadline services."""

from datetime import timedelta
from django.utils import timezone
from apps.complaints.models import ComplaintPriority
from apps.sla.models import SLAPolicy, SLALog


def find_matching_sla_policy(complaint):
    """
    Hierarchical policy lookup:
    1. Exact match: Department + Category + Priority + Severity
    2. Department + Priority
    3. Category + Priority
    4. Global Priority
    5. Fallback baseline
    """
    policies = SLAPolicy.objects.filter(is_active=True)

    # 1. Department + Category + Priority
    match = policies.filter(
        department=complaint.department,
        category=complaint.category,
        priority=complaint.priority
    ).first()
    if match:
        return match

    # 2. Department + Priority
    match = policies.filter(
        department=complaint.department,
        priority=complaint.priority
    ).first()
    if match:
        return match

    # 3. Category + Priority
    match = policies.filter(
        category=complaint.category,
        priority=complaint.priority
    ).first()
    if match:
        return match

    # 4. Global Priority
    match = policies.filter(
        department__isnull=True,
        category__isnull=True,
        priority=complaint.priority
    ).first()
    if match:
        return match

    # 5. First active policy or None
    return policies.first()


def initialize_complaint_sla(complaint):
    """Initialize SLA record when a complaint is created or reopened."""
    policy = find_matching_sla_policy(complaint)

    # Calculate hours duration
    if policy:
        duration_hours = policy.resolution_time_hours
    else:
        # Default fallbacks based on priority
        fallback_hours = {
            ComplaintPriority.CRITICAL: 12,
            ComplaintPriority.HIGH: 24,
            ComplaintPriority.MEDIUM: 48,
            ComplaintPriority.LOW: 96,
        }
        duration_hours = fallback_hours.get(complaint.priority, 48)

    now = timezone.now()
    deadline = now + timedelta(hours=duration_hours)

    # Update complaint pointer
    complaint.expected_resolution_date = deadline
    complaint.save(update_fields=['expected_resolution_date'])

    sla_record, created = SLALog.objects.get_or_create(
        complaint=complaint,
        defaults={
            'policy': policy,
            'start_time': now,
            'deadline': deadline,
            'status': 'ON_TRACK'
        }
    )
    if not created:
        sla_record.policy = policy
        sla_record.start_time = now
        sla_record.deadline = deadline
        sla_record.status = 'ON_TRACK'
        sla_record.breached_at = None
        sla_record.save()

    return sla_record


def update_sla_status(sla_log):
    """
    Recompute current status of SLA (ON_TRACK, DUE_SOON, BREACHED, MET_WITHIN_SLA, MET_AFTER_SLA).
    """
    complaint = sla_log.complaint
    now = timezone.now()

    # If already resolved
    if complaint.resolved_at:
        hours_taken = (complaint.resolved_at - sla_log.start_time).total_seconds() / 3600
        sla_log.actual_hours_taken = round(hours_taken, 2)
        if complaint.resolved_at <= sla_log.deadline:
            sla_log.status = 'MET_WITHIN_SLA'
        else:
            sla_log.status = 'MET_AFTER_SLA'
        sla_log.save()
        return sla_log.status

    # If past deadline
    if now > sla_log.deadline:
        if sla_log.status != 'BREACHED':
            sla_log.status = 'BREACHED'
            sla_log.breached_at = now
            sla_log.save()
        return 'BREACHED'

    # Check due soon
    threshold_pct = sla_log.policy.due_soon_threshold_percent if sla_log.policy else 75
    if sla_log.percentage_elapsed >= threshold_pct:
        sla_log.status = 'DUE_SOON'
    else:
        sla_log.status = 'ON_TRACK'

    sla_log.save(update_fields=['status'])
    return sla_log.status
