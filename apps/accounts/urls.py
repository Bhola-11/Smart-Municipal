"""URLs for accounts authentication and profile."""

from django.urls import path
from apps.accounts import views

app_name = 'accounts'

urlpatterns = [
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile_view, name='profile'),
    path('password-change/', views.password_change_view, name='password_change'),
    path('staff/', views.staff_management_view, name='staff_list'),
    path('staff/create/', views.create_staff_view, name='staff_create'),
]
