from django.contrib import admin
from apps.escalations.models import Escalation


@admin.register(Escalation)
class EscalationAdmin(admin.ModelAdmin):
    list_display = ('complaint', 'level', 'reason', 'previous_owner', 'escalated_to', 'is_resolved', 'created_at')
    list_filter = ('level', 'reason', 'is_resolved')
    search_fields = ('complaint__complaint_number', 'description')
