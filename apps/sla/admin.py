from django.contrib import admin
from apps.sla.models import SLAPolicy, SLALog


@admin.register(SLAPolicy)
class SLAPolicyAdmin(admin.ModelAdmin):
    list_display = ('name', 'department', 'category', 'priority', 'resolution_time_hours', 'is_active')
    list_filter = ('is_active', 'priority')
    search_fields = ('name',)


@admin.register(SLALog)
class SLALogAdmin(admin.ModelAdmin):
    list_display = ('complaint', 'policy', 'deadline', 'status', 'actual_hours_taken')
    list_filter = ('status',)
    search_fields = ('complaint__complaint_number',)
