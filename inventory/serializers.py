from rest_framework import serializers
from .models import Category, Medicine, Batch, StockAdjustment
from suppliers.models import Supplier

class CategorySerializer(serializers.ModelSerializer):
    medicine_count = serializers.IntegerField(source='medicines.count', read_only=True)
    
    class Meta:
        model = Category
        fields = ['id', 'name', 'description', 'medicine_count', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']


class BatchSerializer(serializers.ModelSerializer):
    supplier_name = serializers.CharField(source='supplier.company_name', read_only=True)
    days_to_expiry = serializers.IntegerField(read_only=True)
    is_near_expiry = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = Batch
        fields = [
            'id', 'medicine', 'batch_number', 'supplier', 'supplier_name',
            'quantity', 'remaining_quantity', 'unit_cost', 'selling_price',
            'manufacture_date', 'expiry_date', 'received_date',
            'is_expired', 'is_active', 'notes', 'days_to_expiry',
            'is_near_expiry', 'created_at', 'updated_at'
        ]
        read_only_fields = ['received_date', 'created_at', 'updated_at']
    
    def validate(self, data):
        if data.get('expiry_date') and data.get('manufacture_date'):
            if data['expiry_date'] <= data['manufacture_date']:
                raise serializers.ValidationError(
                    "Expiry date must be after manufacture date"
                )
        return data


class MedicineSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    is_low_stock = serializers.BooleanField(read_only=True)
    profit_margin = serializers.DecimalField(
        max_digits=5, decimal_places=2, read_only=True
    )
    batches = BatchSerializer(many=True, read_only=True)
    
    class Meta:
        model = Medicine
        fields = [
            'id', 'name', 'generic_name', 'category', 'category_name',
            'manufacturer', 'form', 'strength', 'sku', 'barcode',
            'unit_price', 'selling_price', 'total_quantity', 'reorder_level',
            'description', 'side_effects', 'storage_conditions',
            'requires_prescription', 'is_active', 'image', 'is_low_stock',
            'profit_margin', 'batches', 'created_at', 'updated_at'
        ]
        read_only_fields = ['total_quantity', 'created_at', 'updated_at']
    
    def validate(self, data):
        if data.get('selling_price') and data.get('unit_price'):
            if data['selling_price'] < data['unit_price']:
                raise serializers.ValidationError(
                    "Selling price cannot be less than unit price"
                )
        return data


class MedicineListSerializer(serializers.ModelSerializer):
    """Lighter serializer for list views"""
    category_name = serializers.CharField(source='category.name', read_only=True)
    is_low_stock = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = Medicine
        fields = [
            'id', 'name', 'generic_name', 'category_name', 'form', 'strength',
            'sku', 'unit_price', 'selling_price', 'total_quantity',
            'is_low_stock', 'is_active', 'image'
        ]


class StockAdjustmentSerializer(serializers.ModelSerializer):
    medicine_name = serializers.CharField(source='medicine.name', read_only=True)
    adjusted_by_name = serializers.CharField(
        source='adjusted_by.get_full_name', read_only=True
    )
    
    class Meta:
        model = StockAdjustment
        fields = [
            'id', 'medicine', 'medicine_name', 'batch', 'adjustment_type',
            'quantity', 'reason', 'adjusted_by', 'adjusted_by_name', 'adjusted_at'
        ]
        read_only_fields = ['adjusted_by', 'adjusted_at']


class MedicineSearchSerializer(serializers.Serializer):
    """Serializer for medicine search"""
    query = serializers.CharField(required=True, min_length=2)
    category = serializers.IntegerField(required=False)
    form = serializers.CharField(required=False)
    requires_prescription = serializers.BooleanField(required=False)