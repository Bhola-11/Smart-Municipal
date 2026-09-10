from django.urls import path
from apps.complaints import views

app_name = 'complaints'

urlpatterns = [
    path('', views.complaint_list_view, name='list'),
    path('new/', views.complaint_create_view, name='create'),
    path('track/', views.public_track_view, name='track'),
    path('api/subcategories/<int:category_id>/', views.subcategories_by_category_json, name='subcategories_by_category'),
    path('<str:complaint_number>/', views.complaint_detail_view, name='detail'),
]
