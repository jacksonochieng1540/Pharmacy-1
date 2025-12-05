from django.urls import path
from . import views

app_name = 'inventory'

urlpatterns = [
    # Medicines
    path('', views.medicine_list, name='medicine_list'),
    path('medicines/', views.medicine_list, name='medicine_list_alt'),
    path('medicines/create/', views.medicine_create, name='medicine_create'),
    path('medicines/<int:pk>/', views.medicine_detail, name='medicine_detail'),
    path('medicines/<int:pk>/edit/', views.medicine_edit, name='medicine_edit'),
    
    # Batches
    path('medicines/<int:medicine_id>/batch/create/', views.batch_create, name='batch_create'),
    
    # Stock Management
    path('medicines/<int:medicine_id>/adjust-stock/', views.stock_adjustment, name='stock_adjustment'),
    path('low-stock/', views.low_stock_alert, name='low_stock'),
    path('expiring/', views.expiring_medicines, name='expiring'),
    
    # Categories
    path('categories/', views.categories_list, name='categories'),
]

