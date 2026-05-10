# scraper/views.py - COMPLETE WORKING VERSION

from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.utils import timezone
import json
import traceback
import re

# Import your services
from .services.google_search_selenium import SeleniumGoogleSearch
from .services.linkedin_scraper import BatchLinkedInScraper
from .models import Profile, SearchHistory


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
    """
    Search LinkedIn profiles based on keyword
    This is the main search view
    """
    if request.method == 'POST':
        keyword = request.POST.get('keyword', '').strip()
        
        if not keyword:
            messages.error(request, 'Please enter a search keyword')
            return redirect('search')
        
        # Start timing
        start_time = timezone.now()
        
        try:
            # Step 1: Search Google for LinkedIn profiles using Selenium
            messages.info(request, f'🔍 Searching for "{keyword}"...')
            
            # Initialize Selenium scraper (headless=False so you can see the browser)
            google_scraper = SeleniumGoogleSearch(headless=False)
            profile_urls = google_scraper.search_linkedin_profiles(keyword, max_results=15)
            google_scraper.close()
            
            if not profile_urls:
                messages.warning(request, f'No LinkedIn profiles found for "{keyword}". Try a different keyword.')
                return redirect('search')
            
            messages.success(request, f'Found {len(profile_urls)} LinkedIn profiles!')
            
            # Optional: Show found URLs in console for debugging
            print(f"\n📋 Found LinkedIn URLs for '{keyword}':")
            for url in profile_urls[:5]:  # Show first 5
                print(f"  - {url}")
            
            # Step 2: Scrape profile details
            messages.info(request, '📊 Scraping profile details... This may take a moment.')
            batch_scraper = BatchLinkedInScraper(delay_between_requests=2)
            scraped_profiles = batch_scraper.scrape_multiple(profile_urls)
            
            # Step 3: Save to database
            saved_count = 0
            updated_count = 0
            
            for profile_data in scraped_profiles:
                if profile_data and profile_data.get('linkedin_url'):
                    profile, created = Profile.objects.get_or_create(
                        linkedin_url=profile_data['linkedin_url'],
                        defaults={
                            'name': profile_data.get('name') or 'Unknown',
                            'headline': profile_data.get('headline', '')[:250] if profile_data.get('headline') else '',
                            'location': profile_data.get('location', '')[:100] if profile_data.get('location') else '',
                            'about': profile_data.get('about', '')[:500] if profile_data.get('about') else '',
                            'skills': profile_data.get('skills', '') if profile_data.get('skills') else '',
                            'search_keyword': keyword,
                            'scrape_status': 'completed',
                            'is_scraped': True,
                            'last_scraped_at': timezone.now()
                        }
                    )
                    
                    if created:
                        saved_count += 1
                    else:
                        # Update existing profile
                        profile.search_keyword = keyword
                        profile.last_scraped_at = timezone.now()
                        profile.save(update_fields=['search_keyword', 'last_scraped_at'])
                        updated_count += 1
            
            # Calculate duration
            duration = (timezone.now() - start_time).total_seconds()
            
            # Save search history
            SearchHistory.objects.create(
                keyword=keyword,
                total_results_found=len(profile_urls),
                profiles_scraped=len(scraped_profiles),
                search_duration=duration,
                user=request.user,
                ip_address=get_client_ip(request)
            )
            
            messages.success(
                request, 
                f'✅ Search completed!\n'
                f'📊 Found: {len(profile_urls)} profiles\n'
                f'✅ Scraped: {len(scraped_profiles)} profiles\n'
                f'💾 Saved: {saved_count} new, {updated_count} updated\n'
                f'⏱️ Time: {duration:.2f} seconds'
            )
            
            # Store results in session for dashboard
            request.session['last_search_keyword'] = keyword
            request.session['last_search_results'] = len(scraped_profiles)
            
            return redirect('dashboard')
            
        except Exception as e:
            print(f"Error in search: {traceback.format_exc()}")
            messages.error(request, f'Error occurred: {str(e)[:200]}')
            return redirect('search')
    
    # GET request - show search form
    return render(request, 'scraper/search.html')


@login_required
def dashboard_view(request):
    """
    Dashboard to show scraped profiles
    """
    # Get filter parameters
    category = request.GET.get('category', '')
    location = request.GET.get('location', '')
    search_query = request.GET.get('search', '')
    
    # Start with all profiles
    profiles = Profile.objects.all()
    
    # Apply filters
    if category and category != 'all':
        profiles = profiles.filter(category=category)
    
    if location:
        profiles = profiles.filter(location__icontains=location)
    
    if search_query:
        profiles = profiles.filter(
            models.Q(name__icontains=search_query) |
            models.Q(headline__icontains=search_query) |
            models.Q(skills__icontains=search_query)
        )
    
    # Order by latest first
    profiles = profiles.order_by('-created_at')
    
    # Pagination
    paginator = Paginator(profiles, 20)  # 20 profiles per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get statistics
    total_profiles = Profile.objects.count()
    categories_stats = {
        'recruiter': Profile.objects.filter(category='recruiter').count(),
        'hr': Profile.objects.filter(category='hr').count(),
        'backend_dev': Profile.objects.filter(category='backend_dev').count(),
        'frontend_dev': Profile.objects.filter(category='frontend_dev').count(),
        'manager': Profile.objects.filter(category='manager').count(),
        'ceo': Profile.objects.filter(category='ceo').count(),
    }
    
    context = {
        'page_obj': page_obj,
        'total_profiles': total_profiles,
        'categories_stats': categories_stats,
        'current_category': category,
        'current_location': location,
        'current_search': search_query,
    }
    
    return render(request, 'dashboard/dashboard.html', context)


@login_required
def profile_detail(request, profile_id):
    """
    View single profile details
    """
    try:
        profile = Profile.objects.get(id=profile_id)
        return render(request, 'dashboard/profile_detail.html', {'profile': profile})
    except Profile.DoesNotExist:
        messages.error(request, 'Profile not found')
        return redirect('dashboard')


@login_required
def export_csv(request):
    """
    Export profiles to CSV
    """
    import csv
    from django.http import HttpResponse
    
    # Create CSV response
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="linkedin_profiles.csv"'
    
    # Get all profiles
    profiles = Profile.objects.all().order_by('-created_at')
    
    # Create CSV writer
    writer = csv.writer(response)
    
    # Write headers
    writer.writerow([
        'Name', 'Headline', 'Location', 'Category', 
        'LinkedIn URL', 'Skills', 'Created At'
    ])
    
    # Write data
    for profile in profiles:
        writer.writerow([
            profile.name,
            profile.headline or '',
            profile.location or '',
            profile.get_category_display(),
            profile.linkedin_url,
            profile.skills or '',
            profile.created_at.strftime('%Y-%m-%d %H:%M:%S')
        ])
    
    messages.success(request, f'Exported {profiles.count()} profiles to CSV')
    return response


@login_required
def search_status(request):
    """AJAX endpoint to check search status"""
    return JsonResponse({'status': 'ready', 'message': 'Search system ready'})


def test_scraper(request):
    """Test view to check if scraper works (admin only)"""
    if not request.user.is_authenticated or not request.user.is_superuser:
        return HttpResponse("Access denied. Admin only.", status=403)
    
    keyword = request.GET.get('keyword', 'Python Developer')
    
    try:
        # Test with Selenium
        scraper = SeleniumGoogleSearch(headless=False)
        urls = scraper.search_linkedin_profiles(keyword, max_results=5)
        scraper.close()
        
        result = f"""
        <html>
        <head>
            <title>Scraper Test Results</title>
            <style>
                body {{ font-family: Arial; margin: 20px; }}
                .success {{ color: green; }}
                .error {{ color: red; }}
                ul {{ background: #f0f0f0; padding: 20px; }}
                li {{ margin: 10px 0; }}
            </style>
        </head>
        <body>
            <h1>🔍 Scraper Test Results</h1>
            <h2>Keyword: {keyword}</h2>
            <p class="success">✅ Found {len(urls)} LinkedIn profiles:</p>
            <ul>
        """
        
        for url in urls:
            result += f"<li><a href='{url}' target='_blank'>{url}</a></li>"
        
        result += """
            </ul>
            <p>⏱️ Test completed successfully!</p>
            <a href="/search/">← Back to Search</a>
        </body>
        </html>
        """
        
        return HttpResponse(result)
        
    except Exception as e:
        return HttpResponse(f"""
        <html>
        <body>
            <h1 class="error">❌ Error</h1>
            <p>Error: {str(e)}</p>
            <p>Make sure Chrome browser is installed!</p>
            <a href="/search/">← Back to Search</a>
        </body>
        </html>
        """)


@login_required
def manual_add_profiles(request):
    """
    Manually add LinkedIn URLs for testing
    """
    if request.method == 'POST':
        urls_text = request.POST.get('urls', '')
        urls = [url.strip() for url in urls_text.split('\n') if url.strip()]
        
        saved_count = 0
        failed_urls = []
        
        for url in urls:
            if 'linkedin.com/in/' in url:
                # Extract name from URL
                match = re.search(r'/in/([^/?]+)', url)
                name = match.group(1).replace('-', ' ').replace('_', ' ').title() if match else 'Unknown'
                
                profile, created = Profile.objects.get_or_create(
                    linkedin_url=url,
                    defaults={
                        'name': name,
                        'headline': 'Manually Added Profile',
                        'location': 'Not specified',
                        'search_keyword': 'manual',
                        'scrape_status': 'completed',
                        'is_scraped': True,
                    }
                )
                if created:
                    saved_count += 1
                else:
                    failed_urls.append(url)
            else:
                failed_urls.append(url)
        
        if saved_count > 0:
            messages.success(request, f'✅ Added {saved_count} profiles manually!')
        if failed_urls:
            messages.warning(request, f'⚠️ Failed to add {len(failed_urls)} URLs (invalid LinkedIn URLs)')
        
        return redirect('dashboard')
    
    # Sample URLs for testing
    sample_urls = """https://www.linkedin.com/in/satya-nadella/
https://www.linkedin.com/in/tim-cook/
https://www.linkedin.com/in/sundarpichai/
https://www.linkedin.com/in/jeffweiner/"""
    
    return render(request, 'scraper/manual_add.html', {'sample_urls': sample_urls})


@login_required
def delete_profile(request, profile_id):
    """
    Delete a profile (admin only)
    """
    if not request.user.is_superuser:
        messages.error(request, 'Only admin can delete profiles')
        return redirect('dashboard')
    
    try:
        profile = Profile.objects.get(id=profile_id)
        profile_name = profile.name
        profile.delete()
        messages.success(request, f'Deleted profile: {profile_name}')
    except Profile.DoesNotExist:
        messages.error(request, 'Profile not found')
    
    return redirect('dashboard')


@login_required
def reclassify_profiles(request):
    """
    Reclassify all profiles using AI (to be implemented in Phase 8)
    """
    messages.info(request, 'AI classification feature coming in Phase 8!')
    return redirect('dashboard')


@login_required
def search_history(request):
    """
    View search history
    """
    histories = SearchHistory.objects.filter(user=request.user).order_by('-created_at')[:50]
    return render(request, 'dashboard/search_history.html', {'histories': histories})