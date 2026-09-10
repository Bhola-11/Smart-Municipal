from django.urls import path
from apps.dashboard import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.index_view, name='index'),
    path('citizen/', views.citizen_dashboard_view, name='citizen'),
    path('staff/', views.staff_dashboard_view, name='staff'),
    path('manager/', views.manager_dashboard_view, name='manager'),
    path('admin-portal/', views.admin_dashboard_view, name='admin'),
    path('transparency/', views.public_transparency_view, name='transparency'),
]
