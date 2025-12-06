from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Sum
from django.core.paginator import Paginator
from django.http import JsonResponse

from .models import Customer, CustomerInsurance
from apps.sales.models import Sale
from apps.accounts.models import UserActivity


@login_required
def customer_list(request):
    """List all customers"""
    customers = Customer.objects.all()
    
    
    search = request.GET.get('search')
    if search:
        customers = customers.filter(
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search) |
            Q(phone__icontains=search) |
            Q(email__icontains=search) |
            Q(customer_id__icontains=search)
        )
    
    
    status = request.GET.get('status')
    if status:
        customers = customers.filter(is_active=status == 'active')
    
    
    order_by = request.GET.get('order_by', '-created_at')
    customers = customers.order_by(order_by)
    
    
    paginator = Paginator(customers, 20)
    page_number = request.GET.get('page')
    customers_page = paginator.get_page(page_number)
    
    context = {
        'customers': customers_page,
        'search': search,
        'status': status,
    }
    
    return render(request, 'customers/customer_list.html', context)


@login_required
def customer_detail(request, pk):
    """View customer details"""
    customer = get_object_or_404(Customer, pk=pk)
    
    
    sales = Sale.objects.filter(customer=customer).order_by('-sale_date')[:10]

    
    insurances = customer.insurances.all()
    
    
    total_spent = Sale.objects.filter(
        customer=customer, status='completed'
    ).aggregate(total=Sum('total_amount'))['total'] or 0
    
    total_orders = Sale.objects.filter(customer=customer).count()
    
    context = {
        'customer': customer,
        'sales': sales,
        'insurances': insurances,
        'total_spent': total_spent,
        'total_orders': total_orders,
    }
    
    return render(request, 'customers/customer_detail.html', context)


@login_required
def customer_create(request):
    """Create new customer"""
    if request.method == 'POST':
        try:
            customer = Customer.objects.create(
                first_name=request.POST['first_name'],
                last_name=request.POST['last_name'],
                email=request.POST.get('email', ''),
                phone=request.POST['phone'],
                alternate_phone=request.POST.get('alternate_phone', ''),
                date_of_birth=request.POST.get('date_of_birth') or None,
                gender=request.POST.get('gender', ''),
                address_line1=request.POST['address_line1'],
                address_line2=request.POST.get('address_line2', ''),
                city=request.POST['city'],
                state=request.POST.get('state', ''),
                postal_code=request.POST.get('postal_code', ''),
                country=request.POST.get('country', 'Kenya'),
                allergies=request.POST.get('allergies', ''),
                medical_conditions=request.POST.get('medical_conditions', ''),
                blood_group=request.POST.get('blood_group', ''),
                notes=request.POST.get('notes', ''),
            )
            
            UserActivity.objects.create(
                user=request.user,
                action='create',
                description=f'Created customer: {customer.full_name}'
            )
            
            messages.success(request, 'Customer created successfully!')
            return redirect('customers:customer_detail', pk=customer.pk)
            
        except Exception as e:
            messages.error(request, f'Error creating customer: {str(e)}')
    
    context = {
        'gender_choices': Customer.GENDER_CHOICES,
    }
    
    return render(request, 'customers/customer_form.html', context)


@login_required
def customer_edit(request, pk):
    """Edit customer"""
    customer = get_object_or_404(Customer, pk=pk)
    
    if request.method == 'POST':
        try:
            customer.first_name = request.POST['first_name']
            customer.last_name = request.POST['last_name']
            customer.email = request.POST.get('email', '')
            customer.phone = request.POST['phone']
            customer.alternate_phone = request.POST.get('alternate_phone', '')
            customer.date_of_birth = request.POST.get('date_of_birth') or None
            customer.gender = request.POST.get('gender', '')
            customer.address_line1 = request.POST['address_line1']
            customer.address_line2 = request.POST.get('address_line2', '')
            customer.city = request.POST['city']
            customer.state = request.POST.get('state', '')
            customer.postal_code = request.POST.get('postal_code', '')
            customer.country = request.POST.get('country', 'Kenya')
            customer.allergies = request.POST.get('allergies', '')
            customer.medical_conditions = request.POST.get('medical_conditions', '')
            customer.blood_group = request.POST.get('blood_group', '')
            customer.notes = request.POST.get('notes', '')
            customer.is_active = request.POST.get('is_active') == 'on'
            
            customer.save()
            
            UserActivity.objects.create(
                user=request.user,
                action='update',
                description=f'Updated customer: {customer.full_name}'
            )
            
            messages.success(request, 'Customer updated successfully!')
            return redirect('customers:customer_detail', pk=pk)
            
        except Exception as e:
            messages.error(request, f'Error updating customer: {str(e)}')
    
    context = {
        'customer': customer,
        'gender_choices': Customer.GENDER_CHOICES,
        'is_edit': True,
    }
    
    return render(request, 'customers/customer_form.html', context)

