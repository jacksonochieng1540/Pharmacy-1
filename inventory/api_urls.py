from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import api_views

router = DefaultRouter()
router.register('medicines', api_views.MedicineViewSet, basename='medicine')
router.register('categories', api_views.CategoryViewSet, basename='category')
router.register('batches', api_views.BatchViewSet, basename='batch')

urlpatterns = [
    path('', include(router.urls)),
]