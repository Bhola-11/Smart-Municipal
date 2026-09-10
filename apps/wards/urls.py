from django.urls import path
from apps.wards import views

app_name = 'wards'

urlpatterns = [
    path('', views.ward_list_view, name='list'),
    path('create/', views.ward_create_view, name='create'),
    path('<int:pk>/', views.ward_detail_view, name='detail'),
    path('api/areas/<int:ward_id>/', views.areas_by_ward_json, name='areas_by_ward'),
]
