from rest_framework import serializers
from .models import Notification, EmailNotification, SMSNotification, NotificationPreference

class NotificationSerializer(serializers.ModelSerializer):
    medicine_name = serializers.CharField(source='medicine.name', read_only=True)
    is_expired = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = Notification
        fields = '__all__'

class EmailNotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmailNotification
        fields = '__all__'

class SMSNotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = SMSNotification
        fields = '__all__'

class NotificationPreferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationPreference
        fields = '__all__'