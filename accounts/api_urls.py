from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import api_views

router = DefaultRouter()
router.register('users', api_views.UserViewSet, basename='user')
router.register('activities', api_views.UserActivityViewSet, basename='activity')

urlpatterns = [
    path('', include(router.urls)),
    path('login/', api_views.LoginAPIView.as_view(), name='login'),
    path('logout/', api_views.LogoutAPIView.as_view(), name='logout'),
    path('refresh-token/', api_views.refresh_token, name='refresh_token'),
]