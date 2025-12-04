from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import User

def login_view(request):
    if request.user.is_authenticated:
        return redirect('accounts:dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            return redirect('accounts:dashboard')
        else:
            messages.error(request, 'Invalid username or password')
    
    return render(request, 'accounts/login.html')

@login_required
def logout_view(request):
    logout(request)
    return redirect('accounts:login')

@login_required
def dashboard(request):
    context = {
        'user': request.user,
        'total_medicines': Medicine.objects.count(),
        'low_stock_count': Medicine.objects.filter(
            total_quantity__lte=models.F('reorder_level')
        ).count(),
    }
    return render(request, 'dashboard.html', context)