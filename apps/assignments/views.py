"""Staff assignment views and actions."""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from apps.accounts.models import User, UserRole
from apps.accounts.permissions import manager_required, staff_required
from apps.complaints.models import Complaint
from apps.assignments.models import Assignment, AssignmentStatus
from apps.assignments.services import (
    assign_staff_to_complaint,
    accept_work_assignment,
    reject_work_assignment,
    get_staff_workload_stats
)


@login_required
@manager_required
def assign_complaint_view(request, complaint_number):
    """Manager assigns or reassigns staff to a complaint."""
    complaint = get_object_or_404(Complaint, complaint_number=complaint_number)

    if request.method == 'POST':
        staff_id = request.POST.get('staff_id')
        reason = request.POST.get('reason', '').strip()

        if not staff_id:
            messages.error(request, "Please select an officer to assign.")
            return redirect(complaint.get_absolute_url())

        staff = get_object_or_404(User, pk=staff_id, role=UserRole.STAFF)
        assign_staff_to_complaint(complaint, staff, request.user, reason=reason, request=request)
        messages.success(request, f"Complaint successfully assigned to {staff.get_full_name() or staff.username}.")
        return redirect(complaint.get_absolute_url())

    workload = get_staff_workload_stats(department=complaint.department)
    return render(request, 'complaints/assign_modal.html', {
        'complaint': complaint,
        'workload': workload
    })


@login_required
@staff_required
def accept_assignment_view(request, pk):
    """Staff accepts assignment."""
    assignment = get_object_or_404(Assignment, pk=pk, staff=request.user)
    accept_work_assignment(assignment, request.user, request=request)
    messages.success(request, f"You accepted assignment for {assignment.complaint.complaint_number}.")
    return redirect(assignment.complaint.get_absolute_url())


@login_required
@staff_required
def reject_assignment_view(request, pk):
    """Staff declines assignment with reason."""
    assignment = get_object_or_404(Assignment, pk=pk, staff=request.user)
    if request.method == 'POST':
        reason = request.POST.get('rejection_reason', '').strip()
        if not reason:
            messages.error(request, "You must specify a justification to decline this assignment.")
            return redirect(assignment.complaint.get_absolute_url())
        reject_work_assignment(assignment, request.user, reason, request=request)
        messages.info(request, "Assignment has been declined and referred back to the department manager.")
    return redirect('dashboard:staff')


@login_required
@manager_required
def workload_monitor_view(request):
    """Manager view to monitor workload across all department staff."""
    dept = request.user.department if not request.user.is_superuser else None
    workload = get_staff_workload_stats(department=dept)
    return render(request, 'management/workload.html', {
        'workload': workload,
        'title': 'Field Officer Workload Distribution'
    })
