from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    path('', views.reports_dashboard, name='dashboard'),
    path('dashboard/', views.reports_dashboard, name='dashboard_alt'),
    
    # Reports
    path('sales/', views.sales_report, name='sales'),
    path('inventory/', views.inventory_report, name='inventory'),
    path('profit-loss/', views.profit_loss_report, name='profit_loss'),
    path('customers/', views.customer_report, name='customers'),
    path('stock-movement/', views.stock_movement_report, name='stock_movement'),
]