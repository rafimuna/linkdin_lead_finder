# scraper/urls.py - Complete URL Configuration

from django.urls import path
from . import views

urlpatterns = [
    # ========== Main Pages ==========
    path('', views.home, name='home'),                    # Homepage
    path('search/', views.search_profiles, name='search'), # Search page
    path('dashboard/', views.dashboard_view, name='dashboard'),  # Dashboard
    
    # ========== Profile Actions ==========
    path('profile/<int:profile_id>/', views.profile_detail, name='profile_detail'),
    path('profile/<int:profile_id>/delete/', views.delete_profile, name='delete_profile'),
    
    # ========== Export & Utilities ==========
    path('export/csv/', views.export_csv, name='export_csv'),
    path('export/excel/', views.export_excel, name='export_excel'),
    path('manual-add/', views.manual_add_profiles, name='manual_add'),
    path('search-history/', views.search_history, name='search_history'),
    
    # ========== AI Features ==========
    path('reclassify/', views.reclassify_profiles, name='reclassify'),
    path('classify-profile/<int:profile_id>/', views.classify_single_profile, name='classify_single'),
    
    # ========== API Endpoints ==========
    path('api/search-status/', views.search_status, name='search_status'),
    path('api/profile-stats/', views.profile_stats_api, name='profile_stats_api'),
    
    # ========== Test Endpoints (Admin Only) ==========
    path('test-scraper/', views.test_scraper, name='test_scraper'),
    path('quick-add/', views.quick_add_profiles, name='quick_add'),
]