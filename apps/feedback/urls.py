from django.urls import path
from apps.feedback import views

app_name = 'feedback'

urlpatterns = [
    path('submit/<str:complaint_number>/', views.submit_feedback_view, name='submit'),
    path('analytics/', views.feedback_dashboard_view, name='analytics'),
]
