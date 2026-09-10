from django.urls import path
from apps.escalations import views

app_name = 'escalations'

urlpatterns = [
    path('', views.escalation_list_view, name='list'),
    path('trigger/<str:complaint_number>/', views.manual_escalate_view, name='trigger'),
    path('resolve/<int:pk>/', views.resolve_escalation_view, name='resolve'),
]
