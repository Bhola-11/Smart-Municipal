"""Department management forms and views."""

from django import forms
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from apps.accounts.permissions import manager_required, admin_required
from apps.departments.models import Department
from apps.audit.utils import record_audit_log


class DepartmentForm(forms.ModelForm):
    class Meta:
        model = Department
        fields = ('name', 'code', 'description', 'head_officer', 'email', 'phone', 'office_location', 'default_sla_hours', 'is_active')
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-input'}),
            'code': forms.TextInput(attrs={'class': 'form-input'}),
            'description': forms.Textarea(attrs={'class': 'form-input', 'rows': 3}),
            'head_officer': forms.Select(attrs={'class': 'form-select'}),
            'email': forms.EmailInput(attrs={'class': 'form-input'}),
            'phone': forms.TextInput(attrs={'class': 'form-input'}),
            'office_location': forms.TextInput(attrs={'class': 'form-input'}),
            'default_sla_hours': forms.NumberInput(attrs={'class': 'form-input'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
        }


def department_list_view(request):
    """List all departments."""
    departments = Department.objects.prefetch_related('staff_members', 'complaints').all()
    return render(request, 'management/department_list.html', {
        'departments': departments,
        'title': 'Municipal Departments Directory'
    })


def department_detail_view(request, pk):
    """Detailed view of a department with its staff and recent issues."""
    dept = get_object_or_404(Department.objects.prefetch_related('staff_members'), pk=pk)
    recent_complaints = dept.complaints.select_related('citizen', 'ward').order_by('-created_at')[:10]
    return render(request, 'management/department_detail.html', {
        'department': dept,
        'recent_complaints': recent_complaints,
        'title': f"{dept.name} Overview"
    })


@admin_required
def department_create_view(request):
    """Create a new municipal department."""
    if request.method == 'POST':
        form = DepartmentForm(request.POST)
        if form.is_valid():
            dept = form.save()
            record_audit_log(
                actor=request.user,
                action='DEPARTMENT_CREATED',
                target_model='departments.Department',
                target_id=str(dept.id),
                details=f"Created department {dept.name} ({dept.code})",
                request=request
            )
            messages.success(request, f"Department '{dept.name}' created.")
            return redirect('departments:list')
    else:
        form = DepartmentForm()
    return render(request, 'management/department_form.html', {'form': form, 'title': 'Add New Department'})


@admin_required
def department_edit_view(request, pk):
    """Update department configuration."""
    dept = get_object_or_404(Department, pk=pk)
    if request.method == 'POST':
        form = DepartmentForm(request.POST, instance=dept)
        if form.is_valid():
            form.save()
            record_audit_log(
                actor=request.user,
                action='DEPARTMENT_UPDATED',
                target_model='departments.Department',
                target_id=str(dept.id),
                details=f"Updated department {dept.name}",
                request=request
            )
            messages.success(request, f"Department '{dept.name}' updated.")
            return redirect('departments:detail', pk=dept.pk)
    else:
        form = DepartmentForm(instance=dept)
    return render(request, 'management/department_form.html', {'form': form, 'title': f"Edit {dept.name}"})
