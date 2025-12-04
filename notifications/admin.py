from django.contrib import admin
from apps.notifications.models import (
    Notification, EmailNotification, SMSNotification, NotificationPreference
)

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('title', 'notification_type', 'priority', 'is_read', 'created_at')
    list_filter = ('notification_type', 'priority', 'is_read', 'created_at')
    search_fields = ('title', 'message')
    filter_horizontal = ('recipients', 'read_by')

@admin.register(EmailNotification)
class EmailNotificationAdmin(admin.ModelAdmin):
    list_display = ('subject', 'recipient_email', 'status', 'sent_at')
    list_filter = ('status', 'sent_at')
    search_fields = ('subject', 'recipient_email')

@admin.register(SMSNotification)
class SMSNotificationAdmin(admin.ModelAdmin):
    list_display = ('recipient_phone', 'status', 'sent_at')
    list_filter = ('status', 'sent_at')
    search_fields = ('recipient_phone',)

@admin.register(NotificationPreference)
class NotificationPreferenceAdmin(admin.ModelAdmin):
    list_display = ('user', 'email_low_stock', 'email_expiry', 'sms_critical_only')
    search_fields = ('user__username',)