from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from .models import Medicine, Category, Batch, StockAdjustment
from .serializers import (
    MedicineSerializer, MedicineListSerializer, CategorySerializer,
    BatchSerializer, StockAdjustmentSerializer
)

class MedicineViewSet(viewsets.ModelViewSet):
    queryset = Medicine.objects.all()
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category', 'form', 'requires_prescription', 'is_active']
    search_fields = ['name', 'generic_name', 'sku', 'barcode']
    ordering_fields = ['name', 'unit_price', 'total_quantity', 'created_at']
    
    def get_serializer_class(self):
        if self.action == 'list':
            return MedicineListSerializer
        return MedicineSerializer
    
    @action(detail=False, methods=['get'])
    def low_stock(self, request):
        """Get medicines with low stock"""
        low_stock_items = self.queryset.filter(
            total_quantity__lte=models.F('reorder_level')
        )
        serializer = self.get_serializer(low_stock_items, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def expiring_soon(self, request):
        """Get medicines expiring within 90 days"""
        from datetime import date, timedelta
        expiry_threshold = date.today() + timedelta(days=90)
        
        expiring_batches = Batch.objects.filter(
            expiry_date__lte=expiry_threshold,
            expiry_date__gt=date.today(),
            is_active=True
        ).select_related('medicine')
        
        data = []
        for batch in expiring_batches:
            data.append({
                'medicine': MedicineListSerializer(batch.medicine).data,
                'batch': BatchSerializer(batch).data
            })
        
        return Response(data)

class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticated]
    search_fields = ['name']

class BatchViewSet(viewsets.ModelViewSet):
    queryset = Batch.objects.all()
    serializer_class = BatchSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['medicine', 'supplier', 'is_expired', 'is_active']
    ordering_fields = ['expiry_date', 'received_date']