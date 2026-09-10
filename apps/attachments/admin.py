from django.contrib import admin
from apps.attachments.models import Attachment


@admin.register(Attachment)
class AttachmentAdmin(admin.ModelAdmin):
    list_display = ('complaint', 'stage', 'uploaded_by', 'file_type', 'file_size', 'is_internal_only', 'created_at')
    list_filter = ('stage', 'is_internal_only')
    search_fields = ('complaint__complaint_number', 'caption')
