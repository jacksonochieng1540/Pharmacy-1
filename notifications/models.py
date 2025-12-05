from django.db import models
from accounts.models import User
from inventory.models import Medicine, Batch

class Notification(models.Model):
    """System notifications and alerts"""
    
    TYPE_CHOICES = (
        ('low_stock', 'Low Stock Alert'),
        ('expiry', 'Expiry Alert'),
        ('expired', 'Expired Product'),
        ('reorder', 'Reorder Reminder'),
        ('sale', 'Sale Notification'),
        ('purchase', 'Purchase Order'),
        ('system', 'System Notification'),
        ('info', 'Information'),
    )
    
    PRIORITY_CHOICES = (
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    )
    
    notification_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    
    title = models.CharField(max_length=200)
    message = models.TextField()
    
    # Related objects (optional)
    medicine = models.ForeignKey(Medicine, on_delete=models.CASCADE, null=True, blank=True, related_name='notifications')
    batch = models.ForeignKey(Batch, on_delete=models.CASCADE, null=True, blank=True, related_name='notifications')
    
    # Recipients (if empty, notify all admins/managers)
    recipients = models.ManyToManyField(User, related_name='notifications', blank=True)
    
    is_read = models.BooleanField(default=False)
    read_by = models.ManyToManyField(User, related_name='read_notifications', blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'notifications'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['notification_type']),
            models.Index(fields=['priority']),
            models.Index(fields=['is_read']),
        ]
    
    def __str__(self):
        return f"{self.get_priority_display()} - {self.title}"
    
    @property
    def is_expired(self):
        from django.utils import timezone
        if self.expires_at:
            return timezone.now() > self.expires_at
        return False


class EmailNotification(models.Model):
    """Email notifications sent to users"""
    
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('sent', 'Sent'),
        ('failed', 'Failed'),
    )
    
    notification = models.ForeignKey(Notification, on_delete=models.CASCADE, related_name='emails')
    
    recipient_email = models.EmailField()
    subject = models.CharField(max_length=200)
    body = models.TextField()
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    error_message = models.TextField(blank=True)
    
    sent_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'email_notifications'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.subject} - {self.recipient_email}"


class SMSNotification(models.Model):
    """SMS notifications sent to users"""
    
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('sent', 'Sent'),
        ('failed', 'Failed'),
    )
    
    notification = models.ForeignKey(Notification, on_delete=models.CASCADE, related_name='sms')
    
    recipient_phone = models.CharField(max_length=15)
    message = models.TextField(max_length=160)  # SMS character limit
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    error_message = models.TextField(blank=True)
    
    sent_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'sms_notifications'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"SMS to {self.recipient_phone}"


class NotificationPreference(models.Model):
    """User preferences for notifications"""
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='notification_preferences')
    
    # Email preferences
    email_low_stock = models.BooleanField(default=True)
    email_expiry = models.BooleanField(default=True)
    email_sales = models.BooleanField(default=False)
    email_daily_report = models.BooleanField(default=False)
    
    # SMS preferences
    sms_low_stock = models.BooleanField(default=False)
    sms_expiry = models.BooleanField(default=False)
    sms_critical_only = models.BooleanField(default=True)
    
    # In-app preferences
    in_app_notifications = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'notification_preferences'
    
    def __str__(self):
        return f"Notification preferences for {self.user.username}"