"""Communications view logic."""

from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from apps.accounts.models import UserRole
from apps.complaints.models import Complaint
from apps.communications.models import ComplaintMessage, MessageType
from apps.audit.utils import record_audit_log


@login_required
def post_message_view(request, complaint_number):
    """Post message or internal note to complaint timeline."""
    complaint = get_object_or_404(Complaint, complaint_number=complaint_number)

    is_owner = complaint.citizen_id == request.user.id
    is_staff = request.user.role in [UserRole.STAFF, UserRole.MANAGER, UserRole.ADMIN] or request.user.is_superuser
    if not (is_owner or is_staff):
        raise PermissionDenied("You are not authorized to post messages on this docket.")

    if request.method == 'POST':
        message_text = request.POST.get('message', '').strip()
        is_internal = request.POST.get('is_internal_only') == 'on'

        if not message_text:
            messages.error(request, "Message text cannot be empty.")
            return redirect(complaint.get_absolute_url())

        # Enforce role logic
        if not is_staff:
            is_internal = False
            msg_type = MessageType.CITIZEN_UPDATE
        else:
            if is_internal:
                msg_type = MessageType.INTERNAL_NOTE
            else:
                msg_type = MessageType.STAFF_REPLY

        msg_record = ComplaintMessage.objects.create(
            complaint=complaint,
            sender=request.user,
            message_type=msg_type,
            message=message_text,
            is_internal_only=is_internal
        )

        record_audit_log(
            actor=request.user,
            action='MESSAGE_POSTED',
            target_model='communications.ComplaintMessage',
            target_id=str(msg_record.id),
            details=f"Posted {msg_type} on {complaint.complaint_number}",
            request=request
        )

        # Notify other party
        try:
            from apps.notifications.services import create_notification
            if is_staff and not is_internal:
                # Notify citizen
                create_notification(
                    recipient=complaint.citizen,
                    title="Municipal Update on Your Complaint",
                    message=f"Department officer posted an update on {complaint.complaint_number}: '{message_text[:100]}'",
                    notification_type='MESSAGE',
                    related_complaint=complaint
                )
            elif not is_staff and complaint.assigned_staff:
                # Notify assigned staff
                create_notification(
                    recipient=complaint.assigned_staff,
                    title="Citizen Response Received",
                    message=f"Citizen posted update on {complaint.complaint_number}: '{message_text[:100]}'",
                    notification_type='MESSAGE',
                    related_complaint=complaint
                )
        except Exception:
            pass

        messages.success(request, "Message successfully logged to complaint docket.")

    return redirect(complaint.get_absolute_url())
