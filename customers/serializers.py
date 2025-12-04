from rest_framework import serializers
from .models import Customer, CustomerInsurance

class CustomerInsuranceSerializer(serializers.ModelSerializer):
    is_valid = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = CustomerInsurance
        fields = '__all__'

class CustomerSerializer(serializers.ModelSerializer):
    insurances = CustomerInsuranceSerializer(many=True, read_only=True)
    full_name = serializers.CharField(read_only=True)
    age = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Customer
        fields = '__all__'
        read_only_fields = ['customer_id', 'loyalty_points', 'total_purchases']