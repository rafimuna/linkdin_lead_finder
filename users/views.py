# users/views.py

from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages

def login_view(request):
    """Login page view"""
    return HttpResponse("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Login - LinkedIn Lead Finder</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 50px; background: #f0f2f5; }
            .login-box {
                max-width: 400px;
                margin: auto;
                background: white;
                padding: 30px;
                border-radius: 10px;
                box-shadow: 0 0 10px rgba(0,0,0,0.1);
            }
            input { width: 100%; padding: 10px; margin: 10px 0; border: 1px solid #ddd; border-radius: 5px; }
            button { background: #667eea; color: white; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer; }
        </style>
    </head>
    <body>
        <div class="login-box">
            <h2>🔐 Login</h2>
            <p>Authentication system coming in Phase 10</p>
            <form method="post">
                <input type="text" placeholder="Username" disabled>
                <input type="password" placeholder="Password" disabled>
                <button disabled>Login (Coming Soon)</button>
            </form>
            <p><a href="/">← Back to Home</a></p>
        </div>
    </body>
    </html>
    """)

def logout_view(request):
    """Logout view"""
    return HttpResponse("Logged out! <a href='/'>Go Home</a>")

def register_view(request):
    """Register page view"""
    return HttpResponse("""
    <h2>Register</h2>
    <p>Registration system coming in Phase 10</p>
    <a href="/">Back to Home</a>
    """)