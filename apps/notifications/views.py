"""Notification center views."""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from apps.notifications.models import Notification


@login_required
def notification_list_view(request):
    """View all notifications for current user."""
    notifications = request.user.notifications.select_related('related_complaint').all()
    return render(request, 'management/notification_list.html', {
        'notifications': notifications,
        'title': 'My Notifications & Civic Alerts'
    })


@login_required
def mark_read_view(request, pk):
    """Mark a single notification as read."""
    notif = get_object_or_404(Notification, pk=pk, recipient=request.user)
    notif.mark_as_read()
    if notif.related_complaint:
        return redirect(notif.related_complaint.get_absolute_url())
    return redirect('notifications:list')


@login_required
def mark_all_read_view(request):
    """Mark all unread notifications as read."""
    request.user.notifications.filter(is_read=False).update(is_read=True)
    messages.success(request, "All notifications marked as read.")
    return redirect('notifications:list')
