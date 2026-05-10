# scraper/services/linkedin_scraper.py - Updated version

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
            'User-Agent': self.ua.random,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
        return session
    
    def scrape_profile(self, profile_url):
        """
        Scrape public information from LinkedIn profile
        Note: Most LinkedIn data requires login, so we get basic info only
        """
        try:
            print(f"🔄 Attempting to scrape: {profile_url}")
            
            # Add random delay
            time.sleep(random.uniform(2, 4))
            
            response = self.session.get(profile_url, timeout=self.timeout, allow_redirects=True)
            
            if response.status_code == 200:
                return self._parse_profile_basic(response.text, profile_url)
            elif response.status_code == 404:
                print(f"❌ Profile not found: {profile_url}")
                return None
            elif response.status_code == 403 or response.status_code == 429:
                print(f"⚠️ Access denied or rate limited for {profile_url}")
                # Try to extract from URL as fallback
                return self._fallback_extract(profile_url)
            else:
                print(f"⚠️ Status code {response.status_code} for {profile_url}")
                return self._fallback_extract(profile_url)
                
        except Exception as e:
            print(f"❌ Error scraping {profile_url}: {str(e)}")
            return self._fallback_extract(profile_url)
    
    def _parse_profile_basic(self, html, url):
        """Parse basic profile info from HTML"""
        soup = BeautifulSoup(html, 'html.parser')
        
        profile_data = {
            'linkedin_url': url,
            'name': None,
            'headline': None,
            'location': None,
            'about': None,
            'skills': None,
        }
        
        # Try multiple selectors for name
        name_selectors = [
            'h1',
            '.pv-top-card--list li',
            '.inline.t-24',
            '.text-heading-xlarge',
            '[data-anonymize="person-name"]'
        ]
        
        for selector in name_selectors:
            try:
                elem = soup.select_one(selector)
                if elem and elem.get_text(strip=True):
                    name = elem.get_text(strip=True)
                    if len(name) > 2 and len(name) < 100:
                        profile_data['name'] = name
                        break
            except:
                continue
        
        # If name not found, extract from URL
        if not profile_data['name']:
            match = re.search(r'/in/([^/?]+)', url)
            if match:
                username = match.group(1).replace('-', ' ').replace('_', ' ')
                profile_data['name'] = username.title()
        
        # Extract headline/title
        headline_selectors = [
            '.pv-top-card-section__headline',
            '.text-body-medium',
            '.t-16',
            '[data-anonymize="title"]'
        ]
        
        for selector in headline_selectors:
            try:
                elem = soup.select_one(selector)
                if elem and elem.get_text(strip=True):
                    profile_data['headline'] = elem.get_text(strip=True)[:200]
                    break
            except:
                continue
        
        # Extract location
        location_selectors = [
            '.pv-top-card-section__location',
            '.text-body-small',
            '[data-anonymize="location"]'
        ]
        
        for selector in location_selectors:
            try:
                elem = soup.select_one(selector)
                if elem and elem.get_text(strip=True):
                    profile_data['location'] = elem.get_text(strip=True)
                    break
            except:
                continue
        
        # Clean up data
        if profile_data['name']:
            print(f"✅ Extracted: {profile_data['name']}")
        else:
            print(f"⚠️ Could not extract name from {url}")
        
        return profile_data
    
    def _fallback_extract(self, url):
        """Extract basic info from URL when scraping fails"""
        match = re.search(r'/in/([^/?]+)', url)
        if match:
            username = match.group(1)
            name = username.replace('-', ' ').replace('_', ' ').title()
            
            return {
                'linkedin_url': url,
                'name': name,
                'headline': f'LinkedIn Profile - {name}',
                'location': 'Not specified',
                'about': None,
                'skills': None,
            }
        return None


class BatchLinkedInScraper:
    """Batch scraper for multiple profiles"""
    
    def __init__(self, delay_between_requests=3):
        self.scraper = LinkedInScraper()
        self.delay = delay_between_requests
    
    def scrape_multiple(self, profile_urls, progress_callback=None):
        """Scrape multiple profiles"""
        scraped_data = []
        total = len(profile_urls)
        
        for index, url in enumerate(profile_urls):
            print(f"\n📊 Progress: {index + 1}/{total}")
            
            profile_data = self.scraper.scrape_profile(url)
            
            if profile_data and profile_data.get('name'):
                scraped_data.append(profile_data)
                print(f"✅ Successfully scraped: {profile_data['name']}")
            else:
                print(f"⚠️ Failed to scrape: {url}")
            
            # Progress callback
            if progress_callback:
                progress_callback(index + 1, total)
            
            # Delay between requests
            if index < total - 1:
                time.sleep(self.delay)
        
        print(f"\n📊 Summary: Scraped {len(scraped_data)} out of {total} profiles")
        return scraped_data