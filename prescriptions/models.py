from django.db import models
from apps.customers.models import Customer
from apps.accounts.models import User
from apps.inventory.models import Medicine

class Doctor(models.Model):
    """Doctor/Physician information"""
    
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    specialization = models.CharField(max_length=100)
    
    license_number = models.CharField(max_length=100, unique=True)
    phone = models.CharField(max_length=15)
    email = models.EmailField(blank=True)
    
    hospital_clinic = models.CharField(max_length=200, blank=True)
    address = models.TextField(blank=True)
    
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'doctors'
        ordering = ['last_name', 'first_name']
    
    def __str__(self):
        return f"Dr. {self.first_name} {self.last_name} - {self.specialization}"
    
    @property
    def full_name(self):
        return f"Dr. {self.first_name} {self.last_name}"


class Prescription(models.Model):
    """Medical prescriptions from doctors"""
    
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('partial', 'Partially Filled'),
        ('filled', 'Filled'),
        ('cancelled', 'Cancelled'),
        ('expired', 'Expired'),
    )
    
    prescription_number = models.CharField(max_length=50, unique=True, editable=False)
    
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='prescriptions')
    doctor = models.ForeignKey(Doctor, on_delete=models.SET_NULL, null=True, related_name='prescriptions')
    
    prescription_date = models.DateField()
    valid_until = models.DateField()
    
    diagnosis = models.TextField(blank=True)
    notes = models.TextField(blank=True, help_text="Special instructions or notes")
    
    # Image of physical prescription
    prescription_image = models.ImageField(upload_to='prescriptions/', blank=True, null=True)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Tracking
    filled_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='filled_prescriptions')
    filled_at = models.DateTimeField(null=True, blank=True)
    
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='prescriptions_created')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'prescriptions'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['prescription_number']),
            models.Index(fields=['prescription_date']),
        ]
    
    def __str__(self):
        return f"RX-{self.prescription_number} - {self.customer.full_name}"
    
    def save(self, *args, **kwargs):
        if not self.prescription_number:
            from datetime import datetime
            date_str = datetime.now().strftime('%Y%m%d')
            last_prescription = Prescription.objects.filter(
                prescription_number__startswith=date_str
            ).order_by('-prescription_number').first()
            
            if last_prescription:
                last_num = int(last_prescription.prescription_number.split('-')[-1])
                new_num = last_num + 1
            else:
                new_num = 1
            
            self.prescription_number = f'{date_str}-{new_num:04d}'
        
        super().save(*args, **kwargs)
    
    @property
    def is_expired(self):
        from datetime import date
        return date.today() > self.valid_until


class PrescriptionItem(models.Model):
    """Medicines prescribed in a prescription"""
    
    prescription = models.ForeignKey(Prescription, on_delete=models.CASCADE, related_name='items')
    medicine = models.ForeignKey(Medicine, on_delete=models.CASCADE)
    
    dosage = models.CharField(max_length=100, help_text="e.g., 500mg")
    frequency = models.CharField(max_length=100, help_text="e.g., Twice daily, Every 8 hours")
    duration = models.CharField(max_length=100, help_text="e.g., 7 days, 2 weeks")
    
    quantity_prescribed = models.IntegerField()
    quantity_dispensed = models.IntegerField(default=0)
    
    instructions = models.TextField(blank=True, help_text="Special instructions for this medicine")
    
    is_filled = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'prescription_items'
    
    def __str__(self):
        return f"{self.medicine.name} - {self.dosage} - {self.frequency}"