from django.urls import path
from apps.workflow import views

app_name = 'workflow'

urlpatterns = [
    path('transition/<str:complaint_number>/', views.transition_status_view, name='transition'),
]
