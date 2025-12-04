from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.core.paginator import Paginator

from .models import Doctor, Prescription, PrescriptionItem
from apps.customers.models import Customer
from apps.inventory.models import Medicine


@login_required
def prescription_list(request):
    """List all prescriptions"""
    prescriptions = Prescription.objects.select_related(
        'customer', 'doctor', 'created_by'
    ).order_by('-created_at')
    
    # Filter by status
    status = request.GET.get('status')
    if status:
        prescriptions = prescriptions.filter(status=status)
    
    # Search
    search = request.GET.get('search')
    if search:
        prescriptions = prescriptions.filter(
            Q(prescription_number__icontains=search) |
            Q(customer__first_name__icontains=search) |
            Q(customer__last_name__icontains=search)
        )
    
    # Pagination
    paginator = Paginator(prescriptions, 20)
    page_number = request.GET.get('page')
    prescriptions_page = paginator.get_page(page_number)
    
    context = {
        'prescriptions': prescriptions_page,
        'status': status,
        'search': search,
        'status_choices': Prescription.STATUS_CHOICES,
    }
    
    return render(request, 'prescriptions/prescription_list.html', context)


@login_required
def prescription_detail(request, pk):
    """View prescription details"""
    prescription = get_object_or_404(
        Prescription.objects.select_related('customer', 'doctor', 'filled_by')
        .prefetch_related('items__medicine'),
        pk=pk
    )
    
    context = {
        'prescription': prescription,
    }
    
    return render(request, 'prescriptions/prescription_detail.html', context)


@login_required
def prescription_create(request):
    """Create new prescription"""
    if request.method == 'POST':
        try:
            prescription = Prescription.objects.create(
                customer_id=request.POST['customer'],
                doctor_id=request.POST['doctor'],
                prescription_date=request.POST['prescription_date'],
                valid_until=request.POST['valid_until'],
                diagnosis=request.POST.get('diagnosis', ''),
                notes=request.POST.get('notes', ''),
                created_by=request.user
            )
            
            # Handle prescription image upload
            if 'prescription_image' in request.FILES:
                prescription.prescription_image = request.FILES['prescription_image']
                prescription.save()
            
            messages.success(request, 'Prescription created successfully!')
            return redirect('prescriptions:prescription_detail', pk=prescription.pk)
            
        except Exception as e:
            messages.error(request, f'Error creating prescription: {str(e)}')
    
    customers = Customer.objects.filter(is_active=True)
    doctors = Doctor.objects.filter(is_active=True)
    
    context = {
        'customers': customers,
        'doctors': doctors,
    }
    
    return render(request, 'prescriptions/prescription_form.html', context)


@login_required
def doctor_list(request):
    """List all doctors"""
    doctors = Doctor.objects.all().order_by('last_name', 'first_name')
    
    # Search
    search = request.GET.get('search')
    if search:
        doctors = doctors.filter(
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search) |
            Q(specialization__icontains=search) |
            Q(license_number__icontains=search)
        )
    
    context = {
        'doctors': doctors,
        'search': search,
    }
    
    return render(request, 'prescriptions/doctor_list.html', context)