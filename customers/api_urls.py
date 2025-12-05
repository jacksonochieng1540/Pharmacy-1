from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import api_views

router = DefaultRouter()
router.register('customers', api_views.CustomerViewSet, basename='customer')

urlpatterns = [
    path('', include(router.urls)),
]