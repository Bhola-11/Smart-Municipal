"""Finite-state machine workflow engine for CivicFlow complaints."""

import logging
from django.core.exceptions import ValidationError
from django.utils import timezone
from apps.accounts.models import UserRole
from apps.complaints.models import ComplaintStatus
from apps.workflow.models import WorkflowTransition
from apps.audit.utils import record_audit_log

logger = logging.getLogger('civicflow.workflow')

# Map of legal transitions
ALLOWED_TRANSITIONS = {
    ComplaintStatus.SUBMITTED: [
        ComplaintStatus.UNDER_REVIEW,
        ComplaintStatus.VERIFIED,
        ComplaintStatus.ASSIGNED,
        ComplaintStatus.REJECTED,
        ComplaintStatus.DUPLICATE,
    ],
    ComplaintStatus.UNDER_REVIEW: [
        ComplaintStatus.VERIFIED,
        ComplaintStatus.MORE_INFO_REQUIRED,
        ComplaintStatus.REJECTED,
        ComplaintStatus.DUPLICATE,
    ],
    ComplaintStatus.MORE_INFO_REQUIRED: [
        ComplaintStatus.UNDER_REVIEW,
        ComplaintStatus.INVESTIGATION,
        ComplaintStatus.REJECTED,
    ],
    ComplaintStatus.VERIFIED: [
        ComplaintStatus.ASSIGNED,
        ComplaintStatus.WORK_IN_PROGRESS,
    ],
    ComplaintStatus.ASSIGNED: [
        ComplaintStatus.INVESTIGATION,
        ComplaintStatus.WORK_IN_PROGRESS,
        ComplaintStatus.ASSIGNED,  # Reassignment
    ],
    ComplaintStatus.INVESTIGATION: [
        ComplaintStatus.WORK_IN_PROGRESS,
        ComplaintStatus.MORE_INFO_REQUIRED,
        ComplaintStatus.ON_HOLD,
        ComplaintStatus.RESOLVED,
        ComplaintStatus.ESCALATED,
    ],
    ComplaintStatus.WORK_IN_PROGRESS: [
        ComplaintStatus.RESOLVED,
        ComplaintStatus.ON_HOLD,
        ComplaintStatus.ESCALATED,
        ComplaintStatus.MORE_INFO_REQUIRED,
    ],
    ComplaintStatus.ON_HOLD: [
        ComplaintStatus.WORK_IN_PROGRESS,
        ComplaintStatus.INVESTIGATION,
    ],
    ComplaintStatus.ESCALATED: [
        ComplaintStatus.INVESTIGATION,
        ComplaintStatus.WORK_IN_PROGRESS,
        ComplaintStatus.RESOLVED,
    ],
    ComplaintStatus.RESOLVED: [
        ComplaintStatus.CITIZEN_VERIFICATION,
        ComplaintStatus.CLOSED,
        ComplaintStatus.REOPENED,
    ],
    ComplaintStatus.CITIZEN_VERIFICATION: [
        ComplaintStatus.CLOSED,
        ComplaintStatus.REOPENED,
    ],
    ComplaintStatus.REOPENED: [
        ComplaintStatus.INVESTIGATION,
        ComplaintStatus.WORK_IN_PROGRESS,
        ComplaintStatus.ESCALATED,
    ],
    ComplaintStatus.CLOSED: [
        ComplaintStatus.REOPENED,  # Allowed within dispute grace window
    ],
    ComplaintStatus.REJECTED: [],
    ComplaintStatus.DUPLICATE: [],
}


def can_transition(complaint, to_status, actor):
    """
    Evaluate if an actor holds permissions to transition complaint to target status.
    """
    from_status = complaint.status

    # Check if transition is defined in state machine
    allowed_targets = ALLOWED_TRANSITIONS.get(from_status, [])
    if to_status not in allowed_targets:
        return False, f"Illegal transition from '{from_status}' to '{to_status}'."

    # Superuser has master clearance
    if actor and getattr(actor, 'is_superuser', False):
        return True, "Permitted via Superuser Clearance."

    role = getattr(actor, 'role', None)

    # Citizen constraints:
    if role == UserRole.CITIZEN:
        # Citizen can only act on their own complaint
        if complaint.citizen_id != actor.id:
            return False, "You can only perform actions on your own complaints."

        # Citizen can verify/accept resolution (CLOSED) or reject (REOPENED)
        if from_status in [ComplaintStatus.RESOLVED, ComplaintStatus.CITIZEN_VERIFICATION]:
            if to_status in [ComplaintStatus.CLOSED, ComplaintStatus.REOPENED]:
                return True, "Citizen verification action permitted."

        # Citizen responding to MORE_INFO_REQUIRED
        if from_status == ComplaintStatus.MORE_INFO_REQUIRED and to_status in [ComplaintStatus.UNDER_REVIEW, ComplaintStatus.INVESTIGATION]:
            return True, "Citizen information provision permitted."

        return False, f"Citizens cannot transition complaints from {from_status} to {to_status}."

    # Staff constraints:
    if role == UserRole.STAFF:
        if to_status in [ComplaintStatus.INVESTIGATION, ComplaintStatus.WORK_IN_PROGRESS, ComplaintStatus.ON_HOLD, ComplaintStatus.RESOLVED, ComplaintStatus.MORE_INFO_REQUIRED, ComplaintStatus.ESCALATED]:
            return True, "Staff operation permitted."
        return False, "Staff members cannot perform this administrative state transition."

    # Manager / Admin constraints:
    if role in [UserRole.MANAGER, UserRole.ADMIN]:
        return True, "Manager clearance permitted."

    return False, "Unauthorized role."


def execute_transition(complaint, to_status, actor, notes='', reason='', request=None):
    """
    Execute state transition, validate invariants, update timestamps, and log history.
    """
    is_allowed, error_msg = can_transition(complaint, to_status, actor)
    if not is_allowed:
        raise ValidationError(error_msg)

    old_status = complaint.status
    complaint.status = to_status
    now = timezone.now()

    # Lifecycle timestamp triggers
    if to_status == ComplaintStatus.RESOLVED:
        complaint.resolved_at = now
    elif to_status == ComplaintStatus.CLOSED:
        complaint.closed_at = now
    elif to_status == ComplaintStatus.REOPENED:
        complaint.reopen_count += 1
        complaint.resolved_at = None
        complaint.closed_at = None

    if to_status == ComplaintStatus.ESCALATED:
        complaint.is_escalated = True
        if complaint.escalation_level == 0:
            complaint.escalation_level = 1

    complaint.save()

    # Record historical workflow transition
    transition_record = WorkflowTransition.objects.create(
        complaint=complaint,
        from_status=old_status,
        to_status=to_status,
        actor=actor if (actor and getattr(actor, 'is_authenticated', False)) else None,
        notes=notes,
        reason=reason
    )

    # Record audit log
    record_audit_log(
        actor=actor,
        action='STATUS_TRANSITION',
        target_model='complaints.Complaint',
        target_id=complaint.complaint_number,
        details=f"Status changed from {old_status} to {to_status}. Notes: {notes}",
        request=request
    )

    # Trigger In-App Notification (lazy import to prevent circular dependency)
    try:
        from apps.notifications.services import create_status_notification
        create_status_notification(complaint, old_status, to_status, actor)
    except Exception as exc:
        logger.warning(f"Notification trigger failed: {exc}")

    return transition_record
