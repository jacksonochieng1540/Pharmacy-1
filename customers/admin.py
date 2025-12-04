from django.contrib import admin
from apps.customers.models import Customer, CustomerInsurance

class CustomerInsuranceInline(admin.TabularInline):
    model = CustomerInsurance
    extra = 0

@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('customer_id', 'full_name', 'phone', 'email', 
                   'loyalty_points', 'total_purchases', 'is_active')
    list_filter = ('is_active', 'gender', 'created_at')
    search_fields = ('first_name', 'last_name', 'phone', 'email', 'customer_id')
    readonly_fields = ('customer_id', 'loyalty_points', 'total_purchases', 
                      'created_at', 'updated_at')
    inlines = [CustomerInsuranceInline]
    
    fieldsets = (
        ('Personal Information', {
            'fields': ('customer_id', 'first_name', 'last_name', 'email', 
                      'phone', 'alternate_phone', 'date_of_birth', 'gender')
        }),
        ('Address', {
            'fields': ('address_line1', 'address_line2', 'city', 'state', 
                      'postal_code', 'country')
        }),
        ('Medical Information', {
            'fields': ('allergies', 'medical_conditions', 'blood_group'),
            'classes': ('collapse',)
        }),
        ('Customer Stats', {
            'fields': ('loyalty_points', 'total_purchases')
        }),
        ('Status & Notes', {
            'fields': ('is_active', 'notes')
        }),
    )

@admin.register(CustomerInsurance)
class CustomerInsuranceAdmin(admin.ModelAdmin):
    list_display = ('customer', 'insurance_company', 'policy_number', 
                   'coverage_percentage', 'valid_until', 'is_valid_status')
    list_filter = ('insurance_company', 'is_active', 'valid_until')
    search_fields = ('customer__first_name', 'customer__last_name', 
                    'policy_number', 'insurance_company')
    
    def is_valid_status(self, obj):
        from django.utils.html import format_html
        if obj.is_valid:
            return format_html('<span style="color: green;">Active</span>')
        return format_html('<span style="color: red;">Expired</span>')
    is_valid_status.short_description = 'Status'

