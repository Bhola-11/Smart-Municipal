"""Wards forms and management views."""

from django import forms
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib import messages
from apps.accounts.permissions import admin_required
from apps.wards.models import Zone, Ward, Area
from apps.audit.utils import record_audit_log


class WardForm(forms.ModelForm):
    class Meta:
        model = Ward
        fields = ('zone', 'ward_number', 'name', 'ward_officer', 'population', 'office_address', 'contact_phone')
        widgets = {
            'zone': forms.Select(attrs={'class': 'form-select'}),
            'ward_number': forms.NumberInput(attrs={'class': 'form-input'}),
            'name': forms.TextInput(attrs={'class': 'form-input'}),
            'ward_officer': forms.Select(attrs={'class': 'form-select'}),
            'population': forms.NumberInput(attrs={'class': 'form-input'}),
            'office_address': forms.TextInput(attrs={'class': 'form-input'}),
            'contact_phone': forms.TextInput(attrs={'class': 'form-input'}),
        }


class AreaForm(forms.ModelForm):
    class Meta:
        model = Area
        fields = ('ward', 'name', 'postal_code', 'landmark', 'latitude', 'longitude')
        widgets = {
            'ward': forms.Select(attrs={'class': 'form-select'}),
            'name': forms.TextInput(attrs={'class': 'form-input'}),
            'postal_code': forms.TextInput(attrs={'class': 'form-input'}),
            'landmark': forms.TextInput(attrs={'class': 'form-input'}),
            'latitude': forms.NumberInput(attrs={'class': 'form-input', 'step': '0.000001'}),
            'longitude': forms.NumberInput(attrs={'class': 'form-input', 'step': '0.000001'}),
        }


def ward_list_view(request):
    """List all wards grouped by zones."""
    wards = Ward.objects.select_related('zone', 'ward_officer').prefetch_related('areas').all()
    zones = Zone.objects.prefetch_related('wards').all()
    return render(request, 'management/ward_list.html', {
        'wards': wards,
        'zones': zones,
        'title': 'Municipal Wards & Zones'
    })


def ward_detail_view(request, pk):
    """Details of a ward and its areas."""
    ward = get_object_or_404(Ward.objects.select_related('zone', 'ward_officer').prefetch_related('areas'), pk=pk)
    return render(request, 'management/ward_detail.html', {
        'ward': ward,
        'title': f"Ward {ward.ward_number}: {ward.name}"
    })


@admin_required
def ward_create_view(request):
    """Create new ward."""
    if request.method == 'POST':
        form = WardForm(request.POST)
        if form.is_valid():
            ward = form.save()
            record_audit_log(
                actor=request.user,
                action='WARD_CREATED',
                target_model='wards.Ward',
                target_id=str(ward.id),
                details=f"Created Ward {ward.ward_number}: {ward.name}",
                request=request
            )
            messages.success(request, f"Ward {ward.ward_number} successfully registered.")
            return redirect('wards:list')
    else:
        form = WardForm()
    return render(request, 'management/ward_form.html', {'form': form, 'title': 'Add Municipal Ward'})


def areas_by_ward_json(request, ward_id):
    """API endpoint to get list of areas for a specific ward (used by dynamic JS dropdowns)."""
    areas = Area.objects.filter(ward_id=ward_id).values('id', 'name', 'postal_code', 'latitude', 'longitude')
    return JsonResponse({'areas': list(areas)})
