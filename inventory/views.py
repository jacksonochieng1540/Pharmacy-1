from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Sum, F, Count
from django.http import JsonResponse, HttpResponse
from django.core.paginator import Paginator
from datetime import date, timedelta
from decimal import Decimal

from .models import Category, Medicine, Batch, StockAdjustment
from apps.accounts.models import UserActivity


@login_required
def medicine_list(request):
    """List all medicines with filtering and search"""
    medicines = Medicine.objects.select_related('category').prefetch_related('batches')
    
    # Search
    search_query = request.GET.get('search')
    if search_query:
        medicines = medicines.filter(
            Q(name__icontains=search_query) |
            Q(generic_name__icontains=search_query) |
            Q(sku__icontains=search_query) |
            Q(barcode__icontains=search_query)
        )
    
    # Filter by category
    category_id = request.GET.get('category')
    if category_id:
        medicines = medicines.filter(category_id=category_id)
    
    # Filter by form
    form_filter = request.GET.get('form')
    if form_filter:
        medicines = medicines.filter(form=form_filter)
    
    # Filter by stock status
    stock_filter = request.GET.get('stock')
    if stock_filter == 'low':
        medicines = medicines.filter(total_quantity__lte=F('reorder_level'))
    elif stock_filter == 'out':
        medicines = medicines.filter(total_quantity=0)
    
    # Filter by active status
    active_filter = request.GET.get('active')
    if active_filter:
        medicines = medicines.filter(is_active=active_filter == 'true')
    
    # Ordering
    order_by = request.GET.get('order_by', '-created_at')
    medicines = medicines.order_by(order_by)
    
    # Pagination
    paginator = Paginator(medicines, 20)
    page_number = request.GET.get('page')
    medicines_page = paginator.get_page(page_number)
    
    # Get all categories for filter dropdown
    categories = Category.objects.all()
    
    # Get form choices
    form_choices = Medicine.FORM_CHOICES
    
    context = {
        'medicines': medicines_page,
        'categories': categories,
        'form_choices': form_choices,
        'search_query': search_query,
        'category_id': category_id,
        'form_filter': form_filter,
        'stock_filter': stock_filter,
        'active_filter': active_filter,
    }
    
    return render(request, 'inventory/medicine_list.html', context)


@login_required
def medicine_detail(request, pk):
    """View medicine details"""
    medicine = get_object_or_404(
        Medicine.objects.select_related('category', 'created_by')
        .prefetch_related('batches__supplier'),
        pk=pk
    )
    
    # Get all batches for this medicine
    batches = medicine.batches.all().order_by('expiry_date')
    
    # Get recent stock adjustments
    adjustments = StockAdjustment.objects.filter(
        medicine=medicine
    ).select_related('adjusted_by').order_by('-adjusted_at')[:10]
    
    # Calculate statistics
    total_batches = batches.count()
    active_batches = batches.filter(is_active=True, remaining_quantity__gt=0).count()
    expired_batches = batches.filter(is_expired=True).count()
    
    # Expiring soon (within 90 days)
    expiry_threshold = date.today() + timedelta(days=90)
    expiring_batches = batches.filter(
        expiry_date__lte=expiry_threshold,
        expiry_date__gt=date.today(),
        is_active=True
    ).count()
    
    context = {
        'medicine': medicine,
        'batches': batches,
        'adjustments': adjustments,
        'total_batches': total_batches,
        'active_batches': active_batches,
        'expired_batches': expired_batches,
        'expiring_batches': expiring_batches,
    }
    
    return render(request, 'inventory/medicine_detail.html', context)


@login_required
def medicine_create(request):
    """Create new medicine"""
    if not request.user.can_manage_inventory:
        messages.error(request, 'You do not have permission to add medicines.')
        return redirect('inventory:medicine_list')
    
    if request.method == 'POST':
        try:
            # Get form data
            medicine = Medicine.objects.create(
                name=request.POST['name'],
                generic_name=request.POST.get('generic_name', ''),
                category_id=request.POST.get('category'),
                manufacturer=request.POST['manufacturer'],
                form=request.POST['form'],
                strength=request.POST['strength'],
                sku=request.POST['sku'],
                barcode=request.POST.get('barcode', ''),
                unit_price=Decimal(request.POST['unit_price']),
                selling_price=Decimal(request.POST['selling_price']),
                reorder_level=int(request.POST.get('reorder_level', 20)),
                description=request.POST.get('description', ''),
                side_effects=request.POST.get('side_effects', ''),
                storage_conditions=request.POST.get('storage_conditions', ''),
                requires_prescription=request.POST.get('requires_prescription') == 'on',
                is_active=True,
                created_by=request.user
            )
            
            # Handle image upload
            if 'image' in request.FILES:
                medicine.image = request.FILES['image']
                medicine.save()
            
            # Log activity
            UserActivity.objects.create(
                user=request.user,
                action='create',
                description=f'Created medicine: {medicine.name}'
            )
            
            messages.success(request, f'Medicine "{medicine.name}" created successfully!')
            return redirect('inventory:medicine_detail', pk=medicine.pk)
            
        except Exception as e:
            messages.error(request, f'Error creating medicine: {str(e)}')
    
    categories = Category.objects.all()
    form_choices = Medicine.FORM_CHOICES
    
    context = {
        'categories': categories,
        'form_choices': form_choices,
    }
    
    return render(request, 'inventory/medicine_form.html', context)


@login_required
def medicine_edit(request, pk):
    """Edit existing medicine"""
    medicine = get_object_or_404(Medicine, pk=pk)
    
    if not request.user.can_manage_inventory:
        messages.error(request, 'You do not have permission to edit medicines.')
        return redirect('inventory:medicine_detail', pk=pk)
    
    if request.method == 'POST':
        try:
            # Update fields
            medicine.name = request.POST['name']
            medicine.generic_name = request.POST.get('generic_name', '')
            medicine.category_id = request.POST.get('category')
            medicine.manufacturer = request.POST['manufacturer']
            medicine.form = request.POST['form']
            medicine.strength = request.POST['strength']
            medicine.sku = request.POST['sku']
            medicine.barcode = request.POST.get('barcode', '')
            medicine.unit_price = Decimal(request.POST['unit_price'])
            medicine.selling_price = Decimal(request.POST['selling_price'])
            medicine.reorder_level = int(request.POST.get('reorder_level', 20))
            medicine.description = request.POST.get('description', '')
            medicine.side_effects = request.POST.get('side_effects', '')
            medicine.storage_conditions = request.POST.get('storage_conditions', '')
            medicine.requires_prescription = request.POST.get('requires_prescription') == 'on'
            medicine.is_active = request.POST.get('is_active') == 'on'
            
            # Handle image upload
            if 'image' in request.FILES:
                medicine.image = request.FILES['image']
            
            medicine.save()
            
            # Log activity
            UserActivity.objects.create(
                user=request.user,
                action='update',
                description=f'Updated medicine: {medicine.name}'
            )
            
            messages.success(request, 'Medicine updated successfully!')
            return redirect('inventory:medicine_detail', pk=pk)
            
        except Exception as e:
            messages.error(request, f'Error updating medicine: {str(e)}')
    
    categories = Category.objects.all()
    form_choices = Medicine.FORM_CHOICES
    
    context = {
        'medicine': medicine,
        'categories': categories,
        'form_choices': form_choices,
        'is_edit': True,
    }
    
    return render(request, 'inventory/medicine_form.html', context)


@login_required
def batch_create(request, medicine_id):
    """Add new batch for a medicine"""
    medicine = get_object_or_404(Medicine, pk=medicine_id)
    
    if not request.user.can_manage_inventory:
        messages.error(request, 'You do not have permission to add batches.')
        return redirect('inventory:medicine_detail', pk=medicine_id)
    
    if request.method == 'POST':
        try:
            quantity = int(request.POST['quantity'])
            
            batch = Batch.objects.create(
                medicine=medicine,
                batch_number=request.POST['batch_number'],
                supplier_id=request.POST.get('supplier'),
                quantity=quantity,
                remaining_quantity=quantity,
                unit_cost=Decimal(request.POST['unit_cost']),
                selling_price=Decimal(request.POST['selling_price']),
                manufacture_date=request.POST['manufacture_date'],
                expiry_date=request.POST['expiry_date'],
                notes=request.POST.get('notes', ''),
                created_by=request.user
            )
            
            # Update medicine total quantity
            medicine.total_quantity += quantity
            medicine.save()
            
            # Log activity
            UserActivity.objects.create(
                user=request.user,
                action='create',
                description=f'Added batch {batch.batch_number} for {medicine.name}'
            )
            
            messages.success(request, f'Batch added successfully! Stock updated.')
            return redirect('inventory:medicine_detail', pk=medicine_id)
            
        except Exception as e:
            messages.error(request, f'Error adding batch: {str(e)}')
    
    from apps.suppliers.models import Supplier
    suppliers = Supplier.objects.filter(is_active=True)
    
    context = {
        'medicine': medicine,
        'suppliers': suppliers,
    }
    
    return render(request, 'inventory/batch_form.html', context)


@login_required
def stock_adjustment(request, medicine_id):
    """Adjust stock quantity"""
    medicine = get_object_or_404(Medicine, pk=medicine_id)
    
    if not request.user.can_manage_inventory:
        messages.error(request, 'You do not have permission to adjust stock.')
        return redirect('inventory:medicine_detail', pk=medicine_id)
    
    if request.method == 'POST':
        try:
            adjustment_type = request.POST['adjustment_type']
            quantity = int(request.POST['quantity'])
            reason = request.POST['reason']
            batch_id = request.POST.get('batch')
            
            # Create adjustment record
            adjustment = StockAdjustment.objects.create(
                medicine=medicine,
                batch_id=batch_id if batch_id else None,
                adjustment_type=adjustment_type,
                quantity=quantity if adjustment_type != 'damaged' else -abs(quantity),
                reason=reason,
                adjusted_by=request.user
            )
            
            # Update stock
            if adjustment_type in ['damaged', 'expired', 'lost', 'return']:
                # Reduce stock
                medicine.total_quantity = max(0, medicine.total_quantity - abs(quantity))
                if batch_id:
                    batch = Batch.objects.get(pk=batch_id)
                    batch.remaining_quantity = max(0, batch.remaining_quantity - abs(quantity))
                    batch.save()
            else:
                # Add stock (correction)
                medicine.total_quantity += abs(quantity)
                if batch_id:
                    batch = Batch.objects.get(pk=batch_id)
                    batch.remaining_quantity += abs(quantity)
                    batch.save()
            
            medicine.save()
            
            # Log activity
            UserActivity.objects.create(
                user=request.user,
                action='update',
                description=f'Stock adjustment: {medicine.name} ({adjustment_type})'
            )
            
            messages.success(request, 'Stock adjusted successfully!')
            return redirect('inventory:medicine_detail', pk=medicine_id)
            
        except Exception as e:
            messages.error(request, f'Error adjusting stock: {str(e)}')
    
    batches = medicine.batches.filter(is_active=True, remaining_quantity__gt=0)
    adjustment_types = StockAdjustment.REASON_CHOICES
    
    context = {
        'medicine': medicine,
        'batches': batches,
        'adjustment_types': adjustment_types,
    }
    
    return render(request, 'inventory/stock_adjustment.html', context)


@login_required
def low_stock_alert(request):
    """View medicines with low stock"""
    low_stock_medicines = Medicine.objects.filter(
        total_quantity__lte=F('reorder_level'),
        is_active=True
    ).select_related('category').order_by('total_quantity')
    
    context = {
        'medicines': low_stock_medicines,
    }
    
    return render(request, 'inventory/low_stock.html', context)


@login_required
def expiring_medicines(request):
    """View expiring and expired medicines"""
    today = date.today()
    expiry_threshold = today + timedelta(days=90)
    
    # Expiring soon
    expiring_batches = Batch.objects.filter(
        expiry_date__lte=expiry_threshold,
        expiry_date__gt=today,
        is_active=True
    ).select_related('medicine', 'supplier').order_by('expiry_date')
    
    # Already expired
    expired_batches = Batch.objects.filter(
        expiry_date__lte=today,
        is_active=True
    ).select_related('medicine', 'supplier').order_by('-expiry_date')
    
    context = {
        'expiring_batches': expiring_batches,
        'expired_batches': expired_batches,
    }
    
    return render(request, 'inventory/expiring.html', context)


@login_required
def categories_list(request):
    """List all categories"""
    categories = Category.objects.annotate(
        medicine_count=Count('medicines')
    ).order_by('name')
    
    context = {
        'categories': categories,
    }
    
    return render(request, 'inventory/categories.html', context)