from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    # Authentication
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # Dashboard
    path('', views.dashboard, name='dashboard'),
    path('dashboard/', views.dashboard, name='dashboard_alt'),
    
    # Profile
    path('profile/', views.profile_view, name='profile'),
    path('change-password/', views.change_password, name='change_password'),
    
    # User Management
    path('users/', views.user_list, name='user_list'),
    path('users/<int:pk>/', views.user_detail, name='user_detail'),
]
