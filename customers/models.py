from django.db import models
from django.core.validators import EmailValidator

class Customer(models.Model):
    """Customer/Patient information"""
    
    GENDER_CHOICES = (
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    )
    
    # Personal Information
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(unique=True, blank=True, null=True, validators=[EmailValidator()])
    phone = models.CharField(max_length=15, unique=True)
    alternate_phone = models.CharField(max_length=15, blank=True)
    
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, blank=True)
    
    # Address
    address_line1 = models.CharField(max_length=200)
    address_line2 = models.CharField(max_length=200, blank=True)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100, blank=True)
    postal_code = models.CharField(max_length=20, blank=True)
    country = models.CharField(max_length=100, default='Kenya')
    
    # Medical Information
    allergies = models.TextField(blank=True, help_text="Known drug allergies")
    medical_conditions = models.TextField(blank=True)
    blood_group = models.CharField(max_length=5, blank=True)
    
    # Customer ID
    customer_id = models.CharField(max_length=20, unique=True, editable=False)
    
    # Loyalty Program
    loyalty_points = models.IntegerField(default=0)
    total_purchases = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # Status
    is_active = models.BooleanField(default=True)
    
    # Metadata
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'customers'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['customer_id']),
            models.Index(fields=['phone']),
            models.Index(fields=['email']),
        ]
    
    def __str__(self):
        return f"{self.first_name} {self.last_name} - {self.phone}"
    
    def save(self, *args, **kwargs):
        if not self.customer_id:
            # Generate customer ID: CUST-YYYYMMDD-XXX
            from datetime import datetime
            date_str = datetime.now().strftime('%Y%m%d')
            last_customer = Customer.objects.filter(
                customer_id__startswith=f'CUST-{date_str}'
            ).order_by('-customer_id').first()
            
            if last_customer:
                last_num = int(last_customer.customer_id.split('-')[-1])
                new_num = last_num + 1
            else:
                new_num = 1
            
            self.customer_id = f'CUST-{date_str}-{new_num:03d}'
        
        super().save(*args, **kwargs)
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    @property
    def age(self):
        if self.date_of_birth:
            from datetime import date
            today = date.today()
            return today.year - self.date_of_birth.year - (
                (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day)
            )
        return None


class CustomerInsurance(models.Model):
    """Customer insurance information"""
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='insurances')
    
    insurance_company = models.CharField(max_length=200)
    policy_number = models.CharField(max_length=100, unique=True)
    group_number = models.CharField(max_length=100, blank=True)
    
    coverage_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    
    valid_from = models.DateField()
    valid_until = models.DateField()
    
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'customer_insurance'
        verbose_name_plural = 'Customer Insurance'
        ordering = ['-valid_until']
    
    def __str__(self):
        return f"{self.customer.full_name} - {self.insurance_company}"
    
    @property
    def is_valid(self):
        from datetime import date
        return self.valid_from <= date.today() <= self.valid_until