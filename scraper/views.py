# scraper/views.py - Add all missing functions

from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.utils import timezone
from django.db.models import Count, Q
from .models import Profile, SearchHistory
import csv
import json
import re

# ========== Existing Functions Keep as is ==========

def home(request):
    """Home page view"""
    return render(request, 'scraper/home.html')


def get_client_ip(request):
    """Get client IP address"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


@login_required
def search_profiles(request):
    """Search LinkedIn profiles - Keep your existing code"""
    # Your existing search_profiles code here
    pass


# ========== DASHBOARD VIEW - COMPLETE ==========

@login_required
def dashboard_view(request):
    """
    Dashboard to show scraped profiles with filters and pagination
    """
    # Get filter parameters from GET request
    category = request.GET.get('category', '')
    location = request.GET.get('location', '')
    search_query = request.GET.get('search', '')
    
    # Start with all profiles
    profiles = Profile.objects.all()
    
    # Apply category filter
    if category and category != 'all':
        profiles = profiles.filter(category=category)
    
    # Apply location filter
    if location:
        profiles = profiles.filter(location__icontains=location)
    
    # Apply search filter (name or headline)
    if search_query:
        profiles = profiles.filter(
            Q(name__icontains=search_query) |
            Q(headline__icontains=search_query) |
            Q(skills__icontains=search_query)
        )
    
    # Order by latest first
    profiles = profiles.order_by('-created_at')
    
    # Pagination - 20 profiles per page
    paginator = Paginator(profiles, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get statistics for dashboard cards
    total_profiles = Profile.objects.count()
    
    # Category wise statistics
    categories_stats = {
        'recruiter': Profile.objects.filter(category='recruiter').count(),
        'hr': Profile.objects.filter(category='hr').count(),
        'backend_dev': Profile.objects.filter(category='backend_dev').count(),
        'frontend_dev': Profile.objects.filter(category='frontend_dev').count(),
        'fullstack_dev': Profile.objects.filter(category='fullstack_dev').count(),
        'manager': Profile.objects.filter(category='manager').count(),
        'ceo': Profile.objects.filter(category='ceo').count(),
        'other': Profile.objects.filter(category='other').count(),
    }
    
    # Recent searches (last 5)
    recent_searches = SearchHistory.objects.filter(
        user=request.user
    ).order_by('-created_at')[:5]
    
    context = {
        'page_obj': page_obj,
        'total_profiles': total_profiles,
        'categories_stats': categories_stats,
        'current_category': category,
        'current_location': location,
        'current_search': search_query,
        'recent_searches': recent_searches,
    }
    
    return render(request, 'dashboard/dashboard.html', context)


# ========== PROFILE DETAIL VIEW ==========

@login_required
def profile_detail(request, profile_id):
    """
    View single profile details
    """
    profile = get_object_or_404(Profile, id=profile_id)
    
    # Get related profiles (same category)
    related_profiles = Profile.objects.filter(
        category=profile.category
    ).exclude(id=profile.id)[:5]
    
    context = {
        'profile': profile,
        'related_profiles': related_profiles,
    }
    
    return render(request, 'dashboard/profile_detail.html', context)


# ========== DELETE PROFILE ==========

@login_required
def delete_profile(request, profile_id):
    """
    Delete a profile (requires admin or owner)
    """
    profile = get_object_or_404(Profile, id=profile_id)
    
    # Only superuser can delete
    if not request.user.is_superuser:
        messages.error(request, 'Only admin can delete profiles')
        return redirect('dashboard')
    
    profile_name = profile.name
    profile.delete()
    messages.success(request, f'Successfully deleted: {profile_name}')
    
    return redirect('dashboard')


# ========== CSV EXPORT ==========

@login_required
def export_csv(request):
    """
    Export all profiles to CSV file
    """
    # Create response object
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="linkedin_profiles_export.csv"'
    
    # Get all profiles
    profiles = Profile.objects.all().order_by('-created_at')
    
    # Create CSV writer
    writer = csv.writer(response)
    
    # Write headers
    writer.writerow([
        'ID', 'Name', 'Headline', 'Location', 'Category', 
        'LinkedIn URL', 'Skills', 'Search Keyword', 
        'Created At', 'Last Scraped'
    ])
    
    # Write data rows
    for profile in profiles:
        writer.writerow([
            profile.id,
            profile.name,
            profile.headline or '',
            profile.location or '',
            profile.get_category_display(),
            profile.linkedin_url,
            profile.skills or '',
            profile.search_keyword or '',
            profile.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            profile.last_scraped_at.strftime('%Y-%m-%d %H:%M:%S') if profile.last_scraped_at else '',
        ])
    
    messages.success(request, f'Exported {profiles.count()} profiles to CSV')
    return response


@login_required
def export_excel(request):
    """
    Export to Excel format (using pandas if available)
    """
    try:
        import pandas as pd
        from io import BytesIO
        
        profiles = Profile.objects.all().values(
            'name', 'headline', 'location', 'category', 
            'linkedin_url', 'skills', 'search_keyword', 'created_at'
        )
        
        df = pd.DataFrame(list(profiles))
        
        # Convert category codes to labels
        category_labels = dict(Profile._meta.get_field('category').choices)
        df['category'] = df['category'].map(category_labels)
        
        # Create Excel file
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='LinkedIn Profiles', index=False)
        
        response = HttpResponse(
            output.getvalue(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = 'attachment; filename="linkedin_profiles.xlsx"'
        
        messages.success(request, f'Exported {len(df)} profiles to Excel')
        return response
        
    except ImportError:
        messages.error(request, 'Pandas not installed. Please install: pip install pandas openpyxl')
        return redirect('dashboard')


# ========== MANUAL ADD PROFILES ==========

@login_required
def manual_add_profiles(request):
    """
    Manually add LinkedIn URLs
    """
    if request.method == 'POST':
        urls_text = request.POST.get('urls', '')
        category = request.POST.get('category', 'other')
        
        urls = [url.strip() for url in urls_text.split('\n') if url.strip()]
        
        saved_count = 0
        duplicate_count = 0
        invalid_count = 0
        
        for url in urls:
            if 'linkedin.com/in/' in url:
                # Clean the URL
                if '#:~:text' in url:
                    url = url.split('#:~:text')[0]
                
                # Extract name from URL
                match = re.search(r'/in/([^/?]+)', url)
                name = match.group(1).replace('-', ' ').replace('_', ' ').title() if match else 'Unknown'
                
                # Check if already exists
                profile, created = Profile.objects.get_or_create(
                    linkedin_url=url,
                    defaults={
                        'name': name,
                        'headline': f'Manually Added - {category}',
                        'location': 'Not specified',
                        'category': category,
                        'search_keyword': 'manual',
                        'scrape_status': 'completed',
                        'is_scraped': True,
                        'last_scraped_at': timezone.now()
                    }
                )
                
                if created:
                    saved_count += 1
                else:
                    duplicate_count += 1
            else:
                invalid_count += 1
        
        if saved_count > 0:
            messages.success(request, f'✅ Added {saved_count} new profiles!')
        if duplicate_count > 0:
            messages.warning(request, f'⚠️ {duplicate_count} profiles already exist')
        if invalid_count > 0:
            messages.error(request, f'❌ {invalid_count} invalid LinkedIn URLs')
        
        return redirect('dashboard')
    
    # Sample URLs for testing
    sample_urls = """https://www.linkedin.com/in/satya-nadella/
https://www.linkedin.com/in/tim-cook/
https://www.linkedin.com/in/sundarpichai/
https://www.linkedin.com/in/jeffweiner/"""
    
    return render(request, 'scraper/manual_add.html', {'sample_urls': sample_urls})


# ========== SEARCH HISTORY ==========

@login_required
def search_history(request):
    """
    View search history
    """
    histories = SearchHistory.objects.filter(user=request.user).order_by('-created_at')
    
    paginator = Paginator(histories, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'dashboard/search_history.html', {'page_obj': page_obj})


# ========== AI CLASSIFICATION ==========

@login_required
def reclassify_profiles(request):
    """
    Reclassify all profiles using AI
    """
    from .services.ai_classifier import classify_profiles_batch
    
    messages.info(request, 'AI classification started...')
    
    # Run classification in background (for now, run sync)
    result = classify_profiles_batch()
    
    messages.success(request, f'AI classification completed! Updated {result} profiles')
    return redirect('dashboard')


@login_required
def classify_single_profile(request, profile_id):
    """
    Classify a single profile
    """
    from .services.ai_classifier import classify_profile
    
    profile = get_object_or_404(Profile, id=profile_id)
    new_category, confidence = classify_profile(profile)
    
    profile.update_category(new_category, confidence)
    messages.success(request, f'Profile classified as: {profile.get_category_display()} (Confidence: {confidence}%)')
    
    return redirect('profile_detail', profile_id=profile_id)


# ========== API ENDPOINTS ==========

@login_required
def search_status(request):
    """AJAX endpoint to check search status"""
    return JsonResponse({'status': 'ready', 'message': 'Search system ready'})


@login_required
def profile_stats_api(request):
    """API endpoint for profile statistics"""
    stats = {
        'total': Profile.objects.count(),
        'by_category': dict(Profile.objects.values_list('category').annotate(count=Count('id'))),
        'last_7_days': Profile.objects.filter(created_at__gte=timezone.now() - timezone.timedelta(days=7)).count(),
    }
    return JsonResponse(stats)


# ========== TEST FUNCTIONS ==========

@login_required
def test_scraper(request):
    """Test scraper (admin only)"""
    if not request.user.is_superuser:
        return HttpResponse("Access denied", status=403)
    
    from .services.google_search_selenium import SeleniumGoogleSearch
    
    keyword = request.GET.get('keyword', 'Python Developer')
    
    try:
        scraper = SeleniumGoogleSearch(headless=False)
        urls = scraper.search_linkedin_profiles(keyword, max_results=5)
        scraper.close()
        
        result = f"<h2>Test Results for '{keyword}'</h2>"
        result += f"<p>Found {len(urls)} profiles:</p><ul>"
        for url in urls:
            result += f"<li>{url}</li>"
        result += "</ul><a href='/dashboard/'>Back to Dashboard</a>"
        
        return HttpResponse(result)
    except Exception as e:
        return HttpResponse(f"Error: {e}")


@login_required
def quick_add_profiles(request):
    """Quick add predefined test profiles"""
    test_profiles = [
        {'name': 'Satya Nadella', 'url': 'https://www.linkedin.com/in/satya-nadella/', 'category': 'ceo'},
        {'name': 'Tim Cook', 'url': 'https://www.linkedin.com/in/tim-cook/', 'category': 'ceo'},
        {'name': 'Sundar Pichai', 'url': 'https://www.linkedin.com/in/sundarpichai/', 'category': 'ceo'},
    ]
    
    added = 0
    for data in test_profiles:
        profile, created = Profile.objects.get_or_create(
            linkedin_url=data['url'],
            defaults={
                'name': data['name'],
                'headline': f'CEO of Major Tech Company',
                'category': data['category'],
                'search_keyword': 'quick_add',
                'scrape_status': 'completed',
                'is_scraped': True,
            }
        )
        if created:
            added += 1
    
    messages.success(request, f'Added {added} test profiles!')
    return redirect('dashboard')