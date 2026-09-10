from django.contrib import admin
from apps.communications.models import ComplaintMessage


@admin.register(ComplaintMessage)
class ComplaintMessageAdmin(admin.ModelAdmin):
    list_display = ('complaint', 'sender', 'message_type', 'is_internal_only', 'created_at')
    list_filter = ('message_type', 'is_internal_only')
    search_fields = ('complaint__complaint_number', 'message')
