# dashboard/views.py

from django.shortcuts import render
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required

def dashboard_home(request):
    """Dashboard home view"""
    return HttpResponse("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Dashboard - LinkedIn Lead Finder</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 50px; }
            .container { max-width: 1200px; margin: auto; }
            .header { background: #667eea; color: white; padding: 20px; border-radius: 10px; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>📊 Dashboard</h1>
                <p>Your LinkedIn leads will appear here</p>
            </div>
            <div style="margin-top: 20px;">
                <h3>Coming Soon in Phase 7:</h3>
                <ul>
                    <li>Search form</li>
                    <li>Results table</li>
                    <li>Filter and pagination</li>
                    <li>CSV export</li>
                </ul>
                <a href="/">← Back to Home</a>
            </div>
        </div>
    </body>
    </html>
    """)