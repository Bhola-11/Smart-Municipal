from django.urls import path
from apps.communications import views

app_name = 'communications'

urlpatterns = [
    path('post/<str:complaint_number>/', views.post_message_view, name='post'),
]
