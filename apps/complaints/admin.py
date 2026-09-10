from django.contrib import admin
from apps.complaints.models import Category, SubCategory, Complaint


class SubCategoryInline(admin.TabularInline):
    model = SubCategory
    extra = 1


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'default_department', 'is_active', 'created_at')
    list_filter = ('default_department', 'is_active')
    search_fields = ('name', 'code')
    inlines = [SubCategoryInline]


@admin.register(Complaint)
class ComplaintAdmin(admin.ModelAdmin):
    list_display = ('complaint_number', 'title', 'citizen', 'department', 'ward', 'priority', 'severity', 'status', 'is_escalated', 'created_at')
    list_filter = ('status', 'priority', 'severity', 'department', 'ward', 'is_escalated')
    search_fields = ('complaint_number', 'title', 'description', 'specific_address')
    readonly_fields = ('complaint_number', 'created_at', 'updated_at')
