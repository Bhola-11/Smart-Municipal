from django.contrib import admin
from apps.citizens.models import CitizenVerification


@admin.register(CitizenVerification)
class CitizenVerificationAdmin(admin.ModelAdmin):
    list_display = ('citizen', 'document_type', 'document_number', 'status', 'verified_at', 'created_at')
    list_filter = ('status', 'document_type')
    search_fields = ('citizen__username', 'document_number')
