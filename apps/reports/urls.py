from django.urls import path
from apps.reports import views

app_name = 'reports'

urlpatterns = [
    path('', views.report_center_view, name='center'),
    path('export/csv/', views.export_complaints_csv, name='export_csv'),
    path('printable/', views.printable_executive_report, name='printable'),
]
