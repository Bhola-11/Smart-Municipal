"""Attachment upload, validation, and controlled file serving."""

import os
from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.http import FileResponse, Http404
from django.conf import settings
from apps.accounts.models import UserRole
from apps.complaints.models import Complaint
from apps.attachments.models import Attachment, AttachmentStage
from apps.audit.utils import record_audit_log


@login_required
def upload_attachment_view(request, complaint_number):
    """Handle evidence uploads for citizens and municipal staff."""
    complaint = get_object_or_404(Complaint, complaint_number=complaint_number)

    # Authorization verification
    is_owner = complaint.citizen_id == request.user.id
    is_staff = request.user.role in [UserRole.STAFF, UserRole.MANAGER, UserRole.ADMIN] or request.user.is_superuser
    if not (is_owner or is_staff):
        raise PermissionDenied("Unauthorized to upload files to this complaint docket.")

    if request.method == 'POST':
        uploaded_file = request.FILES.get('file')
        caption = request.POST.get('caption', '').strip()
        stage = request.POST.get('stage', AttachmentStage.SUBMISSION)
        is_internal = request.POST.get('is_internal_only') == 'on'

        # Only staff can designate files as internal or advanced stages
        if not is_staff:
            is_internal = False
            stage = AttachmentStage.SUBMISSION

        if not uploaded_file:
            messages.error(request, "No file was selected for upload.")
            return redirect(complaint.get_absolute_url())

        # Size validation (10 MB limit)
        if uploaded_file.size > settings.MAX_UPLOAD_SIZE:
            messages.error(request, "File size exceeds the 10 MB municipal ceiling limit.")
            return redirect(complaint.get_absolute_url())

        # Extension validation
        ext = os.path.splitext(uploaded_file.name)[1].lower()
        if ext not in settings.ALLOWED_UPLOAD_EXTENSIONS:
            messages.error(request, f"File format {ext} is not permitted. Allowed: {', '.join(settings.ALLOWED_UPLOAD_EXTENSIONS)}")
            return redirect(complaint.get_absolute_url())

        attachment = Attachment.objects.create(
            complaint=complaint,
            uploaded_by=request.user,
            file=uploaded_file,
            caption=caption,
            stage=stage,
            file_size=uploaded_file.size,
            file_type=ext.replace('.', '').upper(),
            is_internal_only=is_internal
        )

        record_audit_log(
            actor=request.user,
            action='ATTACHMENT_UPLOADED',
            target_model='attachments.Attachment',
            target_id=str(attachment.id),
            details=f"Uploaded {uploaded_file.name} ({attachment.get_stage_display()}) on {complaint.complaint_number}",
            request=request
        )
        messages.success(request, f"Evidence file '{uploaded_file.name}' successfully attached.")

    return redirect(complaint.get_absolute_url())


@login_required
def download_attachment_view(request, pk):
    """Secure attachment access verification."""
    attachment = get_object_or_404(Attachment, pk=pk)
    complaint = attachment.complaint

    # Citizen access check
    if request.user.role == UserRole.CITIZEN:
        if complaint.citizen_id != request.user.id or attachment.is_internal_only:
            raise PermissionDenied("You do not hold permissions to view this internal or restricted file.")

    if not attachment.file:
        raise Http404("Requested file does not exist on storage.")

    return FileResponse(attachment.file.open(), as_attachment=False)
