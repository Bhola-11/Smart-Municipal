"""Feedback submission and CSAT analysis views."""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.db.models import Avg, Count
from apps.accounts.permissions import citizen_required, manager_required
from apps.complaints.models import Complaint, ComplaintStatus
from apps.feedback.models import Feedback, SatisfactionLevel
from apps.workflow.engine import execute_transition
from apps.escalations.services import trigger_escalation
from apps.escalations.models import EscalationReason
from apps.audit.utils import record_audit_log


@login_required
@citizen_required
def submit_feedback_view(request, complaint_number):
    """Citizen accepts or rejects the resolution and leaves ratings."""
    complaint = get_object_or_404(Complaint, complaint_number=complaint_number)

    if complaint.citizen_id != request.user.id:
        raise PermissionDenied("You can only submit feedback on your own complaints.")

    # Only permitted when in RESOLVED or CITIZEN_VERIFICATION
    if complaint.status not in [ComplaintStatus.RESOLVED, ComplaintStatus.CITIZEN_VERIFICATION]:
        messages.warning(request, "Feedback can only be registered once the complaint is marked resolved.")
        return redirect(complaint.get_absolute_url())

    if request.method == 'POST':
        rating = int(request.POST.get('rating', 5))
        satisfaction = request.POST.get('satisfaction', SatisfactionLevel.SATISFIED)
        resolution_accepted = request.POST.get('resolution_accepted') == 'true'
        comments = request.POST.get('comments', '').strip()
        rejection_reason = request.POST.get('rejection_reason', '').strip()

        feedback, _ = Feedback.objects.update_or_create(
            complaint=complaint,
            defaults={
                'citizen': request.user,
                'rating': rating,
                'satisfaction': satisfaction,
                'resolution_accepted': resolution_accepted,
                'comments': comments,
                'rejection_reason': rejection_reason if not resolution_accepted else ''
            }
        )

        record_audit_log(
            actor=request.user,
            action='FEEDBACK_SUBMITTED',
            target_model='feedback.Feedback',
            target_id=str(feedback.id),
            details=f"Feedback submitted: Rating={rating}, Accepted={resolution_accepted}",
            request=request
        )

        if resolution_accepted:
            execute_transition(
                complaint=complaint,
                to_status=ComplaintStatus.CLOSED,
                actor=request.user,
                notes=f"Citizen verified resolution. Rating: {rating} Stars. Feedback: {comments}",
                reason="CitizenAcceptedResolution",
                request=request
            )
            messages.success(request, "Thank you! The complaint has been officially closed based on your satisfaction.")
        else:
            execute_transition(
                complaint=complaint,
                to_status=ComplaintStatus.REOPENED,
                actor=request.user,
                notes=f"Citizen rejected resolution. Reason: {rejection_reason}",
                reason="CitizenRejectedResolution",
                request=request
            )

            # Auto-escalation if multiple re-openings occur
            if complaint.reopen_count >= 2:
                trigger_escalation(
                    complaint=complaint,
                    reason=EscalationReason.CITIZEN_REJECTION,
                    description=f"Complaint reopened {complaint.reopen_count} times by citizen. Rejection note: {rejection_reason}",
                    actor=request.user,
                    request=request
                )
                messages.warning(request, "Your complaint has been reopened and escalated to senior department leadership.")
            else:
                messages.warning(request, "Complaint reopened. Field engineers will re-inspect and rectify the grievance.")

        return redirect(complaint.get_absolute_url())

    return render(request, 'complaints/feedback_form.html', {
        'complaint': complaint,
        'satisfaction_levels': SatisfactionLevel.choices,
        'title': f"Verify Resolution - {complaint.complaint_number}"
    })


@login_required
@manager_required
def feedback_dashboard_view(request):
    """Management view analyzing citizen satisfaction scores."""
    dept = request.user.department if not request.user.is_superuser else None
    feedbacks = Feedback.objects.select_related('complaint', 'citizen', 'complaint__department')
    if dept:
        feedbacks = feedbacks.filter(complaint__department=dept)

    avg_rating = feedbacks.aggregate(avg=Avg('rating'))['avg'] or 0.0
    total_feedbacks = feedbacks.count()
    accepted_count = feedbacks.filter(resolution_accepted=True).count()
    acceptance_rate = round((accepted_count / total_feedbacks * 100), 1) if total_feedbacks > 0 else 100.0

    return render(request, 'management/feedback_analytics.html', {
        'feedbacks': feedbacks.order_by('-created_at')[:50],
        'avg_rating': round(avg_rating, 2),
        'total_feedbacks': total_feedbacks,
        'acceptance_rate': acceptance_rate,
        'title': 'Citizen Satisfaction (CSAT) Overview'
    })
