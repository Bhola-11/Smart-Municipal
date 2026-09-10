"""Authentication and user management forms."""

from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, PasswordChangeForm
from apps.accounts.models import UserRole

User = get_user_model()


class CitizenRegistrationForm(UserCreationForm):
    """Registration form tailored for citizens."""
    first_name = forms.CharField(max_length=30, required=True, widget=forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'First Name'}))
    last_name = forms.CharField(max_length=30, required=True, widget=forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Last Name'}))
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={'class': 'form-input', 'placeholder': 'Email Address'}))
    phone_number = forms.CharField(max_length=20, required=True, widget=forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Mobile Number (e.g. +1 555-0199)'}))
    address = forms.CharField(required=False, widget=forms.Textarea(attrs={'class': 'form-input', 'rows': 2, 'placeholder': 'Residential Address'}))

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'phone_number', 'ward', 'address')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({'class': 'form-input', 'placeholder': 'Username / Citizen ID'})
        if 'ward' in self.fields:
            self.fields['ward'].widget.attrs.update({'class': 'form-select'})

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = UserRole.CITIZEN
        if commit:
            user.save()
        return user


class CustomLoginForm(AuthenticationForm):
    """Styled login form with role clarity."""
    username = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Username, Citizen ID, or Staff ID'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-input', 'placeholder': 'Password'}))


class UserProfileForm(forms.ModelForm):
    """User profile editing form."""
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email', 'phone_number', 'alt_phone', 'address', 'ward', 'profile_image')
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-input'}),
            'last_name': forms.TextInput(attrs={'class': 'form-input'}),
            'email': forms.EmailInput(attrs={'class': 'form-input'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-input'}),
            'alt_phone': forms.TextInput(attrs={'class': 'form-input'}),
            'address': forms.Textarea(attrs={'class': 'form-input', 'rows': 3}),
            'ward': forms.Select(attrs={'class': 'form-select'}),
            'profile_image': forms.FileInput(attrs={'class': 'form-file'}),
        }


class StaffCreationForm(UserCreationForm):
    """Administrative form to onboard municipal staff and managers."""
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'phone_number', 'role', 'department', 'designation', 'employee_id', 'ward')
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-input'}),
            'first_name': forms.TextInput(attrs={'class': 'form-input'}),
            'last_name': forms.TextInput(attrs={'class': 'form-input'}),
            'email': forms.EmailInput(attrs={'class': 'form-input'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-input'}),
            'role': forms.Select(attrs={'class': 'form-select'}),
            'department': forms.Select(attrs={'class': 'form-select'}),
            'designation': forms.TextInput(attrs={'class': 'form-input'}),
            'employee_id': forms.TextInput(attrs={'class': 'form-input'}),
            'ward': forms.Select(attrs={'class': 'form-select'}),
        }
