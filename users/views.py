# users/views.py - সম্পূর্ণ আপডেটেড ওয়ার্কিং ভার্সন
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.models import User

def login_view(request):
    """User login view - Working with manual form"""
    
    # যদি ইতিমধ্যে লগইন করা থাকে
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        # ইউজার অথেনটিকেট করুন
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            messages.success(request, f'Welcome back, {username}!')
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid username or password!')
            # ফর্মটি আবার দেখান
            return render(request, 'users/login.html')
    
    # GET রিকোয়েস্ট - ফর্ম দেখান
    return render(request, 'users/login.html')


def logout_view(request):
    """User logout view"""
    logout(request)
    messages.info(request, 'You have been logged out successfully.')
    return redirect('home')


def register_view(request):
    """User registration view - Working with manual form"""
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email', '')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')
        
        # ভ্যালিডেশন
        if password1 != password2:
            messages.error(request, 'Passwords do not match!')
            return redirect('register')
        
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists!')
            return redirect('register')
        
        if len(password1) < 6:
            messages.error(request, 'Password must be at least 6 characters!')
            return redirect('register')
        
        # ইউজার তৈরি করুন
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password1
        )
        user.save()
        
        messages.success(request, f'Account created for {username}! Please login.')
        return redirect('login')
    
    # GET রিকোয়েস্ট - ফর্ম দেখান
    return render(request, 'users/register.html')


def profile_view(request):
    """User profile view"""
    if not request.user.is_authenticated:
        return redirect('login')
    return render(request, 'users/profile.html', {'user': request.user})