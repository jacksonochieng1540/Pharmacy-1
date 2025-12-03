from django.contrib import admin
from django.utils.html import format_html
from .models import Category, Medicine, Batch, StockAdjustment

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'medicine_count', 'created_at')
    search_fields = ('name',)
    
    def medicine_count(self, obj):
        return obj.medicines.count()
    medicine_count.short_description = 'Medicines'

class BatchInline(admin.TabularInline):
    model = Batch
    extra = 0
    fields = ('batch_number', 'quantity', 'remaining_quantity', 'unit_cost', 
              'selling_price', 'expiry_date', 'is_active')
    readonly_fields = ('remaining_quantity',)

@admin.register(Medicine)
class MedicineAdmin(admin.ModelAdmin):
    list_display = ('name', 'sku', 'category', 'form', 'strength', 
                   'unit_price', 'selling_price', 'total_quantity', 
                   'stock_status', 'is_active')
    list_filter = ('category', 'form', 'requires_prescription', 'is_active', 'created_at')
    search_fields = ('name', 'generic_name', 'sku', 'barcode', 'manufacturer')
    readonly_fields = ('total_quantity', 'created_by', 'created_at', 'updated_at')
    inlines = [BatchInline]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'generic_name', 'category', 'manufacturer', 
                      'form', 'strength')
        }),
        ('Identifiers', {
            'fields': ('sku', 'barcode')
        }),
        ('Pricing', {
            'fields': ('unit_price', 'selling_price')
        }),
        ('Stock', {
            'fields': ('total_quantity', 'reorder_level')
        }),
        ('Additional Information', {
            'fields': ('description', 'side_effects', 'storage_conditions', 
                      'requires_prescription', 'image', 'is_active'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def stock_status(self, obj):
        if obj.is_low_stock:
            return format_html(
                '<span style="color: red; font-weight: bold;">⚠ Low Stock</span>'
            )
        return format_html(
            '<span style="color: green;">✓ In Stock</span>'
        )
    stock_status.short_description = 'Status'
    
    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

@admin.register(Batch)
class BatchAdmin(admin.ModelAdmin):
    list_display = ('medicine', 'batch_number', 'quantity', 'remaining_quantity', 
                   'expiry_date', 'days_until_expiry', 'expiry_status', 'is_active')
    list_filter = ('is_expired', 'is_active', 'expiry_date', 'received_date')
    search_fields = ('batch_number', 'medicine__name')
    readonly_fields = ('received_date', 'created_at', 'updated_at')
    
    fieldsets = (
        ('Batch Information', {
            'fields': ('medicine', 'batch_number', 'supplier')
        }),
        ('Quantity', {
            'fields': ('quantity', 'remaining_quantity')
        }),
        ('Pricing', {
            'fields': ('unit_cost', 'selling_price')
        }),
        ('Dates', {
            'fields': ('manufacture_date', 'expiry_date', 'received_date')
        }),
        ('Status', {
            'fields': ('is_expired', 'is_active', 'notes')
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def days_until_expiry(self, obj):
        return obj.days_to_expiry
    days_until_expiry.short_description = 'Days to Expiry'
    
    def expiry_status(self, obj):
        if obj.is_expired:
            return format_html('<span style="color: red;">Expired</span>')
        elif obj.is_near_expiry:
            return format_html('<span style="color: orange;">Near Expiry</span>')
        return format_html('<span style="color: green;">Good</span>')
    expiry_status.short_description = 'Expiry Status'

@admin.register(StockAdjustment)
class StockAdjustmentAdmin(admin.ModelAdmin):
    list_display = ('medicine', 'adjustment_type', 'quantity', 
                   'adjusted_by', 'adjusted_at')
    list_filter = ('adjustment_type', 'adjusted_at')
    search_fields = ('medicine__name', 'reason')
    readonly_fields = ('adjusted_by', 'adjusted_at')
    
    def save_model(self, request, obj, form, change):
        if not change:
            obj.adjusted_by = request.user
        super().save_model(request, obj, form, change)