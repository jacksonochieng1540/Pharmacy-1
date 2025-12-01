from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal
from apps.customers.models import Customer
from apps.accounts.models import User
from apps.inventory.models import Medicine, Batch
from apps.prescriptions.models import Prescription

class Sale(models.Model):
    """Main sales/invoice model"""
    
    PAYMENT_METHOD_CHOICES = (
        ('cash', 'Cash'),
        ('card', 'Credit/Debit Card'),
        ('mobile', 'Mobile Money'),
        ('insurance', 'Insurance'),
        ('credit', 'Credit'),
    )
    
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('refunded', 'Refunded'),
        ('cancelled', 'Cancelled'),
    )
    
    invoice_number = models.CharField(max_length=50, unique=True, editable=False)
    
    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True, blank=True, related_name='sales')
    prescription = models.ForeignKey(Prescription, on_delete=models.SET_NULL, null=True, blank=True, related_name='sales')
    
    sale_date = models.DateTimeField(auto_now_add=True)
    
    
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tax_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=16)  # VAT 16%
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, default='cash')
    amount_paid = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    change_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    
    insurance_coverage = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    customer_copay = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='completed')
    
    
    notes = models.TextField(blank=True)
    served_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='sales')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'sales'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['invoice_number']),
            models.Index(fields=['sale_date']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"Invoice #{self.invoice_number} - {self.total_amount}"
    
    def save(self, *args, **kwargs):
        if not self.invoice_number:
            from datetime import datetime
            date_str = datetime.now().strftime('%Y%m%d')
            last_sale = Sale.objects.filter(
                invoice_number__startswith=f'INV-{date_str}'
            ).order_by('-invoice_number').first()
            
            if last_sale:
                last_num = int(last_sale.invoice_number.split('-')[-1])
                new_num = last_num + 1
            else:
                new_num = 1
            
            self.invoice_number = f'INV-{date_str}-{new_num:05d}'
        
        # Calculate totals
        self.discount_amount = (self.subtotal * self.discount_percentage) / 100
        taxable_amount = self.subtotal - self.discount_amount
        self.tax_amount = (taxable_amount * self.tax_percentage) / 100
        self.total_amount = taxable_amount + self.tax_amount
        
        if self.amount_paid >= self.total_amount:
            self.change_amount = self.amount_paid - self.total_amount
        
        super().save(*args, **kwargs)
    
    @property
    def profit(self):
        """Calculate profit for this sale"""
        total_cost = sum(item.total_cost for item in self.items.all())
        return self.total_amount - total_cost


class SaleItem(models.Model):
    """Items in a sale"""
    
    sale = models.ForeignKey(Sale, on_delete=models.CASCADE, related_name='items')
    medicine = models.ForeignKey(Medicine, on_delete=models.CASCADE)
    batch = models.ForeignKey(Batch, on_delete=models.SET_NULL, null=True)
    
    quantity = models.IntegerField(validators=[MinValueValidator(1)])
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    total_price = models.DecimalField(max_digits=12, decimal_places=2)
    
    # Track cost for profit calculation
    unit_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    class Meta:
        db_table = 'sale_items'
    
    def __str__(self):
        return f"{self.medicine.name} x {self.quantity}"
    
    def save(self, *args, **kwargs):
        self.total_price = self.quantity * self.unit_price
        self.discount_amount = (self.total_price * self.discount_percentage) / 100
        self.total_price -= self.discount_amount
        
        self.total_cost = self.quantity * self.unit_cost
        
        super().save(*args, **kwargs)
    
    @property
    def profit(self):
        return self.total_price - self.total_cost


class Return(models.Model):
    """Product returns/refunds"""
    
    REASON_CHOICES = (
        ('expired', 'Expired Product'),
        ('damaged', 'Damaged Product'),
        ('wrong_item', 'Wrong Item'),
        ('customer_request', 'Customer Request'),
        ('other', 'Other'),
    )
    
    return_number = models.CharField(max_length=50, unique=True, editable=False)
    
    original_sale = models.ForeignKey(Sale, on_delete=models.CASCADE, related_name='returns')
    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True)
    
    return_date = models.DateTimeField(auto_now_add=True)
    reason = models.CharField(max_length=50, choices=REASON_CHOICES)
    notes = models.TextField(blank=True)
    
    refund_amount = models.DecimalField(max_digits=10, decimal_places=2)
    refund_method = models.CharField(max_length=20, choices=Sale.PAYMENT_METHOD_CHOICES)
    
    processed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'returns'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Return #{self.return_number}"
    
    def save(self, *args, **kwargs):
        if not self.return_number:
            from datetime import datetime
            date_str = datetime.now().strftime('%Y%m%d')
            last_return = Return.objects.filter(
                return_number__startswith=f'RET-{date_str}'
            ).order_by('-return_number').first()
            
            if last_return:
                last_num = int(last_return.return_number.split('-')[-1])
                new_num = last_num + 1
            else:
                new_num = 1
            
            self.return_number = f'RET-{date_str}-{new_num:04d}'
        
        super().save(*args, **kwargs)


class ReturnItem(models.Model):
    """Items being returned"""
    
    return_record = models.ForeignKey(Return, on_delete=models.CASCADE, related_name='items')
    sale_item = models.ForeignKey(SaleItem, on_delete=models.CASCADE)
    medicine = models.ForeignKey(Medicine, on_delete=models.CASCADE)
    
    quantity = models.IntegerField(validators=[MinValueValidator(1)])
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    total_refund = models.DecimalField(max_digits=10, decimal_places=2)
    
    restock = models.BooleanField(default=False, help_text="Add back to inventory?")
    
    class Meta:
        db_table = 'return_items'
    
    def __str__(self):
        return f"{self.medicine.name} x {self.quantity}"
    
    def save(self, *args, **kwargs):
        self.total_refund = self.quantity * self.unit_price
        super().save(*args, **kwargs)
