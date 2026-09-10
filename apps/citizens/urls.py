from django.urls import path
from apps.citizens import views

app_name = 'citizens'

urlpatterns = [
    path('verification/', views.citizen_verification_view, name='verification'),
]
