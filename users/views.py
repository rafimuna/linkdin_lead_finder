# users/views.py - সম্পূর্ণ আপডেটেড ভার্সন (কোনো disabled attribute নেই)
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm 

def login_view(request):
    """
    User login view - working version with enabled form fields
    """
    
    # যদি ইতিমধ্যে logged in থাকে
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        # Authenticate user
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            messages.success(request, f'Welcome back, {username}!')
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid username or password!')
            return redirect('login')
    
    # GET request - show login form
    return render(request, 'users/login.html')

def logout_view(request):
    """User logout view"""
    logout(request)
    messages.info(request, 'You have been logged out successfully.')
    return redirect('home')
def register_view(request):
    """User registration view"""
    if request.method == 'POST':
        form = UserCreationForm(request.POST)  # ← form তৈরি করুন
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f'Account created for {username}! Please login.')
            return redirect('login')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = UserCreationForm()  # ← empty form
    
    return render(request, 'users/register.html', {'form': form})  # ← form পাস করুন

        
        
       
        
        

def profile_view(request):
    """User profile view - requires login"""
    if not request.user.is_authenticated:
        return redirect('login')
    
    return render(request, 'users/profile.html', {'user': request.user})