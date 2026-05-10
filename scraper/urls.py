# scraper/urls.py

from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),  # Now 'home' function exists
    path('search/', views.search_linkedin, name='search_linkedin'),
]