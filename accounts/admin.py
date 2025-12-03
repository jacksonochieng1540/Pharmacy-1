from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, UserActivity

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'role', 'is_active_employee', 'is_staff')
    list_filter = ('role', 'is_staff', 'is_active', 'is_active_employee', 'date_joined')
    search_fields = ('username', 'first_name', 'last_name', 'email', 'employee_id')
    
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Additional Info', {
            'fields': ('role', 'phone', 'address', 'profile_picture', 'employee_id', 
                      'date_of_birth', 'hire_date', 'salary', 'is_active_employee')
        }),
    )
    
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Additional Info', {
            'fields': ('role', 'phone', 'email', 'first_name', 'last_name')
        }),
    )

@admin.register(UserActivity)
class UserActivityAdmin(admin.ModelAdmin):
    list_display = ('user', 'action', 'timestamp', 'ip_address')
    list_filter = ('action', 'timestamp')
    search_fields = ('user__username', 'description')
    readonly_fields = ('user', 'action', 'description', 'ip_address', 'user_agent', 'timestamp')
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False