# scraper/services/google_search_selenium.py

"""
Google Search Scraper using Selenium
This bypasses anti-bot protection by using a real browser
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
import time
import re
import random
from urllib.parse import quote_plus

class SeleniumGoogleSearch:
    """
    Google search using Selenium with real browser
    """
    
    def __init__(self, headless=False):
        """
        Initialize Chrome driver
        
        Args:
            headless (bool): Run browser in background if True
        """
        self.headless = headless
        self.driver = None
        self.setup_driver()
    
    def setup_driver(self):
        """Setup Chrome driver with optimal settings"""
        chrome_options = Options()
        
        # Anti-detection options
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # Performance options
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        
        # Window size
        chrome_options.add_argument("--window-size=1920,1080")
        
        # User agent
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        if self.headless:
            chrome_options.add_argument("--headless")
        
        # Auto-download and setup ChromeDriver
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        
        # Execute script to hide webdriver property
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        print("✅ Chrome driver initialized successfully")
    
    def search_linkedin_profiles(self, keyword, max_results=30):
        """
        Search Google for LinkedIn profiles
        
        Args:
            keyword (str): Search keyword
            max_results (int): Maximum results to return
        
        Returns:
            list: List of LinkedIn profile URLs
        """
        # Construct search query
        search_query = f"site:linkedin.com/in {keyword}"
        encoded_query = quote_plus(search_query)
        
        all_links = []
        current_page = 0
        
        try:
            while len(all_links) < max_results and current_page < 5:
                # Construct URL
                start = current_page * 10
                url = f"https://www.google.com/search?q={encoded_query}&start={start}"
                
                print(f"🔍 Searching page {current_page + 1}: {url}")
                
                # Load the page
                self.driver.get(url)
                
                # Wait for results to load
                time.sleep(random.uniform(3, 5))
                
                # Extract links
                links = self._extract_linkedin_links()
                
                if not links:
                    print(f"⚠️ No links found on page {current_page + 1}")
                    # Check if we hit a captcha
                    if "captcha" in self.driver.page_source.lower():
                        print("❌ CAPTCHA detected! Please solve manually or use proxies")
                        break
                
                all_links.extend(links)
                print(f"📊 Found {len(links)} links on page {current_page + 1}")
                
                # Remove duplicates
                all_links = list(dict.fromkeys(all_links))
                
                # Stop if we have enough
                if len(all_links) >= max_results:
                    break
                
                current_page += 1
                
                # Random delay between pages
                if current_page < 5:
                    delay = random.uniform(5, 8)
                    print(f"⏰ Waiting {delay:.1f} seconds before next page...")
                    time.sleep(delay)
            
            print(f"✅ Total unique LinkedIn profiles found: {len(all_links)}")
            return all_links[:max_results]
            
        except Exception as e:
            print(f"❌ Error during search: {str(e)}")
            return []
    
    def _extract_linkedin_links(self):
        """
        Extract LinkedIn profile links from current page
        """
        links = []
        
        try:
            # Wait for search results
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Find all anchor tags
            elements = self.driver.find_elements(By.TAG_NAME, "a")
            
            for element in elements:
                try:
                    href = element.get_attribute("href")
                    if href and 'linkedin.com/in/' in href:
                        clean_url = self._clean_linkedin_url(href)
                        if clean_url and clean_url not in links:
                            links.append(clean_url)
                except:
                    continue
                    
        except Exception as e:
            print(f"Error extracting links: {e}")
        
        return links
    
    def _clean_linkedin_url(self, url):
        """
        Clean LinkedIn URL
        """
        try:
            # Handle Google redirect URLs
            if '/url?q=' in url:
                match = re.search(r'/url\?q=(https?://[^&]+)', url)
                if match:
                    url = match.group(1)
            
            # Decode URL
            from urllib.parse import unquote
            url = unquote(url)
            
            # Extract clean LinkedIn profile URL
            match = re.search(r'(https?://(?:www\.)?linkedin\.com/in/[^/?]+)', url)
            if match:
                return match.group(1)
            
            return None
            
        except Exception as e:
            print(f"Error cleaning URL: {e}")
            return None
    
    def close(self):
        """Close the browser"""
        if self.driver:
            self.driver.quit()
            print("✅ Browser closed")


class BetterGoogleSearch:
    """
    Alternative: Use requests with better headers and cookies
    """
    
    def __init__(self):
        self.session = requests.Session()
        self.setup_session()
    
    def setup_session(self):
        """Setup session with proper headers"""
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
    
    def search_with_selenium_fallback(self, keyword, max_results=20):
        """
        Try normal request first, fallback to selenium if fails
        """
        # First try with requests
        try:
            from .google_search import GoogleSearchScraper
            scraper = GoogleSearchScraper()
            results = scraper.search_linkedin_profiles(keyword, max_results)
            
            if results:
                print("✅ Success with normal requests!")
                return results
        except Exception as e:
            print(f"⚠️ Normal request failed: {e}")
        
        # Fallback to selenium
        print("🔄 Falling back to Selenium...")
        selenium_scraper = SeleniumGoogleSearch(headless=False)
        results = selenium_scraper.search_linkedin_profiles(keyword, max_results)
        selenium_scraper.close()
        
        return results