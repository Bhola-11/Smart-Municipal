from django.contrib import admin
from apps.assignments.models import Assignment


@admin.register(Assignment)
class AssignmentAdmin(admin.ModelAdmin):
    list_display = ('complaint', 'staff', 'assigned_by', 'status', 'created_at', 'accepted_at')
    list_filter = ('status',)
    search_fields = ('complaint__complaint_number', 'staff__username')
