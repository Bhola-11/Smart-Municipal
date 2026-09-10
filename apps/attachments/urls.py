from django.urls import path
from apps.attachments import views

app_name = 'attachments'

urlpatterns = [
    path('upload/<str:complaint_number>/', views.upload_attachment_view, name='upload'),
    path('view/<int:pk>/', views.download_attachment_view, name='view'),
]
