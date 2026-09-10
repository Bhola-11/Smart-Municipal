"""Assignment business logic and workload balancing service."""

from django.db import transaction
from django.utils import timezone
from apps.accounts.models import User, UserRole
from apps.complaints.models import Complaint, ComplaintStatus
from apps.assignments.models import Assignment, AssignmentStatus
from apps.workflow.engine import execute_transition
from apps.audit.utils import record_audit_log


def assign_staff_to_complaint(complaint, staff, assigned_by, reason='', request=None):
    """
    Delegate complaint to municipal staff member, handling reassignments and workflow state.
    """
    with transaction.atomic():
        # Mark previous active assignments as reassigned
        Assignment.objects.filter(
            complaint=complaint,
            status__in=[AssignmentStatus.PENDING, AssignmentStatus.ACCEPTED]
        ).update(status=AssignmentStatus.REASSIGNED)

        # Create new assignment record
        assignment = Assignment.objects.create(
            complaint=complaint,
            staff=staff,
            assigned_by=assigned_by,
            reason=reason,
            status=AssignmentStatus.PENDING
        )

        # Update complaint pointer
        complaint.assigned_staff = staff
        complaint.save(update_fields=['assigned_staff'])

        # Advance workflow to ASSIGNED if previously VERIFIED or SUBMITTED
        if complaint.status in [ComplaintStatus.SUBMITTED, ComplaintStatus.UNDER_REVIEW, ComplaintStatus.VERIFIED]:
            execute_transition(
                complaint=complaint,
                to_status=ComplaintStatus.ASSIGNED,
                actor=assigned_by,
                notes=f"Assigned to {staff.get_full_name() or staff.username}. Notes: {reason}",
                reason="StaffDelegation",
                request=request
            )

        record_audit_log(
            actor=assigned_by,
            action='STAFF_ASSIGNED',
            target_model='assignments.Assignment',
            target_id=str(assignment.id),
            details=f"Assigned complaint {complaint.complaint_number} to {staff.username}",
            request=request
        )

        # Send in-app notification to the assigned staff member
        try:
            from apps.notifications.services import create_notification
            create_notification(
                recipient=staff,
                title="New Work Assignment",
                message=f"You have been assigned complaint {complaint.complaint_number}: '{complaint.title}'.",
                notification_type='ASSIGNMENT',
                related_complaint=complaint
            )
        except Exception:
            pass

        return assignment


def accept_work_assignment(assignment, staff, request=None):
    """Staff accepts assignment and commences investigation."""
    with transaction.atomic():
        assignment.status = AssignmentStatus.ACCEPTED
        assignment.accepted_at = timezone.now()
        assignment.save()

        complaint = assignment.complaint
        if complaint.status == ComplaintStatus.ASSIGNED:
            execute_transition(
                complaint=complaint,
                to_status=ComplaintStatus.INVESTIGATION,
                actor=staff,
                notes="Staff accepted assignment and initiated field investigation.",
                reason="StaffAccepted",
                request=request
            )

        record_audit_log(
            actor=staff,
            action='ASSIGNMENT_ACCEPTED',
            target_model='assignments.Assignment',
            target_id=str(assignment.id),
            details=f"Staff {staff.username} accepted assignment for {complaint.complaint_number}",
            request=request
        )


def reject_work_assignment(assignment, staff, reason, request=None):
    """Staff rejects assignment with justification (returns to manager queue)."""
    with transaction.atomic():
        assignment.status = AssignmentStatus.REJECTED
        assignment.rejection_reason = reason
        assignment.save()

        complaint = assignment.complaint
        complaint.assigned_staff = None
        complaint.save(update_fields=['assigned_staff'])

        # Notify Department Manager
        if complaint.department and complaint.department.head_officer:
            try:
                from apps.notifications.services import create_notification
                create_notification(
                    recipient=complaint.department.head_officer,
                    title="Assignment Declined by Staff",
                    message=f"Staff {staff.get_full_name()} declined assignment on {complaint.complaint_number}. Reason: {reason}",
                    notification_type='ALERT',
                    related_complaint=complaint,
                    priority='HIGH'
                )
            except Exception:
                pass

        record_audit_log(
            actor=staff,
            action='ASSIGNMENT_REJECTED',
            target_model='assignments.Assignment',
            target_id=str(assignment.id),
            details=f"Staff {staff.username} declined assignment for {complaint.complaint_number}. Reason: {reason}",
            request=request
        )


def get_staff_workload_stats(department=None):
    """
    Returns list of staff members with their current active workload count
    to assist managers in balanced delegation.
    """
    qs = User.objects.filter(role=UserRole.STAFF, is_active=True)
    if department:
        qs = qs.filter(department=department)

    workload_list = []
    for staff in qs.select_related('department'):
        active_count = Complaint.objects.filter(
            assigned_staff=staff,
            status__in=[
                ComplaintStatus.ASSIGNED,
                ComplaintStatus.INVESTIGATION,
                ComplaintStatus.WORK_IN_PROGRESS,
                ComplaintStatus.ON_HOLD
            ]
        ).count()
        workload_list.append({
            'staff': staff,
            'active_count': active_count,
            'department': staff.department.name if staff.department else 'General',
        })

    workload_list.sort(key=lambda x: x['active_count'])
    return workload_list
