# scraper/services/linkedin_scraper.py - COMPLETE REWRITE

import requests
import re
import time
import random
from bs4 import BeautifulSoup
from fake_useragent import UserAgent

class LinkedInScraper:
    """
    LinkedIn profile scraper with better error handling
    """
    
    def __init__(self):
        self.ua = UserAgent()
        self.timeout = 20
        self.session = self._create_session()
    
    def _create_session(self):
        """Create requests session with proper headers"""
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
        })
        return session
    
    def clean_url(self, url):
        """
        Clean LinkedIn URL by removing fragments and tracking parameters
        """
        if not url:
            return None
        
        # Remove URL fragment (#:~:text etc.)
        if '#:~:text' in url:
            url = url.split('#:~:text')[0]
        
        # Remove trailing slashes and query parameters
        url = url.split('?')[0]
        url = url.rstrip('/')
        
        # Extract clean LinkedIn profile URL
        match = re.search(r'(https?://(?:www\.)?linkedin\.com/in/[a-zA-Z0-9_-]+)', url)
        if match:
            return match.group(1)
        
        return None
    
    def scrape_profile(self, profile_url):
        """
        Scrape public information from LinkedIn profile
        Note: LinkedIn blocks most scrapers, so we extract from URL
        """
        # First clean the URL
        clean_url = self.clean_url(profile_url)
        
        if not clean_url:
            print(f"❌ Invalid LinkedIn URL: {profile_url}")
            return None
        
        print(f"🔄 Processing: {clean_url}")
        
        # Try to get basic info from URL
        profile_data = self._extract_from_url(clean_url)
        
        try:
            # Try to scrape with requests (might get blocked)
            time.sleep(random.uniform(2, 4))
            response = self.session.get(clean_url, timeout=self.timeout, allow_redirects=True)
            
            if response.status_code == 200:
                # Successfully fetched, parse HTML
                html_data = self._parse_html(response.text, clean_url)
                if html_data:
                    profile_data.update(html_data)
            elif response.status_code == 999:
                print(f"⚠️ LinkedIn blocked the request (Status 999) - Using URL data only")
            else:
                print(f"⚠️ Status code {response.status_code} - Using URL data only")
                
        except Exception as e:
            print(f"⚠️ Could not fetch profile: {str(e)[:50]} - Using URL data only")
        
        # Ensure we have a name
        if not profile_data.get('name'):
            profile_data['name'] = self._generate_name_from_url(clean_url)
        
        return profile_data
    
    def _extract_from_url(self, url):
        """
        Extract basic information from URL only
        """
        # Extract username from URL
        match = re.search(r'/in/([a-zA-Z0-9_-]+)', url)
        username = match.group(1) if match else 'unknown'
        
        # Generate name from username
        name = username.replace('-', ' ').replace('_', ' ').title()
        
        return {
            'linkedin_url': url,
            'name': name,
            'headline': f'LinkedIn Profile - {name}',
            'location': 'Information not available (LinkedIn blocks scrapers)',
            'about': 'Profile information could not be fetched. LinkedIn blocks automated requests.',
            'skills': '',
        }
    
    def _generate_name_from_url(self, url):
        """Generate a readable name from URL"""
        match = re.search(r'/in/([a-zA-Z0-9_-]+)', url)
        if match:
            username = match.group(1)
            # Convert to proper name format
            name_parts = username.replace('-', ' ').replace('_', ' ').split()
            name = ' '.join([part.capitalize() for part in name_parts])
            return name
        return "LinkedIn User"
    
    def _parse_html(self, html, url):
        """
        Parse HTML if we successfully get it
        """
        soup = BeautifulSoup(html, 'html.parser')
        
        data = {}
        
        # Try to find name
        name_selectors = ['h1', '.pv-top-card--list li', '.inline.t-24', '.text-heading-xlarge']
        for selector in name_selectors:
            elem = soup.select_one(selector)
            if elem and elem.get_text(strip=True):
                name = elem.get_text(strip=True)
                if len(name) > 2 and len(name) < 100:
                    data['name'] = name
                    break
        
        # Try to find headline
        headline_selectors = ['.pv-top-card-section__headline', '.text-body-medium', '.t-16']
        for selector in headline_selectors:
            elem = soup.select_one(selector)
            if elem and elem.get_text(strip=True):
                data['headline'] = elem.get_text(strip=True)[:200]
                break
        
        # Try to find location
        location_selectors = ['.pv-top-card-section__location', '.text-body-small']
        for selector in location_selectors:
            elem = soup.select_one(selector)
            if elem and elem.get_text(strip=True):
                data['location'] = elem.get_text(strip=True)
                break
        
        return data


class BatchLinkedInScraper:
    """Batch scraper for multiple profiles"""
    
    def __init__(self, delay_between_requests=2):
        self.scraper = LinkedInScraper()
        self.delay = delay_between_requests
    
    def scrape_multiple(self, profile_urls, progress_callback=None):
        """Scrape multiple profiles"""
        scraped_data = []
        processed_urls = set()  # To avoid duplicates
        
        total = len(profile_urls)
        
        for index, url in enumerate(profile_urls):
            print(f"\n📊 Progress: {index + 1}/{total}")
            
            # Clean URL first
            clean_url = self.scraper.clean_url(url)
            
            # Skip if we already processed this URL
            if clean_url in processed_urls:
                print(f"⏭️ Skipping duplicate: {clean_url}")
                continue
            
            if clean_url:
                processed_urls.add(clean_url)
                profile_data = self.scraper.scrape_profile(clean_url)
                
                if profile_data and profile_data.get('name'):
                    scraped_data.append(profile_data)
                    print(f"✅ Added: {profile_data['name']}")
                else:
                    print(f"⚠️ Failed to process: {url}")
            else:
                print(f"❌ Invalid URL: {url}")
            
            # Progress callback
            if progress_callback:
                progress_callback(index + 1, total)
            
            # Delay between requests
            if index < total - 1:
                time.sleep(self.delay)
        
        print(f"\n📊 Summary: Successfully processed {len(scraped_data)} unique profiles out of {total}")
        return scraped_data