from rest_framework import serializers
from .models import Sale, SaleItem, Return, ReturnItem

class SaleItemSerializer(serializers.ModelSerializer):
    medicine_name = serializers.CharField(source='medicine.name', read_only=True)
    profit = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    
    class Meta:
        model = SaleItem
        fields = '__all__'
        read_only_fields = ['total_price', 'total_cost']

class SaleSerializer(serializers.ModelSerializer):
    items = SaleItemSerializer(many=True, read_only=True)
    customer_name = serializers.CharField(source='customer.full_name', read_only=True)
    served_by_name = serializers.CharField(source='served_by.get_full_name', read_only=True)
    profit = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    
    class Meta:
        model = Sale
        fields = '__all__'
        read_only_fields = [
            'invoice_number', 'subtotal', 'discount_amount', 'tax_amount',
            'total_amount', 'change_amount', 'created_at', 'updated_at'
        ]

class SaleListSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source='customer.full_name', read_only=True)
    
    class Meta:
        model = Sale
        fields = [
            'id', 'invoice_number', 'customer_name', 'sale_date',
            'payment_method', 'total_amount', 'status'
        ]

class ReturnItemSerializer(serializers.ModelSerializer):
    medicine_name = serializers.CharField(source='medicine.name', read_only=True)
    
    class Meta:
        model = ReturnItem
        fields = '__all__'
        read_only_fields = ['total_refund']

class ReturnSerializer(serializers.ModelSerializer):
    items = ReturnItemSerializer(many=True, read_only=True)
    customer_name = serializers.CharField(source='customer.full_name', read_only=True)
    
    class Meta:
        model = Return
        fields = '__all__'
        read_only_fields = ['return_number', 'created_at']

