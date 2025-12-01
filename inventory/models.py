from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal
from apps.accounts.models import User
from apps.suppliers.models import Supplier

class Category(models.Model):
    """Medicine categories (e.g., Antibiotics, Painkillers)"""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'categories'
        verbose_name_plural = 'Categories'
        ordering = ['name']
    
    def __str__(self):
        return self.name


class Medicine(models.Model):
    """Main medicine/product model"""
    
    FORM_CHOICES = (
        ('tablet', 'Tablet'),
        ('capsule', 'Capsule'),
        ('syrup', 'Syrup'),
        ('injection', 'Injection'),
        ('cream', 'Cream'),
        ('drops', 'Drops'),
        ('inhaler', 'Inhaler'),
        ('powder', 'Powder'),
        ('other', 'Other'),
    )
    
    name = models.CharField(max_length=200)
    generic_name = models.CharField(max_length=200, blank=True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='medicines')
    manufacturer = models.CharField(max_length=200)
    form = models.CharField(max_length=20, choices=FORM_CHOICES)
    strength = models.CharField(max_length=50, help_text="e.g., 500mg, 10ml")
    
    # Identifiers
    sku = models.CharField(max_length=50, unique=True, help_text="Stock Keeping Unit")
    barcode = models.CharField(max_length=100, unique=True, blank=True, null=True)
    
    # Pricing
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    selling_price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    
    # Stock
    total_quantity = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    reorder_level = models.IntegerField(default=20, validators=[MinValueValidator(0)])
    
    # Additional info
    description = models.TextField(blank=True)
    side_effects = models.TextField(blank=True)
    storage_conditions = models.TextField(blank=True)
    requires_prescription = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    
    # Images
    image = models.ImageField(upload_to='medicines/', blank=True, null=True)
    
    # Metadata
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='medicines_created')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'medicines'
        verbose_name_plural = 'Medicines'
        ordering = ['name']
        indexes = [
            models.Index(fields=['sku']),
            models.Index(fields=['barcode']),
            models.Index(fields=['name']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.strength})"
    
    @property
    def is_low_stock(self):
        return self.total_quantity <= self.reorder_level
    
    @property
    def profit_margin(self):
        if self.unit_price > 0:
            return ((self.selling_price - self.unit_price) / self.unit_price) * 100
        return 0


class Batch(models.Model):
    """Track different batches of medicines with expiry dates"""
    medicine = models.ForeignKey(Medicine, on_delete=models.CASCADE, related_name='batches')
    batch_number = models.CharField(max_length=100)
    supplier = models.ForeignKey(Supplier, on_delete=models.SET_NULL, null=True, related_name='batches')
    
    quantity = models.IntegerField(validators=[MinValueValidator(0)])
    remaining_quantity = models.IntegerField(validators=[MinValueValidator(0)])
    
    unit_cost = models.DecimalField(max_digits=10, decimal_places=2)
    selling_price = models.DecimalField(max_digits=10, decimal_places=2)
    
    manufacture_date = models.DateField()
    expiry_date = models.DateField()
    received_date = models.DateField(auto_now_add=True)
    
    is_expired = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    
    notes = models.TextField(blank=True)
    
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'batches'
        verbose_name_plural = 'Batches'
        ordering = ['expiry_date']
        unique_together = ['medicine', 'batch_number']
    
    def __str__(self):
        return f"{self.medicine.name} - Batch: {self.batch_number}"
    
    @property
    def days_to_expiry(self):
        from datetime import date
        return (self.expiry_date - date.today()).days
    
    @property
    def is_near_expiry(self):
        return 0 < self.days_to_expiry <= 90  # 3 months


class StockAdjustment(models.Model):
    """Track stock adjustments (damage, theft, corrections)"""
    
    REASON_CHOICES = (
        ('damaged', 'Damaged'),
        ('expired', 'Expired'),
        ('lost', 'Lost/Theft'),
        ('return', 'Return to Supplier'),
        ('correction', 'Stock Correction'),
        ('other', 'Other'),
    )
    
    medicine = models.ForeignKey(Medicine, on_delete=models.CASCADE, related_name='adjustments')
    batch = models.ForeignKey(Batch, on_delete=models.CASCADE, null=True, blank=True)
    
    adjustment_type = models.CharField(max_length=20, choices=REASON_CHOICES)
    quantity = models.IntegerField()  # Positive for addition, negative for reduction
    reason = models.TextField()
    
    adjusted_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    adjusted_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'stock_adjustments'
        ordering = ['-adjusted_at']
    
    def __str__(self):
        return f"{self.medicine.name} - {self.adjustment_type} - {self.quantity}"