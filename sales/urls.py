from django.urls import path
from . import views

app_name = 'sales'

urlpatterns = [
    # Point of Sale
    path('pos/', views.pos_view, name='pos'),
    path('pos/search-medicine/', views.search_medicine_ajax, name='search_medicine'),
    path('pos/process/', views.process_sale, name='process_sale'),
    path('pos/customer-info/<int:customer_id>/', views.get_customer_info, name='customer_info'),
    
    # Sales Management
    path('', views.sales_list, name='sales_list'),
    path('sales/', views.sales_list, name='sales_list_alt'),
    path('sales/<int:sale_id>/', views.sale_detail, name='sale_detail'),
    path('sales/<int:sale_id>/receipt/', views.sale_receipt, name='receipt'),
    
    # Returns
    path('sales/<int:sale_id>/return/', views.process_return, name='process_return'),
    path('returns/', views.returns_list, name='returns_list'),
]