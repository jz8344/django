"""
URL configuration for trailynsafe project.
"""
from django.urls import path
from trailynapp import views

urlpatterns = [
    path('status', views.status_check, name='status'),
    path('status/', views.status_check, name='status_slash'),
    path('', views.status_check, name='root'),
]
