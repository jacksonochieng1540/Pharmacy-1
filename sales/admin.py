from django.contrib import admin
from sales.models import Sale, SaleItem, Return, ReturnItem

class SaleItemInline(admin.TabularInline):
    model = SaleItem
    extra = 0
    readonly_fields = ('total_price', 'total_cost')

@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    list_display = ('invoice_number', 'customer', 'sale_date', 'payment_method', 
                   'total_amount', 'status', 'served_by')
    list_filter = ('status', 'payment_method', 'sale_date')
    search_fields = ('invoice_number', 'customer__first_name', 'customer__last_name')
    readonly_fields = ('invoice_number', 'subtotal', 'tax_amount', 'total_amount', 
                      'change_amount', 'created_at', 'updated_at')
    inlines = [SaleItemInline]

class ReturnItemInline(admin.TabularInline):
    model = ReturnItem
    extra = 0
    readonly_fields = ('total_refund',)

@admin.register(Return)
class ReturnAdmin(admin.ModelAdmin):
    list_display = ('return_number', 'original_sale', 'customer', 
                   'return_date', 'refund_amount', 'reason')
    list_filter = ('reason', 'return_date')
    search_fields = ('return_number', 'original_sale__invoice_number')
    readonly_fields = ('return_number', 'created_at')
    inlines = [ReturnItemInline]

