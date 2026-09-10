"""Escalation management views."""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from apps.accounts.permissions import manager_required
from apps.complaints.models import Complaint
from apps.escalations.models import Escalation, EscalationReason
from apps.escalations.services import trigger_escalation


@login_required
@manager_required
def escalation_list_view(request):
    """View active municipal escalations."""
    escalations = Escalation.objects.select_related(
        'complaint', 'previous_owner', 'escalated_to', 'complaint__department', 'complaint__ward'
    ).filter(is_resolved=False).order_by('-level', '-created_at')

    return render(request, 'management/escalations_list.html', {
        'escalations': escalations,
        'title': 'Active Municipal Escalations'
    })


@login_required
def manual_escalate_view(request, complaint_number):
    """Staff or manager manually escalates a complaint."""
    complaint = get_object_or_404(Complaint, complaint_number=complaint_number)

    if request.method == 'POST':
        reason = request.POST.get('reason')
        description = request.POST.get('description', '').strip()

        if not reason or not description:
            messages.error(request, "Reason and description are mandatory for escalation.")
            return redirect(complaint.get_absolute_url())

        trigger_escalation(
            complaint=complaint,
            reason=reason,
            description=description,
            actor=request.user,
            request=request
        )
        messages.warning(request, f"Docket {complaint.complaint_number} has been escalated to higher management.")
        return redirect(complaint.get_absolute_url())

    return render(request, 'complaints/escalate_modal.html', {
        'complaint': complaint,
        'reasons': EscalationReason.choices
    })


@login_required
@manager_required
def resolve_escalation_view(request, pk):
    """Manager marks escalation addressed and resolved."""
    escalation = get_object_or_404(Escalation, pk=pk)
    if request.method == 'POST':
        notes = request.POST.get('resolution_notes', '').strip()
        escalation.mark_resolved(notes=notes)
        messages.success(request, f"Escalation on {escalation.complaint.complaint_number} marked resolved.")
    return redirect('escalations:list')
