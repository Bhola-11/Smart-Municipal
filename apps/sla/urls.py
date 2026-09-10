from django.urls import path
from apps.sla import views

app_name = 'sla'

urlpatterns = [
    path('', views.sla_policy_list_view, name='list'),
    path('create/', views.sla_policy_create_view, name='create'),
]
