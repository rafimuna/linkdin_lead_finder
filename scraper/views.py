# scraper/views.py - Add these new functions

from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from .services.google_search import GoogleSearchScraper
from .services.linkedin_scraper import BatchLinkedInScraper
from .models import Profile, SearchHistory
from django.utils import timezone
import json
import traceback

# Your existing home function remains
def home(request):
    """Home page - existing code remains"""
    return render(request, 'scraper/home.html')


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
            # Step 1: Search Google for LinkedIn profiles
            messages.info(request, f'🔍 Searching for "{keyword}"...')
            google_scraper = GoogleSearchScraper()
            profile_urls = google_scraper.search_linkedin_profiles(keyword, max_results=20)
            
            if not profile_urls:
                messages.warning(request, f'No LinkedIn profiles found for "{keyword}"')
                return redirect('search')
            
            messages.success(request, f'Found {len(profile_urls)} LinkedIn profiles!')
            
            # Step 2: Scrape profile details
            messages.info(request, '📊 Scraping profile details...')
            batch_scraper = BatchLinkedInScraper(delay_between_requests=2)
            scraped_profiles = batch_scraper.scrape_multiple(profile_urls)
            
            # Step 3: Save to database
            saved_count = 0
            for profile_data in scraped_profiles:
                profile, created = Profile.objects.get_or_create(
                    linkedin_url=profile_data['linkedin_url'],
                    defaults={
                        'name': profile_data['name'] or 'Unknown',
                        'headline': profile_data['headline'] or '',
                        'location': profile_data['location'] or '',
                        'about': profile_data['about'] or '',
                        'search_keyword': keyword,
                        'scrape_status': 'completed',
                        'is_scraped': True,
                        'last_scraped_at': timezone.now()
                    }
                )
                if created:
                    saved_count += 1
            
            # Calculate duration
            duration = (timezone.now() - start_time).total_seconds()
            
            # Save search history
            SearchHistory.objects.create(
                keyword=keyword,
                total_results_found=len(profile_urls),
                profiles_scraped=len(scraped_profiles),
                search_duration=duration,
                user=request.user,
                ip_address=self.get_client_ip(request)
            )
            
            messages.success(
                request, 
                f'✅ Search completed! Found {len(profile_urls)} profiles, '
                f'scraped {len(scraped_profiles)}, saved {saved_count} new profiles.'
            )
            
            # Store results in session for dashboard
            request.session['last_search_keyword'] = keyword
            request.session['last_search_results'] = len(scraped_profiles)
            
            return redirect('dashboard')
            
        except Exception as e:
            print(f"Error in search: {traceback.format_exc()}")
            messages.error(request, f'Error occurred: {str(e)}')
            return redirect('search')
    
    # GET request - show search form
    return render(request, 'scraper/search.html')


def get_client_ip(self, request):
    """Get client IP address"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


@login_required
def search_status(request):
    """AJAX endpoint to check search status"""
    # For future implementation with Celery
    return JsonResponse({'status': 'ready'})


def test_scraper(request):
    """Test view to check if scraper works"""
    if not request.user.is_superuser:
        return HttpResponse("Only admin can test")
    
    keyword = request.GET.get('keyword', 'Django Developer')
    
    try:
        scraper = GoogleSearchScraper()
        urls = scraper.search_linkedin_profiles(keyword, max_results=5)
        
        result = f"<h2>Test Results for '{keyword}'</h2>"
        result += f"<p>Found {len(urls)} LinkedIn profiles:</p><ul>"
        
        for url in urls:
            result += f"<li><a href='{url}' target='_blank'>{url}</a></li>"
        
        result += "</ul><a href='/scraper/search/'>Back to Search</a>"
        
        return HttpResponse(result)
        
    except Exception as e:
        return HttpResponse(f"<h2>Error: {str(e)}</h2>")