"""Notification dispatch services."""

from apps.notifications.models import Notification, NotificationPriority


def create_notification(recipient, title, message, notification_type='SYSTEM', related_complaint=None, priority=NotificationPriority.NORMAL):
    """Deliver an in-app notification to a user."""
    if not recipient:
        return None

    return Notification.objects.create(
        recipient=recipient,
        title=title,
        message=message,
        notification_type=notification_type,
        related_complaint=related_complaint,
        priority=priority
    )


def create_status_notification(complaint, from_status, to_status, actor=None):
    """Generate automatic notification to citizen on state transition."""
    # Notify Citizen
    if complaint.citizen:
        title = f"Docket {complaint.complaint_number} Status Updated"
        message = f"Your civic complaint '{complaint.title}' has transitioned to {to_status.replace('_', ' ').title()}."
        create_notification(
            recipient=complaint.citizen,
            title=title,
            message=message,
            notification_type='STATUS',
            related_complaint=complaint,
            priority=NotificationPriority.NORMAL
        )

    # If assigned to staff, notify staff as well
    if complaint.assigned_staff and actor != complaint.assigned_staff:
        create_notification(
            recipient=complaint.assigned_staff,
            title=f"Complaint Status Update: {complaint.complaint_number}",
            message=f"Docket '{complaint.title}' status shifted to {to_status}.",
            notification_type='STATUS',
            related_complaint=complaint
        )
