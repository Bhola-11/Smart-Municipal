from django.contrib import admin
from apps.feedback.models import Feedback


@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ('complaint', 'citizen', 'rating', 'satisfaction', 'resolution_accepted', 'created_at')
    list_filter = ('rating', 'satisfaction', 'resolution_accepted')
    search_fields = ('complaint__complaint_number', 'comments')
