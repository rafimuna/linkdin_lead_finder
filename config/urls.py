from django.contrib import admin
from django.urls import path, include
from scraper import views as scraper_views
from users import views as user_views
from dashboard import views as dashboard_views  # যদি dashboard app এ আলাদা views থাকে

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Home page (scraper home)
    path('', scraper_views.home, name='home'),
    
    # Authentication URLs
    path('login/', user_views.login_view, name='login'),      # ← কাস্টম view
    path('logout/', user_views.logout_view, name='logout'),   # ← কাস্টম view
    
    # Users app (Registration, Profile)
    path('users/', include('users.urls')),
    
    # Dashboard (scraper dashboard_view ব্যবহার করবে)
    path('dashboard/', scraper_views.dashboard_view, name='dashboard'),
    path('results/', scraper_views.results_view, name='results'),
    # Profile detail and actions
    path('profile/<int:profile_id>/', scraper_views.profile_detail, name='profile_detail'),
    path('profile/<int:profile_id>/delete/', scraper_views.delete_profile, name='delete_profile'),
    
    # Search and scraping
    path('search/', scraper_views.search_profiles, name='search'),
    path('manual-add/', scraper_views.manual_add_profiles, name='manual_add'),
    path('quick-add/', scraper_views.quick_add_profiles, name='quick_add'),
    
    # Exports
    path('export/csv/', scraper_views.export_csv, name='export_csv'),
    path('export/excel/', scraper_views.export_excel, name='export_excel'),
    
    # History
    path('search-history/', scraper_views.search_history, name='search_history'),
    
    # API and test endpoints
    path('api/search-status/', scraper_views.search_status, name='search_status'),
    path('api/profile-stats/', scraper_views.profile_stats_api, name='profile_stats_api'),
    path('test-scraper/', scraper_views.test_scraper, name='test_scraper'),
    
    # Reclassify all
    path('reclassify-all/', scraper_views.reclassify_profiles, name='reclassify_all'),
    
    # Exports app (যদি থাকে)
    path('exports/', include('exports.urls')),
]