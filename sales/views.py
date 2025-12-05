from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.db.models import Sum, Count, Q, F
from django.http import JsonResponse, HttpResponse
from django.core.paginator import Paginator
from django.utils import timezone
from datetime import datetime, timedelta
from decimal import Decimal
import json

from .models import Sale, SaleItem, Return, ReturnItem
from inventory.models import Medicine, Batch
from customers.models import Customer
from prescriptions.models import Prescription
from accounts.models import UserActivity


@login_required
def pos_view(request):
    """Point of Sale interface"""
    if not request.user.can_process_sales:
        messages.error(request, 'You do not have permission to process sales.')
        return redirect('accounts:dashboard')
    
    # Get active customers for dropdown
    customers = Customer.objects.filter(is_active=True).order_by('first_name')
    
    # Get payment methods
    payment_methods = Sale.PAYMENT_METHOD_CHOICES
    
    context = {
        'customers': customers,
        'payment_methods': payment_methods,
    }
    
    return render(request, 'sales/pos.html', context)


@login_required
def search_medicine_ajax(request):
    """AJAX endpoint to search medicines for POS"""
    query = request.GET.get('q', '').strip()
    
    if len(query) < 2:
        return JsonResponse({'results': []})
    
    # Search medicines
    medicines = Medicine.objects.filter(
        Q(name__icontains=query) |
        Q(generic_name__icontains=query) |
        Q(sku__icontains=query) |
        Q(barcode__iexact=query),
        is_active=True,
        total_quantity__gt=0
    ).select_related('category')[:20]
    
    results = []
    for medicine in medicines:
        # Get available quantity from batches
        available_batches = medicine.batches.filter(
            is_active=True,
            remaining_quantity__gt=0,
            expiry_date__gt=timezone.now().date()
        ).aggregate(total=Sum('remaining_quantity'))
        
        results.append({
            'id': medicine.id,
            'name': medicine.name,
            'generic_name': medicine.generic_name,
            'strength': medicine.strength,
            'form': medicine.form,
            'sku': medicine.sku,
            'price': float(medicine.selling_price),
            'unit_price': float(medicine.unit_price),
            'stock': available_batches['total'] or 0,
            'category': medicine.category.name if medicine.category else '',
            'requires_prescription': medicine.requires_prescription,
            'image_url': medicine.image.url if medicine.image else None,
        })
    
    return JsonResponse({'results': results})


@login_required
@transaction.atomic
def process_sale(request):
    """Process a sale transaction"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid request method'})
    
    if not request.user.can_process_sales:
        return JsonResponse({'success': False, 'error': 'Permission denied'})
    
    try:
        # Parse request data
        data = json.loads(request.body)
        
        customer_id = data.get('customer_id')
        prescription_id = data.get('prescription_id')
        payment_method = data.get('payment_method', 'cash')
        amount_paid = Decimal(str(data.get('amount_paid', 0)))
        discount_percentage = Decimal(str(data.get('discount_percentage', 0)))
        notes = data.get('notes', '')
        cart_items = data.get('cart_items', [])
        
        # Validate cart
        if not cart_items:
            return JsonResponse({'success': False, 'error': 'Cart is empty'})
        
        # Create sale
        sale = Sale.objects.create(
            customer_id=customer_id if customer_id else None,
            prescription_id=prescription_id if prescription_id else None,
            payment_method=payment_method,
            discount_percentage=discount_percentage,
            amount_paid=amount_paid,
            notes=notes,
            served_by=request.user,
            status='completed'
        )
        
        subtotal = Decimal('0')
        total_cost = Decimal('0')
        
        # Process each item
        for item_data in cart_items:
            medicine_id = item_data['medicine_id']
            quantity = int(item_data['quantity'])
            
            # Get medicine
            medicine = Medicine.objects.select_for_update().get(id=medicine_id)
            
            # Check stock availability
            if medicine.total_quantity < quantity:
                raise ValueError(f'Insufficient stock for {medicine.name}. Available: {medicine.total_quantity}')
            
            # Get oldest non-expired batch (FIFO)
            batch = medicine.batches.filter(
                is_active=True,
                remaining_quantity__gte=quantity,
                expiry_date__gt=timezone.now().date()
            ).order_by('expiry_date').first()
            
            if not batch:
                # Try to fulfill from multiple batches
                batches = medicine.batches.filter(
                    is_active=True,
                    remaining_quantity__gt=0,
                    expiry_date__gt=timezone.now().date()
                ).order_by('expiry_date')
                
                remaining_qty = quantity
                for b in batches:
                    if remaining_qty <= 0:
                        break
                    
                    qty_from_batch = min(b.remaining_quantity, remaining_qty)
                    
                    # Create sale item for this portion
                    SaleItem.objects.create(
                        sale=sale,
                        medicine=medicine,
                        batch=b,
                        quantity=qty_from_batch,
                        unit_price=medicine.selling_price,
                        unit_cost=b.unit_cost
                    )
                    
                    # Update batch
                    b.remaining_quantity -= qty_from_batch
                    b.save()
                    
                    remaining_qty -= qty_from_batch
                
                if remaining_qty > 0:
                    raise ValueError(f'Insufficient stock for {medicine.name}')
            else:
                # Create sale item
                sale_item = SaleItem.objects.create(
                    sale=sale,
                    medicine=medicine,
                    batch=batch,
                    quantity=quantity,
                    unit_price=medicine.selling_price,
                    unit_cost=batch.unit_cost
                )
                
                # Update batch
                batch.remaining_quantity -= quantity
                batch.save()
            
            # Update medicine total quantity
            medicine.total_quantity -= quantity
            medicine.save()
        
        # Calculate totals
        sale.subtotal = sale.items.aggregate(total=Sum('total_price'))['total'] or Decimal('0')
        sale.save()  # This triggers automatic calculation of tax and total
        
        # Update customer stats if customer exists
        if sale.customer:
            sale.customer.total_purchases += sale.total_amount
            sale.customer.loyalty_points += int(sale.total_amount / 100)  # 1 point per 100
            sale.customer.save()
        
        # Update prescription status if linked
        if sale.prescription:
            sale.prescription.status = 'filled'
            sale.prescription.filled_by = request.user
            sale.prescription.filled_at = timezone.now()
            sale.prescription.save()
        
        # Log activity
        UserActivity.objects.create(
            user=request.user,
            action='sale',
            description=f'Processed sale: {sale.invoice_number}'
        )
        
        return JsonResponse({
            'success': True,
            'invoice_number': sale.invoice_number,
            'sale_id': sale.id,
            'total_amount': float(sale.total_amount),
            'change_amount': float(sale.change_amount),
            'subtotal': float(sale.subtotal),
            'discount_amount': float(sale.discount_amount),
            'tax_amount': float(sale.tax_amount),
        })
        
    except Medicine.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Medicine not found'})
    except ValueError as e:
        return JsonResponse({'success': False, 'error': str(e)})
    except Exception as e:
        return JsonResponse({'success': False, 'error': f'Error processing sale: {str(e)}'})


@login_required
def sale_receipt(request, sale_id):
    """View/Print sale receipt"""
    sale = get_object_or_404(
        Sale.objects.select_related('customer', 'served_by', 'prescription')
        .prefetch_related('items__medicine', 'items__batch'),
        id=sale_id
    )
    
    context = {
        'sale': sale,
    }
    
    return render(request, 'sales/receipt.html', context)


@login_required
def sales_list(request):
    """List all sales with filters"""
    sales = Sale.objects.select_related('customer', 'served_by').order_by('-sale_date')
    
    # Date filter
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    if start_date and end_date:
        sales = sales.filter(sale_date__date__range=[start_date, end_date])
    elif start_date:
        sales = sales.filter(sale_date__date__gte=start_date)
    elif end_date:
        sales = sales.filter(sale_date__date__lte=end_date)
    
    # Quick filters
    date_filter = request.GET.get('date_filter')
    today = timezone.now().date()
    
    if date_filter == 'today':
        sales = sales.filter(sale_date__date=today)
    elif date_filter == 'yesterday':
        sales = sales.filter(sale_date__date=today - timedelta(days=1))
    elif date_filter == 'week':
        sales = sales.filter(sale_date__date__gte=today - timedelta(days=7))
    elif date_filter == 'month':
        sales = sales.filter(sale_date__date__gte=today.replace(day=1))
    
    # Payment method filter
    payment_method = request.GET.get('payment_method')
    if payment_method:
        sales = sales.filter(payment_method=payment_method)
    
    # Status filter
    status = request.GET.get('status')
    if status:
        sales = sales.filter(status=status)
    
    # Customer filter
    customer_id = request.GET.get('customer')
    if customer_id:
        sales = sales.filter(customer_id=customer_id)
    
    # Search by invoice number
    search = request.GET.get('search')
    if search:
        sales = sales.filter(invoice_number__icontains=search)
    
    # Calculate totals
    totals = sales.aggregate(
        total_sales=Sum('total_amount'),
        total_profit=Sum(F('total_amount') - Sum('items__total_cost')),
        count=Count('id')
    )
    
    # Pagination
    paginator = Paginator(sales, 25)
    page_number = request.GET.get('page')
    sales_page = paginator.get_page(page_number)
    
    context = {
        'sales': sales_page,
        'totals': totals,
        'payment_methods': Sale.PAYMENT_METHOD_CHOICES,
        'status_choices': Sale.STATUS_CHOICES,
        'start_date': start_date,
        'end_date': end_date,
        'date_filter': date_filter,
        'payment_method': payment_method,
        'status': status,
    }
    
    return render(request, 'sales/sales_list.html', context)


@login_required
def sale_detail(request, sale_id):
    """View sale details"""
    sale = get_object_or_404(
        Sale.objects.select_related('customer', 'served_by', 'prescription')
        .prefetch_related('items__medicine', 'items__batch'),
        id=sale_id
    )
    
    context = {
        'sale': sale,
    }
    
    return render(request, 'sales/sale_detail.html', context)


@login_required
@transaction.atomic
def process_return(request, sale_id):
    """Process a product return/refund"""
    sale = get_object_or_404(Sale, id=sale_id)
    
    if request.method == 'POST':
        try:
            reason = request.POST['reason']
            notes = request.POST.get('notes', '')
            refund_method = request.POST.get('refund_method', sale.payment_method)
            
            # Get items to return
            items_to_return = request.POST.getlist('items[]')
            quantities = request.POST.getlist('quantities[]')
            
            if not items_to_return:
                messages.error(request, 'No items selected for return')
                return redirect('sales:sale_detail', sale_id=sale_id)
            
            # Create return record
            return_record = Return.objects.create(
                original_sale=sale,
                customer=sale.customer,
                reason=reason,
                notes=notes,
                refund_method=refund_method,
                processed_by=request.user
            )
            
            refund_amount = Decimal('0')
            
            # Process each item
            for item_id, quantity_str in zip(items_to_return, quantities):
                sale_item = SaleItem.objects.get(id=item_id)
                quantity = int(quantity_str)
                
                if quantity > sale_item.quantity:
                    raise ValueError(f'Return quantity exceeds sold quantity for {sale_item.medicine.name}')
                
                # Create return item
                return_item = ReturnItem.objects.create(
                    return_record=return_record,
                    sale_item=sale_item,
                    medicine=sale_item.medicine,
                    quantity=quantity,
                    unit_price=sale_item.unit_price,
                    restock=request.POST.get(f'restock_{item_id}') == 'on'
                )
                
                refund_amount += return_item.total_refund
                
                # Restock if requested
                if return_item.restock:
                    medicine = sale_item.medicine
                    medicine.total_quantity += quantity
                    medicine.save()
                    
                    if sale_item.batch:
                        batch = sale_item.batch
                        batch.remaining_quantity += quantity
                        batch.save()
            
            # Update return record
            return_record.refund_amount = refund_amount
            return_record.save()
            
            # Update sale status
            sale.status = 'refunded'
            sale.save()
            
            # Log activity
            UserActivity.objects.create(
                user=request.user,
                action='update',
                description=f'Processed return: {return_record.return_number}'
            )
            
            messages.success(request, f'Return processed successfully! Refund: {refund_amount}')
            return redirect('sales:sale_detail', sale_id=sale_id)
            
        except Exception as e:
            messages.error(request, f'Error processing return: {str(e)}')
    
    context = {
        'sale': sale,
        'return_reasons': Return.REASON_CHOICES,
    }
    
    return render(request, 'sales/return_form.html', context)


@login_required
def returns_list(request):
    """List all returns"""
    returns = Return.objects.select_related(
        'original_sale', 'customer', 'processed_by'
    ).order_by('-return_date')
    
    # Date filter
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    if start_date and end_date:
        returns = returns.filter(return_date__date__range=[start_date, end_date])
    
    # Reason filter
    reason = request.GET.get('reason')
    if reason:
        returns = returns.filter(reason=reason)
    
    # Pagination
    paginator = Paginator(returns, 20)
    page_number = request.GET.get('page')
    returns_page = paginator.get_page(page_number)
    
    # Calculate total refunds
    total_refunds = returns.aggregate(total=Sum('refund_amount'))['total'] or Decimal('0')
    
    context = {
        'returns': returns_page,
        'total_refunds': total_refunds,
        'return_reasons': Return.REASON_CHOICES,
        'reason': reason,
    }
    
    return render(request, 'sales/returns_list.html', context)


@login_required
def get_customer_info(request, customer_id):
    """AJAX endpoint to get customer info"""
    try:
        customer = Customer.objects.get(id=customer_id)
        return JsonResponse({
            'success': True,
            'customer': {
                'id': customer.id,
                'name': customer.full_name,
                'phone': customer.phone,
                'email': customer.email,
                'loyalty_points': customer.loyalty_points,
                'allergies': customer.allergies,
            }
        })
    except Customer.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Customer not found'})