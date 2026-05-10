# scraper/urls.py

from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('search/', views.search_profiles, name='search'),
    path('test-scraper/', views.test_scraper, name='test_scraper'),
    path('search-status/', views.search_status, name='search_status'),
]