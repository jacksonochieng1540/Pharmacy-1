from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import api_views

router = DefaultRouter()
router.register('sales', api_views.SaleViewSet, basename='sale')
router.register('returns', api_views.ReturnViewSet, basename='return')

urlpatterns = [
    path('', include(router.urls)),
]