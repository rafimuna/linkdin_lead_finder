# scraper/views.py
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
    """Search LinkedIn profiles - Working version"""
    
    if request.method == 'POST':
        keyword = request.POST.get('keyword', '')
        
        if not keyword:
            messages.error(request, 'Please enter a keyword to search!')
            return render(request, 'scraper/search.html')
        
        # Save search history
        SearchHistory.objects.create(
            user=request.user,
            keyword=keyword,
            ip_address=get_client_ip(request),
            results_count=0
        )
        
        # Redirect to results page with keyword
        return redirect(f'/results/?keyword={keyword}')
    
    # GET request - show search form
    return render(request, 'scraper/search.html')


@login_required
def results_view(request):
    """Show search results"""
    keyword = request.GET.get('keyword', '')
    
    if not keyword:
        return redirect('search')
    
    messages.info(request, f'Searching for "{keyword}"... This feature is being developed.')
    
    return render(request, 'scraper/results.html', {'keyword': keyword})


@login_required
def dashboard_view(request):
    """Dashboard to show scraped profiles with filters and pagination"""
    category = request.GET.get('category', '')
    location = request.GET.get('location', '')
    search_query = request.GET.get('search', '')
    
    profiles = Profile.objects.all()
    
    if category and category != 'all':
        profiles = profiles.filter(category=category)
    if location:
        profiles = profiles.filter(location__icontains=location)
    if search_query:
        profiles = profiles.filter(
            Q(name__icontains=search_query) |
            Q(headline__icontains=search_query) |
            Q(skills__icontains=search_query)
        )
    
    profiles = profiles.order_by('-created_at')
    paginator = Paginator(profiles, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    total_profiles = Profile.objects.count()
    
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


@login_required
def profile_detail(request, profile_id):
    """View single profile details"""
    profile = get_object_or_404(Profile, id=profile_id)
    related_profiles = Profile.objects.filter(
        category=profile.category
    ).exclude(id=profile.id)[:5]
    
    context = {
        'profile': profile,
        'related_profiles': related_profiles,
    }
    
    return render(request, 'dashboard/profile_detail.html', context)


@login_required
def delete_profile(request, profile_id):
    """Delete a profile"""
    profile = get_object_or_404(Profile, id=profile_id)
    
    if not request.user.is_superuser:
        messages.error(request, 'Only admin can delete profiles')
        return redirect('dashboard')
    
    profile_name = profile.name
    profile.delete()
    messages.success(request, f'Successfully deleted: {profile_name}')
    
    return redirect('dashboard')


@login_required
def export_csv(request):
    """Export all profiles to CSV file"""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="linkedin_profiles_export.csv"'
    
    profiles = Profile.objects.all().order_by('-created_at')
    writer = csv.writer(response)
    
    writer.writerow([
        'ID', 'Name', 'Headline', 'Location', 'Category',
        'LinkedIn URL', 'Skills', 'Search Keyword',
        'Created At', 'Last Scraped'
    ])
    
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
    """Export to Excel format"""
    try:
        import pandas as pd
        from io import BytesIO
        
        profiles = Profile.objects.all().values(
            'name', 'headline', 'location', 'category',
            'linkedin_url', 'skills', 'search_keyword', 'created_at'
        )
        
        df = pd.DataFrame(list(profiles))
        category_labels = dict(Profile._meta.get_field('category').choices)
        df['category'] = df['category'].map(category_labels)
        
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
        messages.error(request, 'Pandas not installed.')
        return redirect('dashboard')
@login_required
def manual_add_profiles(request):
    """
    Manually add LinkedIn URLs
    """
    if request.method == 'POST':
        urls_text = request.POST.get('urls', '')
        category = request.POST.get('category', 'other')
        
        if not urls_text:
            messages.error(request, 'Please enter at least one LinkedIn URL!')
            return redirect('manual_add')
        
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
                if match:
                    name_raw = match.group(1)
                    name = name_raw.replace('-', ' ').replace('_', ' ').title()
                else:
                    name = 'Unknown Profile'
                
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
    
    context = {
        'sample_urls': sample_urls
    }
    return render(request, 'scraper/manual_add.html', context)


       
          

@login_required
def search_history(request):
    """View search history"""
    histories = SearchHistory.objects.filter(user=request.user).order_by('-created_at')
    paginator = Paginator(histories, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'dashboard/search_history.html', {'page_obj': page_obj})


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
                'headline': 'CEO of Major Tech Company',
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