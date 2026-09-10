"""Escalation workflow services."""

import logging
from django.db import transaction
from django.utils import timezone
from apps.accounts.models import User, UserRole
from apps.complaints.models import Complaint, ComplaintStatus
from apps.escalations.models import Escalation, EscalationReason
from apps.workflow.engine import execute_transition
from apps.audit.utils import record_audit_log

logger = logging.getLogger('civicflow.escalation')


def trigger_escalation(complaint, reason, description, actor=None, target_user=None, request=None):
    """
    Formally elevate a complaint to the next management escalation tier.
    """
    with transaction.atomic():
        current_level = complaint.escalation_level
        new_level = current_level + 1 if current_level < 3 else 3

        # Locate appropriate target officer if not explicitly provided
        if not target_user:
            if new_level == 1:
                # Ward Officer or Manager
                target_user = complaint.department.head_officer if complaint.department else None
            elif new_level >= 2:
                # Zonal / Central Municipal Administrator
                target_user = User.objects.filter(role=UserRole.ADMIN, is_active=True).first()

        escalation = Escalation.objects.create(
            complaint=complaint,
            level=new_level,
            reason=reason,
            description=description,
            previous_owner=complaint.assigned_staff,
            escalated_to=target_user
        )

        complaint.is_escalated = True
        complaint.escalation_level = new_level
        complaint.save(update_fields=['is_escalated', 'escalation_level'])

        # Advance workflow status to ESCALATED if not closed/resolved
        if complaint.status not in [ComplaintStatus.CLOSED, ComplaintStatus.REJECTED]:
            try:
                execute_transition(
                    complaint=complaint,
                    to_status=ComplaintStatus.ESCALATED,
                    actor=actor,
                    notes=f"Escalated to Tier {new_level}: {description}",
                    reason="EscalationTriggered",
                    request=request
                )
            except Exception as exc:
                logger.warning(f"Workflow transition to ESCALATED had notice: {exc}")

        record_audit_log(
            actor=actor,
            action='COMPLAINT_ESCALATED',
            target_model='escalations.Escalation',
            target_id=str(escalation.id),
            details=f"Complaint {complaint.complaint_number} escalated to Level {new_level}. Reason: {reason}",
            request=request
        )

        # Notify assigned target officer
        if target_user:
            try:
                from apps.notifications.services import create_notification
                create_notification(
                    recipient=target_user,
                    title=f"🚨 Level {new_level} Escalation Alert",
                    message=f"Docket {complaint.complaint_number} requires executive review. Reason: {reason}",
                    notification_type='ESCALATION',
                    related_complaint=complaint,
                    priority='HIGH'
                )
            except Exception:
                pass

        return escalation
