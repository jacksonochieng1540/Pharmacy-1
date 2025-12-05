"""
URL configuration for Pharmacy_project project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('accounts.urls')),  
    path('inventory/', include('inventory.urls')),
    path('sales/', include('sales.urls')),
    path('customers/', include('customers.urls')),
    path('suppliers/', include('suppliers.urls')),
    path('prescriptions/', include('prescriptions.urls')),
    path('reports/', include('report.urls')),
    path('notifications/', include('notifications.urls')),
    
    # API Endpoints
    path('api/auth/', include('accounts.api_urls')),
    path('api/inventory/', include('inventory.api_urls')),
    path('api/sales/', include('sales.api_urls')),
    path('api/customers/', include('customers.api_urls')),
    path('api/suppliers/', include('suppliers.api_urls')),
    path('api/prescriptions/', include('prescriptions.api_urls')),
    path('api/reports/', include('report.api_urls')),
    path('api/notifications/', include('notifications.api_urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# Admin site customization
admin.site.site_header = "Pharmacy Management System"
admin.site.site_title = "Pharmacy Admin"
admin.site.index_title = "Welcome to Pharmacy Management System"
