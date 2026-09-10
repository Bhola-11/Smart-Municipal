"""Complaint views: creation, dossier detail, lifecycle tracking, and filters."""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.http import JsonResponse
from django.db.models import Q
from apps.accounts.models import UserRole
from apps.complaints.models import Complaint, Category, SubCategory, ComplaintStatus
from apps.complaints.forms import ComplaintSubmissionForm, ComplaintSearchFilterForm, ComplaintResolutionForm
from apps.attachments.models import Attachment, AttachmentStage
from apps.workflow.engine import ALLOWED_TRANSITIONS, can_transition, execute_transition
from apps.sla.services import initialize_complaint_sla, update_sla_status
from apps.audit.utils import record_audit_log


@login_required
def complaint_list_view(request):
    """
    Searchable, filterable complaints registry.
    Role-partitioned: Citizens see their own; Staff/Managers see departmental/assigned.
    """
    user = request.user
    queryset = Complaint.objects.select_related('citizen', 'category', 'department', 'ward', 'assigned_staff', 'sla_record')

    # Role-based filtering
    if user.role == UserRole.CITIZEN:
        queryset = queryset.filter(citizen=user)
    elif user.role == UserRole.STAFF:
        queryset = queryset.filter(Q(assigned_staff=user) | Q(department=user.department))
    elif user.role == UserRole.MANAGER and user.department:
        queryset = queryset.filter(department=user.department)

    filter_form = ComplaintSearchFilterForm(request.GET)
    if filter_form.is_valid():
        q = filter_form.cleaned_data.get('q')
        status = filter_form.cleaned_data.get('status')
        priority = filter_form.cleaned_data.get('priority')
        category = filter_form.cleaned_data.get('category')
        ward = filter_form.cleaned_data.get('ward')
        escalated_only = filter_form.cleaned_data.get('escalated_only')
        sla_status = filter_form.cleaned_data.get('sla_status')

        if q:
            queryset = queryset.filter(
                Q(complaint_number__icontains=q) |
                Q(title__icontains=q) |
                Q(description__icontains=q) |
                Q(specific_address__icontains=q) |
                Q(citizen__first_name__icontains=q) |
                Q(citizen__last_name__icontains=q)
            )
        if status:
            queryset = queryset.filter(status=status)
        if priority:
            queryset = queryset.filter(priority=priority)
        if category:
            queryset = queryset.filter(category=category)
        if ward:
            queryset = queryset.filter(ward=ward)
        if escalated_only:
            queryset = queryset.filter(is_escalated=True)
        if sla_status:
            queryset = queryset.filter(sla_record__status=sla_status)

    paginator = Paginator(queryset, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'complaints/complaint_list.html', {
        'page_obj': page_obj,
        'filter_form': filter_form,
        'title': 'Municipal Complaints Registry'
    })


@login_required
def complaint_create_view(request):
    """Citizen registers a new civic grievance."""
    if request.method == 'POST':
        form = ComplaintSubmissionForm(request.POST, request.FILES)
        if form.is_valid():
            complaint = form.save(commit=False)
            complaint.citizen = request.user
            complaint.save()

            # Process initial evidence photo if supplied
            initial_evidence = form.cleaned_data.get('initial_evidence')
            caption = form.cleaned_data.get('evidence_caption') or 'Initial Evidence Photo'
            if initial_evidence:
                Attachment.objects.create(
                    complaint=complaint,
                    uploaded_by=request.user,
                    file=initial_evidence,
                    caption=caption,
                    stage=AttachmentStage.SUBMISSION,
                    file_size=initial_evidence.size,
                    file_type='IMG'
                )

            # Initialize SLA tracking engine
            initialize_complaint_sla(complaint)

            record_audit_log(
                actor=request.user,
                action='COMPLAINT_SUBMITTED',
                target_model='complaints.Complaint',
                target_id=complaint.complaint_number,
                details=f"Citizen filed complaint {complaint.complaint_number} - {complaint.title}",
                request=request
            )

            # Send Notification to Department Head if available
            try:
                from apps.notifications.services import create_notification
                if complaint.department and complaint.department.head_officer:
                    create_notification(
                        recipient=complaint.department.head_officer,
                        title=f"New Complaint Filed: {complaint.complaint_number}",
                        message=f"A new complaint '{complaint.title}' was submitted for {complaint.department.name}.",
                        notification_type='STATUS',
                        related_complaint=complaint
                    )
            except Exception:
                pass

            messages.success(
                request,
                f"Your complaint has been registered with reference ID {complaint.complaint_number}. "
                f"You will receive live tracking updates."
            )
            return redirect(complaint.get_absolute_url())
        else:
            messages.error(request, "Please review the form to correct the highlighted fields.")
    else:
        form = ComplaintSubmissionForm()

    return render(request, 'complaints/complaint_form.html', {
        'form': form,
        'title': 'Report a Civic Issue'
    })


@login_required
def complaint_detail_view(request, complaint_number):
    """
    Comprehensive Complaint Dossier:
    Shows metadata, status, SLA metrics, evidence gallery, timeline, communication, and action guards.
    """
    complaint = get_object_or_404(
        Complaint.objects.select_related(
            'citizen', 'category', 'subcategory', 'department', 'ward', 'area', 'assigned_staff', 'sla_record'
        ),
        complaint_number=complaint_number
    )

    # Permission check: Citizen cannot view another citizen's complaint
    if request.user.role == UserRole.CITIZEN and complaint.citizen_id != request.user.id:
        raise PermissionDenied("You do not hold clearance to access this citizen docket.")

    # Refresh current SLA status
    if hasattr(complaint, 'sla_record') and complaint.sla_record:
        update_sla_status(complaint.sla_record)

    # Load workflow transitions
    transitions = complaint.workflow_transitions.select_related('actor').all()

    # Load evidence attachments (filter out internal if citizen)
    attachments = complaint.attachments.select_related('uploaded_by').all()
    if request.user.role == UserRole.CITIZEN:
        attachments = attachments.filter(is_internal_only=False)

    # Load messages (filter out internal if citizen)
    messages_qs = complaint.messages.select_related('sender').all()
    if request.user.role == UserRole.CITIZEN:
        messages_qs = messages_qs.filter(is_internal_only=False)

    # Calculate allowed target transitions for current user
    possible_transitions = []
    for candidate_status in ALLOWED_TRANSITIONS.get(complaint.status, []):
        allowed, _ = can_transition(complaint, candidate_status, request.user)
        if allowed:
            possible_transitions.append(candidate_status)

    # Resolution form for staff
    resolution_form = ComplaintResolutionForm()

    # Check if feedback exists
    feedback = getattr(complaint, 'feedback', None)

    return render(request, 'complaints/complaint_detail.html', {
        'complaint': complaint,
        'transitions': transitions,
        'attachments': attachments,
        'timeline_messages': messages_qs,
        'possible_transitions': possible_transitions,
        'resolution_form': resolution_form,
        'feedback': feedback,
        'title': f"Docket {complaint.complaint_number}"
    })


def public_track_view(request):
    """Public lookup allowing citizens to check complaint status via tracking number."""
    complaint = None
    searched = False
    ref_number = request.GET.get('ref', '').strip().upper()

    if ref_number:
        searched = True
        complaint = Complaint.objects.select_related(
            'category', 'department', 'ward', 'sla_record'
        ).filter(complaint_number=ref_number).first()

    return render(request, 'public/track_complaint.html', {
        'complaint': complaint,
        'searched': searched,
        'ref_number': ref_number,
        'title': 'Track Civic Grievance'
    })


def subcategories_by_category_json(request, category_id):
    """API for dynamic cascading category dropdown."""
    subcategories = SubCategory.objects.filter(category_id=category_id, is_active=True).values('id', 'name', 'default_priority')
    return JsonResponse({'subcategories': list(subcategories)})
