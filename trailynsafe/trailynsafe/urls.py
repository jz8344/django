"""
"""
URL configuration for trailynsafe project.
"""
from django.contrib import admin # Added for admin.site.urls
from django.urls import path
from trailynapp import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('status', views.status_check, name='status'),
    path('status/', views.status_check, name='status_slash'),
    path('db-test', views.db_test, name='db_test'),
    path('db-test/', views.db_test, name='db_test_slash'),
    path('', views.status_check, name='root'),
]
