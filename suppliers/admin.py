from django.contrib import admin
from suppliers.models import Supplier, PurchaseOrder, PurchaseOrderItem

class PurchaseOrderItemInline(admin.TabularInline):
    model = PurchaseOrderItem
    extra = 1

@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ('supplier_code', 'company_name', 'contact_person', 
                   'phone', 'email', 'rating', 'is_active')
    list_filter = ('is_active', 'rating', 'created_at')
    search_fields = ('company_name', 'supplier_code', 'contact_person', 'email')
    readonly_fields = ('supplier_code', 'current_balance', 'created_at', 'updated_at')

@admin.register(PurchaseOrder)
class PurchaseOrderAdmin(admin.ModelAdmin):
    list_display = ('po_number', 'supplier', 'order_date', 'expected_delivery', 
                   'status', 'total_amount')
    list_filter = ('status', 'order_date', 'expected_delivery')
    search_fields = ('po_number', 'supplier__company_name')
    readonly_fields = ('po_number', 'subtotal', 'tax_amount', 'total_amount', 
                      'created_at', 'updated_at')
    inlines = [PurchaseOrderItemInline]

