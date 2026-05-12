from django.urls import path
from . import views

urlpatterns = [
    # Dashboard
    path('', views.export_dashboard, name='export_dashboard'),
    path('history/', views.export_history, name='export_history'),
    
    # Export formats
    path('csv/', views.export_csv, name='export_csv'),
    path('excel/', views.export_excel, name='export_excel'),
    path('pdf/', views.export_pdf, name='export_pdf'),
    
    # Single profile export
    path('profile/<int:profile_id>/csv/', views.export_single_profile, {'format': 'csv'}, name='export_single_csv'),
    path('profile/<int:profile_id>/json/', views.export_single_profile, {'format': 'json'}, name='export_single_json'),
    
    # Download
    path('download/<int:export_id>/', views.download_export, name='download_export'),
]