from rest_framework import serializers
from .models import Sale, SaleItem, Return, ReturnItem

class SaleItemSerializer(serializers.ModelSerializer):
    medicine_name = serializers.CharField(source='medicine.name', read_only=True)
    profit = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    
    class Meta:
        model = SaleItem
        fields = '__all__'

class SaleSerializer(serializers.ModelSerializer):
    items = SaleItemSerializer(many=True, read_only=True)
    customer_name = serializers.CharField(source='customer.full_name', read_only=True)
    served_by_name = serializers.CharField(source='served_by.get_full_name', read_only=True)
    profit = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    
    class Meta:
        model = Sale
        fields = '__all__'
        read_only_fields = ['invoice_number', 'subtotal', 'tax_amount', 'total_amount']