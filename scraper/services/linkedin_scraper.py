# scraper/services/linkedin_scraper.py

"""
LinkedIn Profile Scraper Module
This module scrapes public LinkedIn profile information
"""

import requests
import re
import time
from bs4 import BeautifulSoup
from fake_useragent import UserAgent

class LinkedInScraper:
    """
    LinkedIn profile scraper for public information
    """
    
    def __init__(self):
        self.ua = UserAgent()
        self.timeout = 20
    
    def get_random_headers(self):
        """Generate random headers"""
        return {
            'User-Agent': self.ua.random,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        }
    
    def scrape_profile(self, profile_url):
        """
        Scrape public information from LinkedIn profile
        
        Args:
            profile_url (str): LinkedIn profile URL
        
        Returns:
            dict: Profile information or None if failed
        """
        try:
            print(f"🔄 Scraping: {profile_url}")
            
            headers = self.get_random_headers()
            response = requests.get(
                profile_url, 
                headers=headers, 
                timeout=self.timeout,
                allow_redirects=True
            )
            
            if response.status_code == 200:
                return self._parse_profile(response.text, profile_url)
            elif response.status_code == 404:
                print(f"❌ Profile not found: {profile_url}")
                return None
            elif response.status_code == 429:
                print(f"⚠️ Rate limited! Need to wait...")
                time.sleep(10)
                return None
            else:
                print(f"⚠️ Status code {response.status_code} for {profile_url}")
                return None
                
        except Exception as e:
            print(f"❌ Error scraping {profile_url}: {e}")
            return None
    
    def _parse_profile(self, html, url):
        """
        Parse profile HTML to extract information
        
        Note: LinkedIn's HTML structure is complex and changes frequently
        This is a basic implementation for public information
        """
        soup = BeautifulSoup(html, 'html.parser')
        
        profile_data = {
            'linkedin_url': url,
            'name': None,
            'headline': None,
            'location': None,
            'about': None,
            'skills': None,
        }
        
        # Try to find name - multiple possible locations
        name_selectors = [
            'h1',
            '.pv-top-card-section__name',
            '.inline.t-24.t-black.t-normal',
            '.text-heading-xlarge'
        ]
        
        for selector in name_selectors:
            name_elem = soup.select_one(selector)
            if name_elem and name_elem.get_text(strip=True):
                profile_data['name'] = name_elem.get_text(strip=True)
                break
        
        # Try to find headline/title
        headline_selectors = [
            '.pv-top-card-section__headline',
            '.text-body-medium',
            '.t-16.t-black.t-normal',
            '.top-card-layout__headline'
        ]
        
        for selector in headline_selectors:
            headline_elem = soup.select_one(selector)
            if headline_elem and headline_elem.get_text(strip=True):
                profile_data['headline'] = headline_elem.get_text(strip=True)
                break
        
        # Try to find location
        location_selectors = [
            '.pv-top-card-section__location',
            '.text-body-small',
            '.top-card-layout__first-subline'
        ]
        
        for selector in location_selectors:
            location_elem = soup.select_one(selector)
            if location_elem and location_elem.get_text(strip=True):
                profile_data['location'] = location_elem.get_text(strip=True)
                break
        
        # Try to find about section
        about_elem = soup.select_one('.pv-about__summary-text, .about-section, .break-words')
        if about_elem:
            profile_data['about'] = about_elem.get_text(strip=True)[:500]  # Limit length
        
        # Extract name from URL if not found
        if not profile_data['name']:
            # Extract username from URL
            match = re.search(r'/in/([^/?]+)', url)
            if match:
                username = match.group(1).replace('-', ' ').replace('_', ' ')
                profile_data['name'] = username.title()
        
        print(f"✅ Scraped: {profile_data['name']}")
        return profile_data


class BatchLinkedInScraper:
    """
    Batch scraper for multiple LinkedIn profiles
    """
    
    def __init__(self, delay_between_requests=3):
        self.scraper = LinkedInScraper()
        self.delay = delay_between_requests
    
    def scrape_multiple(self, profile_urls, progress_callback=None):
        """
        Scrape multiple profiles
        
        Args:
            profile_urls (list): List of profile URLs
            progress_callback (function): Callback for progress updates
        
        Returns:
            list: List of scraped profile data
        """
        scraped_data = []
        total = len(profile_urls)
        
        for index, url in enumerate(profile_urls):
            profile_data = self.scraper.scrape_profile(url)
            
            if profile_data:
                scraped_data.append(profile_data)
            
            # Progress update
            if progress_callback:
                progress_callback(index + 1, total)
            
            # Delay to avoid rate limiting
            if index < total - 1:
                time.sleep(self.delay)
        
        print(f"📊 Successfully scraped {len(scraped_data)} out of {total} profiles")
        return scraped_data