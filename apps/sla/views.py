"""SLA policy management views."""

from django import forms
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from apps.accounts.permissions import admin_required
from apps.sla.models import SLAPolicy
from apps.audit.utils import record_audit_log


class SLAPolicyForm(forms.ModelForm):
    class Meta:
        model = SLAPolicy
        fields = ('name', 'department', 'category', 'priority', 'severity', 'response_time_hours', 'resolution_time_hours', 'due_soon_threshold_percent', 'is_active')
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-input'}),
            'department': forms.Select(attrs={'class': 'form-select'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'priority': forms.Select(attrs={'class': 'form-select'}),
            'severity': forms.Select(attrs={'class': 'form-select'}),
            'response_time_hours': forms.NumberInput(attrs={'class': 'form-input'}),
            'resolution_time_hours': forms.NumberInput(attrs={'class': 'form-input'}),
            'due_soon_threshold_percent': forms.NumberInput(attrs={'class': 'form-input'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
        }


@admin_required
def sla_policy_list_view(request):
    """List of all configured SLA policies."""
    policies = SLAPolicy.objects.select_related('department', 'category').all()
    return render(request, 'management/sla_policies.html', {
        'policies': policies,
        'title': 'SLA Policies & Civic Benchmarks'
    })


@admin_required
def sla_policy_create_view(request):
    """Create new SLA policy."""
    if request.method == 'POST':
        form = SLAPolicyForm(request.POST)
        if form.is_valid():
            policy = form.save()
            record_audit_log(
                actor=request.user,
                action='SLA_POLICY_CREATED',
                target_model='sla.SLAPolicy',
                target_id=str(policy.id),
                details=f"Created SLA policy {policy.name}",
                request=request
            )
            messages.success(request, f"SLA Policy '{policy.name}' created.")
            return redirect('sla:list')
    else:
        form = SLAPolicyForm()
    return render(request, 'management/sla_policy_form.html', {'form': form, 'title': 'Create SLA Policy'})
