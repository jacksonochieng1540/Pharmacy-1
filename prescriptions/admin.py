from django.contrib import admin
from prescriptions.models import Doctor, Prescription, PrescriptionItem

class PrescriptionItemInline(admin.TabularInline):
    model = PrescriptionItem
    extra = 1

@admin.register(Doctor)
class DoctorAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'specialization', 'license_number', 
                   'phone', 'is_active')
    list_filter = ('specialization', 'is_active')
    search_fields = ('first_name', 'last_name', 'license_number', 'specialization')

@admin.register(Prescription)
class PrescriptionAdmin(admin.ModelAdmin):
    list_display = ('prescription_number', 'customer', 'doctor', 
                   'prescription_date', 'valid_until', 'status')
    list_filter = ('status', 'prescription_date', 'valid_until')
    search_fields = ('prescription_number', 'customer__first_name', 
                    'customer__last_name', 'doctor__last_name')
    readonly_fields = ('prescription_number', 'created_at', 'updated_at')
    inlines = [PrescriptionItemInline]

