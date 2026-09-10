"""Citizen portal views."""

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from apps.accounts.permissions import citizen_required
from apps.citizens.models import CitizenVerification
from apps.audit.utils import record_audit_log


@login_required
@citizen_required
def citizen_verification_view(request):
    """Citizen submits verification documents."""
    verification, _ = CitizenVerification.objects.get_or_create(citizen=request.user)

    if request.method == 'POST':
        doc_type = request.POST.get('document_type')
        doc_num = request.POST.get('document_number')
        doc_file = request.FILES.get('document_file')

        if doc_type and doc_num and doc_file:
            verification.document_type = doc_type
            verification.document_number = doc_num
            verification.document_file = doc_file
            verification.status = 'PENDING'
            verification.save()

            record_audit_log(
                actor=request.user,
                action='CITIZEN_VERIFICATION_SUBMITTED',
                target_model='citizens.CitizenVerification',
                target_id=str(verification.id),
                details=f"Citizen uploaded {doc_type} for verification",
                request=request
            )
            messages.success(request, "Your resident verification documents have been submitted for municipal review.")
            return redirect('citizens:verification')
        else:
            messages.error(request, "Please provide all required verification fields and attachment.")

    return render(request, 'citizens/verification.html', {
        'verification': verification,
        'title': 'Citizen Identity Verification'
    })
