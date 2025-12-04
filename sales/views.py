# ============ apps/sales/views.py ============
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_POST
from decimal import Decimal
from datetime import datetime

from .models import Sale, SaleItem, Return, ReturnItem
from apps.inventory.models import Medicine, Batch
from apps.customers.models import Customer
from apps.prescriptions.models import Prescription

@login_required
def pos_view(request):
    """Point of Sale interface"""
    customers = Customer.objects.filter(is_active=True)
    payment_methods = Sale.PAYMENT_METHOD_CHOICES
    
    context = {
        'customers': customers,
        'payment_methods': payment_methods,
    }
    return render(request, 'sales/pos.html', context)

@login_required
@require_POST
def process_sale(request):
    """Process a sale transaction"""
    try:
        with transaction.atomic():
            # Get sale data from request
            customer_id = request.POST.get('customer_id')
            prescription_id = request.POST.get('prescription_id')
            payment_method = request.POST.get('payment_method')
            amount_paid = Decimal(request.POST.get('amount_paid', 0))
            discount_percentage = Decimal(request.POST.get('discount_percentage', 0))
            
            # Get cart items (assuming JSON format)
            import json
            cart_items = json.loads(request.POST.get('cart_items', '[]'))
            
            if not cart_items:
                return JsonResponse({'success': False, 'error': 'Cart is empty'})
            
            # Create sale
            sale = Sale.objects.create(
                customer_id=customer_id if customer_id else None,
                prescription_id=prescription_id if prescription_id else None,
                payment_method=payment_method,
                discount_percentage=discount_percentage,
                served_by=request.user
            )
            
            subtotal = Decimal('0')
            
            # Process each item
            for item in cart_items:
                medicine = Medicine.objects.get(id=item['medicine_id'])
                quantity = int(item['quantity'])
                
                # Check stock availability
                if medicine.total_quantity < quantity:
                    raise ValueError(f"Insufficient stock for {medicine.name}")
                
                # Get oldest batch (FIFO)
                batch = medicine.batches.filter(
                    is_active=True,
                    remaining_quantity__gt=0
                ).order_by('expiry_date').first()
                
                if not batch:
                    raise ValueError(f"No available batch for {medicine.name}")
                
                # Create sale item
                sale_item = SaleItem.objects.create(
                    sale=sale,
                    medicine=medicine,
                    batch=batch,
                    quantity=quantity,
                    unit_price=medicine.selling_price,
                    unit_cost=batch.unit_cost
                )
                
                # Update stock
                medicine.total_quantity -= quantity
                medicine.save()
                
                batch.remaining_quantity -= quantity
                batch.save()
                
                subtotal += sale_item.total_price
            
            # Update sale totals
            sale.subtotal = subtotal
            sale.amount_paid = amount_paid
            sale.save()
            
            # Update customer stats
            if sale.customer:
                sale.customer.total_purchases += sale.total_amount
                sale.customer.loyalty_points += int(sale.total_amount / 100)
                sale.customer.save()
            
            return JsonResponse({
                'success': True,
                'invoice_number': sale.invoice_number,
                'total_amount': float(sale.total_amount),
                'change_amount': float(sale.change_amount)
            })
            
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
def search_medicine(request):
    """Search for medicines (AJAX)"""
    query = request.GET.get('q', '')
    
    if len(query) < 2:
        return JsonResponse({'results': []})
    
    medicines = Medicine.objects.filter(
        name__icontains=query,
        is_active=True,
        total_quantity__gt=0
    )[:10]
    
    results = []
    for medicine in medicines:
        results.append({
            'id': medicine.id,
            'name': medicine.name,
            'strength': medicine.strength,
            'form': medicine.form,
            'price': float(medicine.selling_price),
            'stock': medicine.total_quantity,
            'sku': medicine.sku,
            'requires_prescription': medicine.requires_prescription
        })
    
    return JsonResponse({'results': results})

@login_required
def sale_receipt(request, sale_id):
    """Generate sale receipt"""
    sale = get_object_or_404(Sale, id=sale_id)
    
    context = {
        'sale': sale,
    }
    return render(request, 'sales/receipt.html', context)

@login_required
def sales_list(request):
    """List all sales"""
    sales = Sale.objects.all().select_related('customer', 'served_by')
    
    # Filter by date range if provided
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    if start_date and end_date:
        sales = sales.filter(sale_date__range=[start_date, end_date])
    
    context = {
        'sales': sales,
    }
    return render(request, 'sales/sales_list.html', context)