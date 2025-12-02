from django.db import models
from django.core.validators import EmailValidator
from apps.accounts.models import User

class Supplier(models.Model):
    """Supplier/Vendor information"""
    
    company_name = models.CharField(max_length=200, unique=True)
    supplier_code = models.CharField(max_length=20, unique=True, editable=False)
    
    
    contact_person = models.CharField(max_length=100)
    email = models.EmailField(validators=[EmailValidator()])
    phone = models.CharField(max_length=15)
    alternate_phone = models.CharField(max_length=15, blank=True)
    website = models.URLField(blank=True)
    

    address_line1 = models.CharField(max_length=200)
    address_line2 = models.CharField(max_length=200, blank=True)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100, blank=True)
    postal_code = models.CharField(max_length=20, blank=True)
    country = models.CharField(max_length=100, default='Kenya')
    
    
    tax_id = models.CharField(max_length=50, blank=True, help_text="Tax/VAT ID")
    license_number = models.CharField(max_length=100, blank=True)
    
    
    payment_terms = models.CharField(max_length=100, blank=True, help_text="e.g., Net 30, Net 60")
    credit_limit = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    current_balance = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    
    rating = models.IntegerField(default=5, choices=[(i, str(i)) for i in range(1, 6)])
    is_active = models.BooleanField(default=True)
    
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'suppliers'
        ordering = ['company_name']
        indexes = [
            models.Index(fields=['supplier_code']),
            models.Index(fields=['company_name']),
        ]
    
    def __str__(self):
        return f"{self.company_name} ({self.supplier_code})"
    
    def save(self, *args, **kwargs):
        if not self.supplier_code:
            last_supplier = Supplier.objects.order_by('-id').first()
            if last_supplier:
                last_num = int(last_supplier.supplier_code.split('-')[-1])
                new_num = last_num + 1
            else:
                new_num = 1
            
            self.supplier_code = f'SUP-{new_num:04d}'
        
        super().save(*args, **kwargs)


class PurchaseOrder(models.Model):
    """Purchase orders to suppliers"""
    
    STATUS_CHOICES = (
        ('draft', 'Draft'),
        ('sent', 'Sent to Supplier'),
        ('confirmed', 'Confirmed'),
        ('received', 'Received'),
        ('cancelled', 'Cancelled'),
    )
    
    po_number = models.CharField(max_length=50, unique=True, editable=False)
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, related_name='purchase_orders')
    
    order_date = models.DateField(auto_now_add=True)
    expected_delivery = models.DateField()
    delivery_date = models.DateField(null=True, blank=True)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    notes = models.TextField(blank=True)
    
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='purchase_orders')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'purchase_orders'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"PO-{self.po_number} - {self.supplier.company_name}"
    
    def save(self, *args, **kwargs):
        if not self.po_number:
            from datetime import datetime
            date_str = datetime.now().strftime('%Y%m%d')
            last_po = PurchaseOrder.objects.filter(
                po_number__startswith=date_str
            ).order_by('-po_number').first()
            
            if last_po:
                last_num = int(last_po.po_number.split('-')[-1])
                new_num = last_num + 1
            else:
                new_num = 1
            
            self.po_number = f'{date_str}-{new_num:04d}'
        
        super().save(*args, **kwargs)


class PurchaseOrderItem(models.Model):
    """Items in a purchase order"""
    purchase_order = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE, related_name='items')
    medicine = models.ForeignKey('inventory.Medicine', on_delete=models.CASCADE)
    
    quantity = models.IntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    total_price = models.DecimalField(max_digits=12, decimal_places=2)
    
    received_quantity = models.IntegerField(default=0)
    
    notes = models.TextField(blank=True)
    
    class Meta:
        db_table = 'purchase_order_items'
    
    def __str__(self):
        return f"{self.medicine.name} - Qty: {self.quantity}"
    
    def save(self, *args, **kwargs):
        self.total_price = self.quantity * self.unit_price
        super().save(*args, **kwargs)
