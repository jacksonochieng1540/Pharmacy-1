from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Count, Sum, Q
from django.utils import timezone
from datetime import datetime, timedelta
from decimal import Decimal

from .models import User, UserActivity
from inventory.models import Medicine, Batch
from sales.models import Sale, SaleItem
from customers.models import Customer
from notifications.models import Notification


def login_view(request):
    """User login view"""
    if request.user.is_authenticated:
        return redirect('accounts:dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        remember_me = request.POST.get('remember_me')
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            if user.is_active_employee:
                login(request, user)
                
                # Set session expiry
                if not remember_me:
                    request.session.set_expiry(0)  # Session expires on browser close
                
                # Log activity
                UserActivity.objects.create(
                    user=user,
                    action='login',
                    description=f'{user.username} logged in',
                    ip_address=get_client_ip(request),
                    user_agent=request.META.get('HTTP_USER_AGENT', '')[:200]
                )
                
                messages.success(request, f'Welcome back, {user.get_full_name()}!')
                
                # Redirect to next or dashboard
                next_url = request.GET.get('next', 'accounts:dashboard')
                return redirect(next_url)
            else:
                messages.error(request, 'Your account has been deactivated.')
        else:
            messages.error(request, 'Invalid username or password.')
    
    return render(request, 'accounts/login.html')


@login_required
def logout_view(request):
    """User logout view"""
    # Log activity
    UserActivity.objects.create(
        user=request.user,
        action='logout',
        description=f'{request.user.username} logged out',
        ip_address=get_client_ip(request)
    )
    
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('accounts:login')


@login_required
def dashboard(request):
    """Main dashboard view"""
    today = timezone.now().date()
    week_ago = today - timedelta(days=7)
    month_start = today.replace(day=1)
    
    # Sales Statistics
    today_sales = Sale.objects.filter(
        sale_date__date=today,
        status='completed'
    ).aggregate(
        total=Sum('total_amount'),
        count=Count('id')
    )
    
    week_sales = Sale.objects.filter(
        sale_date__date__gte=week_ago,
        status='completed'
    ).aggregate(
        total=Sum('total_amount'),
        count=Count('id')
    )
    
    month_sales = Sale.objects.filter(
        sale_date__date__gte=month_start,
        status='completed'
    ).aggregate(
        total=Sum('total_amount'),
        count=Count('id')
    )
    
    # Inventory Statistics
    total_medicines = Medicine.objects.filter(is_active=True).count()
    low_stock_count = Medicine.objects.filter(
        total_quantity__lte=F('reorder_level'),
        is_active=True
    ).count()
    
    # Expiring medicines (within 90 days)
    expiry_threshold = today + timedelta(days=90)
    expiring_batches = Batch.objects.filter(
        expiry_date__lte=expiry_threshold,
        expiry_date__gt=today,
        is_active=True
    ).count()
    
    expired_batches = Batch.objects.filter(
        expiry_date__lte=today,
        is_active=True
    ).count()
    
    # Customer Statistics
    total_customers = Customer.objects.filter(is_active=True).count()
    new_customers_month = Customer.objects.filter(
        created_at__date__gte=month_start
    ).count()
    
    # Recent Sales (last 5)
    recent_sales = Sale.objects.filter(
        status='completed'
    ).select_related('customer', 'served_by').order_by('-sale_date')[:5]
    
    # Unread Notifications
    unread_notifications = Notification.objects.filter(
        Q(recipients=request.user) | Q(recipients__isnull=True),
        is_read=False
    ).order_by('-created_at')[:5]
    
    # Low Stock Items (top 5 critical)
    low_stock_items = Medicine.objects.filter(
        total_quantity__lte=F('reorder_level'),
        is_active=True
    ).order_by('total_quantity')[:5]
    
    # Top Selling Products (this month)
    top_products = SaleItem.objects.filter(
        sale__sale_date__date__gte=month_start,
        sale__status='completed'
    ).values(
        'medicine__name', 'medicine__id'
    ).annotate(
        total_quantity=Sum('quantity'),
        total_revenue=Sum('total_price')
    ).order_by('-total_quantity')[:5]
    
    context = {
        # Sales Stats
        'today_sales_total': today_sales['total'] or Decimal('0'),
        'today_sales_count': today_sales['count'] or 0,
        'week_sales_total': week_sales['total'] or Decimal('0'),
        'week_sales_count': week_sales['count'] or 0,
        'month_sales_total': month_sales['total'] or Decimal('0'),
        'month_sales_count': month_sales['count'] or 0,
        
        # Inventory Stats
        'total_medicines': total_medicines,
        'low_stock_count': low_stock_count,
        'expiring_batches': expiring_batches,
        'expired_batches': expired_batches,
        
        # Customer Stats
        'total_customers': total_customers,
        'new_customers_month': new_customers_month,
        
        # Recent Data
        'recent_sales': recent_sales,
        'unread_notifications': unread_notifications,
        'low_stock_items': low_stock_items,
        'top_products': top_products,
    }
    
    return render(request, 'dashboard.html', context)


@login_required
def profile_view(request):
    """User profile view and edit"""
    if request.method == 'POST':
        user = request.user
        
        # Update profile fields
        user.first_name = request.POST.get('first_name', user.first_name)
        user.last_name = request.POST.get('last_name', user.last_name)
        user.email = request.POST.get('email', user.email)
        user.phone = request.POST.get('phone', user.phone)
        user.address = request.POST.get('address', user.address)
        
        # Handle profile picture upload
        if 'profile_picture' in request.FILES:
            user.profile_picture = request.FILES['profile_picture']
        
        user.save()
        
        # Log activity
        UserActivity.objects.create(
            user=user,
            action='update',
            description='Updated profile information'
        )
        
        messages.success(request, 'Profile updated successfully!')
        return redirect('accounts:profile')
    
    # Get user's recent activity
    recent_activity = UserActivity.objects.filter(
        user=request.user
    ).order_by('-timestamp')[:10]
    
    context = {
        'recent_activity': recent_activity,
    }
    
    return render(request, 'accounts/profile.html', context)


@login_required
@user_passes_test(lambda u: u.role in ['admin', 'manager'])
def user_list(request):
    """List all users (Admin/Manager only)"""
    users = User.objects.all().order_by('-date_joined')
    
    # Filter by role
    role_filter = request.GET.get('role')
    if role_filter:
        users = users.filter(role=role_filter)
    
    # Filter by status
    status_filter = request.GET.get('status')
    if status_filter == 'active':
        users = users.filter(is_active_employee=True)
    elif status_filter == 'inactive':
        users = users.filter(is_active_employee=False)
    
    # Search
    search_query = request.GET.get('search')
    if search_query:
        users = users.filter(
            Q(username__icontains=search_query) |
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(email__icontains=search_query)
        )
    
    context = {
        'users': users,
        'role_filter': role_filter,
        'status_filter': status_filter,
        'search_query': search_query,
    }
    
    return render(request, 'accounts/user_list.html', context)


@login_required
@user_passes_test(lambda u: u.role in ['admin', 'manager'])
def user_detail(request, pk):
    """View user details"""
    user = get_object_or_404(User, pk=pk)
    
    # Get user's activity
    activities = UserActivity.objects.filter(user=user).order_by('-timestamp')[:20]
    
    # Get user's sales (if applicable)
    sales = Sale.objects.filter(served_by=user).order_by('-sale_date')[:10]
    
    context = {
        'viewed_user': user,
        'activities': activities,
        'sales': sales,
    }
    
    return render(request, 'accounts/user_detail.html', context)


@login_required
def change_password(request):
    """Change user password"""
    if request.method == 'POST':
        current_password = request.POST.get('current_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')
        
        # Verify current password
        if not request.user.check_password(current_password):
            messages.error(request, 'Current password is incorrect.')
            return redirect('accounts:change_password')
        
        # Verify new passwords match
        if new_password != confirm_password:
            messages.error(request, 'New passwords do not match.')
            return redirect('accounts:change_password')
        
        # Validate password strength
        if len(new_password) < 8:
            messages.error(request, 'Password must be at least 8 characters long.')
            return redirect('accounts:change_password')
        
        # Update password
        request.user.set_password(new_password)
        request.user.save()
        
        # Log activity
        UserActivity.objects.create(
            user=request.user,
            action='update',
            description='Changed password'
        )
        
        messages.success(request, 'Password changed successfully! Please login again.')
        return redirect('accounts:login')
    
    return render(request, 'accounts/change_password.html')


# Helper function
def get_client_ip(request):
    """Get client IP address"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


# Import for F expression
from django.db.models import F