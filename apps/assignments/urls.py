from django.urls import path
from apps.assignments import views

app_name = 'assignments'

urlpatterns = [
    path('assign/<str:complaint_number>/', views.assign_complaint_view, name='assign'),
    path('accept/<int:pk>/', views.accept_assignment_view, name='accept'),
    path('reject/<int:pk>/', views.reject_assignment_view, name='reject'),
    path('workload/', views.workload_monitor_view, name='workload'),
]
