"""Workflow transition views."""

from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.exceptions import ValidationError
from apps.complaints.models import Complaint
from apps.workflow.engine import execute_transition


@login_required
def transition_status_view(request, complaint_number):
    """Handles POST request to perform a permitted workflow status transition."""
    complaint = get_object_or_404(Complaint, complaint_number=complaint_number)

    if request.method == 'POST':
        target_status = request.POST.get('target_status')
        notes = request.POST.get('notes', '').strip()
        reason = request.POST.get('reason', '').strip()

        if not target_status:
            messages.error(request, "Target status is required.")
            return redirect(complaint.get_absolute_url())

        try:
            execute_transition(
                complaint=complaint,
                to_status=target_status,
                actor=request.user,
                notes=notes,
                reason=reason,
                request=request
            )
            messages.success(request, f"Complaint status successfully updated to {target_status.replace('_', ' ').title()}.")
        except ValidationError as e:
            messages.error(request, str(e.message if hasattr(e, 'message') else e))

    return redirect(complaint.get_absolute_url())
