from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Sum, Count
from django.core.paginator import Paginator

from .models import Supplier, PurchaseOrder, PurchaseOrderItem
from inventory.models import Medicine


@login_required
def supplier_list(request):
    """List all suppliers"""
    suppliers = Supplier.objects.all()
    
    # Search
    search = request.GET.get('search')
    if search:
        suppliers = suppliers.filter(
            Q(company_name__icontains=search) |
            Q(supplier_code__icontains=search) |
            Q(contact_person__icontains=search)
        )
    
    # Filter by status
    status = request.GET.get('status')
    if status:
        suppliers = suppliers.filter(is_active=status == 'active')
    
    # Pagination
    paginator = Paginator(suppliers, 20)
    page_number = request.GET.get('page')
    suppliers_page = paginator.get_page(page_number)
    
    context = {
        'suppliers': suppliers_page,
        'search': search,
        'status': status,
    }
    
    return render(request, 'suppliers/supplier_list.html', context)


@login_required
def supplier_detail(request, pk):
    """View supplier details"""
    supplier = get_object_or_404(Supplier, pk=pk)
    
    # Get purchase orders
    purchase_orders = supplier.purchase_orders.all().order_by('-created_at')[:10]
    
    # Get supplied batches
    from inventory.models import Batch
    batches = Batch.objects.filter(supplier=supplier).select_related('medicine')[:10]
    
    # Statistics
    total_orders = supplier.purchase_orders.count()
    total_spent = supplier.purchase_orders.filter(
        status='received'
    ).aggregate(total=Sum('total_amount'))['total'] or 0
    
    context = {
        'supplier': supplier,
        'purchase_orders': purchase_orders,
        'batches': batches,
        'total_orders': total_orders,
        'total_spent': total_spent,
    }
    
    return render(request, 'suppliers/supplier_detail.html', context)


@login_required
def supplier_create(request):
    """Create new supplier"""
    if request.method == 'POST':
        try:
            supplier = Supplier.objects.create(
                company_name=request.POST['company_name'],
                contact_person=request.POST['contact_person'],
                email=request.POST['email'],
                phone=request.POST['phone'],
                alternate_phone=request.POST.get('alternate_phone', ''),
                website=request.POST.get('website', ''),
                address_line1=request.POST['address_line1'],
                address_line2=request.POST.get('address_line2', ''),
                city=request.POST['city'],
                state=request.POST.get('state', ''),
                postal_code=request.POST.get('postal_code', ''),
                country=request.POST.get('country', 'Kenya'),
                tax_id=request.POST.get('tax_id', ''),
                license_number=request.POST.get('license_number', ''),
                payment_terms=request.POST.get('payment_terms', ''),
                rating=int(request.POST.get('rating', 5)),
                notes=request.POST.get('notes', ''),
                created_by=request.user
            )
            
            messages.success(request, 'Supplier created successfully!')
            return redirect('suppliers:supplier_detail', pk=supplier.pk)
            
        except Exception as e:
            messages.error(request, f'Error creating supplier: {str(e)}')
    
    return render(request, 'suppliers/supplier_form.html')


