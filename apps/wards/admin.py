from django.contrib import admin
from apps.wards.models import Zone, Ward, Area


@admin.register(Zone)
class ZoneAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'created_at')
    search_fields = ('name', 'code')


class AreaInline(admin.TabularInline):
    model = Area
    extra = 1


@admin.register(Ward)
class WardAdmin(admin.ModelAdmin):
    list_display = ('ward_number', 'name', 'zone', 'ward_officer', 'population', 'contact_phone')
    list_filter = ('zone',)
    search_fields = ('ward_number', 'name')
    inlines = [AreaInline]


@admin.register(Area)
class AreaAdmin(admin.ModelAdmin):
    list_display = ('name', 'ward', 'postal_code', 'landmark')
    list_filter = ('ward__zone', 'ward')
    search_fields = ('name', 'postal_code', 'landmark')
