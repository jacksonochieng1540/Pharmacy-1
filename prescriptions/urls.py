from django.urls import path
from . import views

app_name = 'prescriptions'

urlpatterns = [
    # Prescriptions
    path('', views.prescription_list, name='prescription_list'),
    path('prescriptions/', views.prescription_list, name='prescription_list_alt'),
    path('prescriptions/create/', views.prescription_create, name='prescription_create'),
    path('prescriptions/<int:pk>/', views.prescription_detail, name='prescription_detail'),
    
    # Doctors
    path('doctors/', views.doctor_list, name='doctor_list'),
]
