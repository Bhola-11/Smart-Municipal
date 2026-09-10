"""Complaint submission and filter forms."""

from django import forms
from apps.complaints.models import Complaint, Category, SubCategory, ComplaintPriority, ComplaintSeverity, ComplaintStatus
from apps.wards.models import Ward, Area


class ComplaintSubmissionForm(forms.ModelForm):
    """Citizen complaint registration form."""
    initial_evidence = forms.FileField(
        required=False,
        widget=forms.FileInput(attrs={'class': 'form-file', 'accept': 'image/*,.pdf,.doc,.docx'}),
        help_text="Optional photograph or document showing the civic issue."
    )
    evidence_caption = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Photo description (e.g. Deep pothole near crossroads)'})
    )

    class Meta:
        model = Complaint
        fields = (
            'title', 'category', 'subcategory', 'priority', 'severity',
            'ward', 'area', 'specific_address', 'landmark', 'description'
        )
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Brief summary (e.g., Overflowing drain on 4th Cross Road)'}),
            'category': forms.Select(attrs={'class': 'form-select', 'id': 'id_category'}),
            'subcategory': forms.Select(attrs={'class': 'form-select', 'id': 'id_subcategory'}),
            'priority': forms.Select(attrs={'class': 'form-select'}),
            'severity': forms.Select(attrs={'class': 'form-select'}),
            'ward': forms.Select(attrs={'class': 'form-select', 'id': 'id_ward'}),
            'area': forms.Select(attrs={'class': 'form-select', 'id': 'id_area'}),
            'specific_address': forms.Textarea(attrs={'class': 'form-input', 'rows': 3, 'placeholder': 'Door number, street name, locality details'}),
            'landmark': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Nearest recognizable building, temple, school, or park'}),
            'description': forms.Textarea(attrs={'class': 'form-input', 'rows': 5, 'placeholder': 'Describe the civic problem clearly, including duration and impact on residents...'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['subcategory'].queryset = SubCategory.objects.none()
        self.fields['area'].queryset = Area.objects.none()

        if 'category' in self.data:
            try:
                category_id = int(self.data.get('category'))
                self.fields['subcategory'].queryset = SubCategory.objects.filter(category_id=category_id)
            except (ValueError, TypeError):
                pass
        elif self.instance.pk and self.instance.category:
            self.fields['subcategory'].queryset = self.instance.category.subcategories.all()

        if 'ward' in self.data:
            try:
                ward_id = int(self.data.get('ward'))
                self.fields['area'].queryset = Area.objects.filter(ward_id=ward_id)
            except (ValueError, TypeError):
                pass
        elif self.instance.pk and self.instance.ward:
            self.fields['area'].queryset = self.instance.ward.areas.all()


class ComplaintResolutionForm(forms.Form):
    """Staff form to record work completion."""
    resolution_summary = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-input', 'rows': 4, 'placeholder': 'Detailed engineering/field explanation of how the problem was resolved...'}),
        required=True
    )
    completion_photo = forms.FileField(
        widget=forms.FileInput(attrs={'class': 'form-file', 'accept': 'image/*,.pdf'}),
        required=False,
        help_text="Upload post-repair photograph proving civic work completion."
    )


class ComplaintSearchFilterForm(forms.Form):
    """Multi-parameter search and filtration form for complaint lists."""
    q = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Search docket #, title, citizen, address...'}))
    status = forms.ChoiceField(required=False, choices=[('', 'All Statuses')] + list(ComplaintStatus.choices), widget=forms.Select(attrs={'class': 'form-select'}))
    priority = forms.ChoiceField(required=False, choices=[('', 'All Priorities')] + list(ComplaintPriority.choices), widget=forms.Select(attrs={'class': 'form-select'}))
    category = forms.ModelChoiceField(required=False, queryset=Category.objects.filter(is_active=True), empty_label="All Categories", widget=forms.Select(attrs={'class': 'form-select'}))
    ward = forms.ModelChoiceField(required=False, queryset=Ward.objects.all(), empty_label="All Wards", widget=forms.Select(attrs={'class': 'form-select'}))
    escalated_only = forms.BooleanField(required=False, widget=forms.CheckboxInput(attrs={'class': 'form-checkbox'}))
    sla_status = forms.ChoiceField(
        required=False,
        choices=[('', 'All SLA States'), ('ON_TRACK', 'On Track'), ('DUE_SOON', 'Due Soon'), ('BREACHED', 'Breached'), ('MET_WITHIN_SLA', 'Met Within SLA')],
        widget=forms.Select(attrs={'class': 'form-select'})
    )
