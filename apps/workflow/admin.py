from django.contrib import admin
from apps.workflow.models import WorkflowTransition


@admin.register(WorkflowTransition)
class WorkflowTransitionAdmin(admin.ModelAdmin):
    list_display = ('complaint', 'from_status', 'to_status', 'actor', 'reason', 'created_at')
    list_filter = ('from_status', 'to_status')
    search_fields = ('complaint__complaint_number', 'notes')
