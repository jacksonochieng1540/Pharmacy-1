from django.urls import path
from . import views

app_name = 'notifications'

urlpatterns = [
    # Implement these later
    path('', views.notification_list, name='list'),
]