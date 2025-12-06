from rest_framework import serializers
from .models import User, UserActivity

class UserSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(source='get_full_name', read_only=True)
    
    class Meta:
        model = User   
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name', 'full_name',
            'role', 'phone', 'address', 'profile_picture', 'employee_id',
            'date_of_birth', 'hire_date', 'is_active_employee', 'date_joined'
        ]
        read_only_fields = ['date_joined']

class UserDetailSerializer(UserSerializer):
    can_manage_inventory = serializers.BooleanField(read_only=True)
    can_process_sales = serializers.BooleanField(read_only=True)
    
    class Meta(UserSerializer.Meta):
        fields = UserSerializer.Meta.fields + ['can_manage_inventory', 'can_process_sales', 'salary']

class UserActivitySerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    
    class Meta:
        model = UserActivity
        fields = '__all__'

class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

class ChangePasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, min_length=8)

