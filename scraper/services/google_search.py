# scraper/services/google_search.py

"""
Google Search Scraper Module
This module handles Google search for LinkedIn profiles
"""

import requests
import time
import re
from bs4 import BeautifulSoup
from urllib.parse import quote_plus
from fake_useragent import UserAgent
import random

class GoogleSearchScraper:
    """
    Google Search Scraper class for finding LinkedIn profiles
    """
    
    def __init__(self):
        """Initialize scraper with headers and settings"""
        self.ua = UserAgent()
        self.base_url = "https://www.google.com/search"
        self.timeout = 30
        self.retry_count = 3
        
    def get_random_headers(self):
        """Generate random headers to avoid blocking"""
        return {
            'User-Agent': self.ua.random,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'max-age=0',
            'TE': 'Trailers',
        }
    
    def search_linkedin_profiles(self, keyword, max_results=30):
        """
        Search Google for LinkedIn profiles
        
        Args:
            keyword (str): Search keyword (e.g., "Django Developer Bangladesh")
            max_results (int): Maximum number of results to return
        
        Returns:
            list: List of LinkedIn profile URLs
        """
        
        # Construct search query
        search_query = f"site:linkedin.com/in {keyword}"
        
        # Encode query for URL
        encoded_query = quote_plus(search_query)
        
        all_links = []
        
        # Google shows ~10 results per page
        num_pages = min((max_results // 10) + 1, 5)  # Max 5 pages
        
        for page in range(num_pages):
            start = page * 10
            url = f"{self.base_url}?q={encoded_query}&start={start}"
            
            print(f"🔍 Searching page {page + 1}: {url}")
            
            # Get page with retry logic
            html_content = self._fetch_page(url)
            
            if html_content:
                # Extract links from page
                links = self._extract_linkedin_links(html_content)
                all_links.extend(links)
                
                # Stop if we have enough results
                if len(all_links) >= max_results:
                    break
                
                # Delay between requests to be polite
                time.sleep(random.uniform(2, 4))
            else:
                print(f"❌ Failed to fetch page {page + 1}")
                break
        
        # Remove duplicates and limit results
        unique_links = list(dict.fromkeys(all_links))
        return unique_links[:max_results]
    
    def _fetch_page(self, url):
        """
        Fetch page with retry logic
        
        Args:
            url (str): URL to fetch
        
        Returns:
            str: HTML content or None
        """
        for attempt in range(self.retry_count):
            try:
                headers = self.get_random_headers()
                
                response = requests.get(
                    url, 
                    headers=headers, 
                    timeout=self.timeout,
                    allow_redirects=True
                )
                
                if response.status_code == 200:
                    print(f"✅ Successfully fetched: {url[:50]}...")
                    return response.text
                elif response.status_code == 429:  # Too many requests
                    print(f"⚠️ Rate limited! Waiting longer...")
                    time.sleep(random.uniform(10, 15))
                else:
                    print(f"⚠️ Status code {response.status_code} for {url}")
                    
            except requests.exceptions.Timeout:
                print(f"⏰ Timeout on attempt {attempt + 1}")
            except requests.exceptions.ConnectionError:
                print(f"🔌 Connection error on attempt {attempt + 1}")
            except Exception as e:
                print(f"❌ Error: {str(e)}")
            
            # Wait before retry
            if attempt < self.retry_count - 1:
                time.sleep(random.uniform(3, 6))
        
        return None
    
    def _extract_linkedin_links(self, html):
        """
        Extract LinkedIn profile links from HTML
        
        Args:
            html (str): HTML content
        
        Returns:
            list: List of LinkedIn URLs
        """
        soup = BeautifulSoup(html, 'html.parser')
        links = []
        
        # Find all anchor tags
        for a_tag in soup.find_all('a', href=True):
            href = a_tag['href']
            
            # Look for LinkedIn URLs
            if 'linkedin.com/in/' in href:
                # Clean the URL (remove tracking parameters)
                clean_url = self._clean_linkedin_url(href)
                if clean_url and clean_url not in links:
                    links.append(clean_url)
        
        print(f"📊 Found {len(links)} LinkedIn profile links")
        return links
    
    def _clean_linkedin_url(self, url):
        """
        Clean LinkedIn URL by removing tracking parameters
        
        Args:
            url (str): Raw URL
        
        Returns:
            str: Cleaned URL or None
        """
        try:
            # Extract the actual LinkedIn URL from Google's redirect
            if '/url?q=' in url:
                # Google redirect URL format
                match = re.search(r'/url\?q=(https?://[^&]+)', url)
                if match:
                    url = match.group(1)
            
            # URL decode
            from urllib.parse import unquote
            url = unquote(url)
            
            # Extract just the profile part
            match = re.search(r'(https?://(?:www\.)?linkedin\.com/in/[^/?]+)', url)
            if match:
                return match.group(1)
            
            return None
            
        except Exception as e:
            print(f"Error cleaning URL {url}: {e}")
            return None


class SafeGoogleSearch(GoogleSearchScraper):
    """
    Enhanced version with rate limiting and proxy support
    """
    
    def __init__(self, use_proxy=False, proxy_list=None):
        super().__init__()
        self.use_proxy = use_proxy
        self.proxy_list = proxy_list or []
        self.request_count = 0
        self.last_request_time = 0
    
    def _get_proxy(self):
        """Get random proxy from list"""
        if self.use_proxy and self.proxy_list:
            return {'http': random.choice(self.proxy_list)}
        return None
    
    def _respect_rate_limit(self):
        """Ensure we don't make too many requests"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        # Minimum 2 seconds between requests
        if time_since_last < 2:
            time.sleep(2 - time_since_last)
        
        self.last_request_time = time.time()
    
    def _fetch_page(self, url):
        """Override to add rate limiting and proxy support"""
        self._respect_rate_limit()
        self.request_count += 1
        
        if self.request_count % 10 == 0:
            print(f"📊 Made {self.request_count} requests so far")
            # Add longer delay after every 10 requests
            time.sleep(random.uniform(5, 8))
        
        return super()._fetch_page(url)