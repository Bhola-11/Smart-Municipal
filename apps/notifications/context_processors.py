"""Notification context processor for unread notification badge."""


def notification_badge(request):
    """Exposes unread notifications count and top 5 recent notifications."""
    if not request.user.is_authenticated:
        return {'unread_notifications_count': 0, 'recent_notifications': []}

    unread_qs = request.user.notifications.filter(is_read=False)
    count = unread_qs.count()
    recent = request.user.notifications.all()[:5]

    return {
        'unread_notifications_count': count,
        'recent_notifications': recent,
    }
