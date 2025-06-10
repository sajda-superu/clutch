#!/usr/bin/env python3
"""
Clutch Profile Scraper - Extract detailed information from individual company profiles

This script takes a Clutch profile URL and extracts all key company information including:
- Company name, description, reviews
- Service lines and percentages  
- Pricing, team size, location
- Contact information and social media
- And much more

Usage:
    python clutch_profile_scraper.py --url "https://clutch.co/profile/100-shapes"
    python clutch_profile_scraper.py --batch-file urls.txt --output results.json
"""

import requests
from bs4 import BeautifulSoup
import json
import csv
import re
import time
import argparse
from urllib.parse import urljoin, urlparse
from typing import Dict, List, Optional
import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import logging
import random

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ClutchProfileScraper:
    def __init__(self, use_selenium=True, headless=True, output_file=None):
        self.use_selenium = use_selenium
        self.headless = headless
        self.session = None
        self.driver = None
        self.current_output_file = output_file
        
        if use_selenium:
            self.setup_selenium()
        else:
            self.setup_requests()
    
    def setup_selenium(self):
        """Setup Selenium WebDriver for handling JavaScript and anti-bot measures"""
        chrome_options = Options()
        if self.headless:
            chrome_options.add_argument("--headless=new")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            # Add additional browser fingerprinting evasion
            self.driver.execute_script("""
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [1, 2, 3, 4, 5]
                });
                Object.defineProperty(navigator, 'languages', {
                    get: () => ['en-US', 'en']
                });
            """)
            logger.info("Selenium WebDriver initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Selenium: {e}")
            logger.info("Falling back to requests method")
            self.use_selenium = False
            self.setup_requests()
    
    def setup_requests(self):
        """Setup requests session with headers"""
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
    
    def get_page_content(self, url: str) -> Optional[str]:
        """Get page content using either Selenium or requests"""
        try:
            if self.use_selenium and self.driver:
                logger.info(f"Fetching {url} with Selenium...")
                self.driver.get(url)
                # Add random mouse movements and scrolling
                self.driver.execute_script(f"window.scrollTo(0, {random.randint(100, 500)});")
                time.sleep(random.uniform(1, 2))
                
                # Wait for specific elements that indicate the page has loaded properly
                try:
                    WebDriverWait(self.driver, 15).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "h1, h2, .company-name, .profile-header"))
                    )
                    # Add a small random delay to mimic human behavior
                    time.sleep(2 + random.random() * 2)
                    
                    # Scroll down slowly
                    total_height = self.driver.execute_script("return document.body.scrollHeight")
                    for i in range(0, total_height, random.randint(100, 200)):
                        self.driver.execute_script(f"window.scrollTo(0, {i});")
                        time.sleep(random.uniform(0.1, 0.3))
                    
                    return self.driver.page_source
                except TimeoutException:
                    logger.warning(f"Timeout waiting for page elements at {url}")
                    return self.driver.page_source
            else:
                logger.info(f"Fetching {url} with requests...")
                response = self.session.get(url, timeout=30)
                response.raise_for_status()
                return response.text
        except Exception as e:
            logger.error(f"Error fetching {url}: {e}")
            return None
    
    def extract_company_info(self, soup: BeautifulSoup, url: str) -> Dict:
        """Extract all company information from the profile page"""
        company_data = {
            'url': url,
            'company_name': '',
            'tagline': '',
            'description': '',
            'reviews_count': 0,
            'reviews_rating': 0.0,
            'min_project_size': '',
            'hourly_rate': '',
            'employees': '',
            'year_founded': '',
            'location': '',
            'services': [],
            'industries': [],
            'clients': [],
            'contact_info': {},
            'social_media': {},
            'additional_info': {}
        }
        
        try:
            # Company name - try multiple selectors
            name_selectors = [
                'h1.company-name',
                'h1.profile-name',
                'h1.header-company-title',
                'h1',
                '.company-name',
                '.profile-name',
                '.header-company-title'
            ]
            
            for selector in name_selectors:
                name_elem = soup.select_one(selector)
                if name_elem and name_elem.get_text(strip=True) and name_elem.get_text(strip=True) != 'clutch.co':
                    company_data['company_name'] = name_elem.get_text(strip=True)
                    break
            
            # If no company name found, try to extract from URL
            if not company_data['company_name'] or company_data['company_name'] == 'clutch.co':
                url_parts = url.split('/')
                if len(url_parts) > 0:
                    company_name = url_parts[-1].replace('-', ' ').title()
                    company_data['company_name'] = company_name
            
            # Tagline/Description
            tagline_selectors = [
                'h2.tagline',
                'h2.subtitle',
                'h2.description',
                '.tagline',
                '.subtitle',
                '.description',
                '.company-description'
            ]
            
            for selector in tagline_selectors:
                tagline_elem = soup.select_one(selector)
                if tagline_elem:
                    company_data['tagline'] = tagline_elem.get_text(strip=True)
                    break
            
            # Main description
            desc_selectors = [
                'div[class*="description"]',
                'div[class*="about"]',
                'p[class*="description"]',
                '.company-description',
                '.profile-description',
                '.about-company'
            ]
            
            for selector in desc_selectors:
                desc_elem = soup.select_one(selector)
                if desc_elem:
                    company_data['description'] = desc_elem.get_text(strip=True)
                    break
            
            # Reviews
            reviews_selectors = [
                '.reviews-count',
                '.review-count',
                '.rating-count',
                '[class*="review"]',
                '[class*="rating"]'
            ]
            
            for selector in reviews_selectors:
                reviews_elem = soup.select_one(selector)
                if reviews_elem:
                    reviews_text = reviews_elem.get_text()
                    review_match = re.search(r'(\d+)\s*review', reviews_text, re.IGNORECASE)
                    if review_match:
                        company_data['reviews_count'] = int(review_match.group(1))
                        break
            
            # Rating
            rating_selectors = [
                '.rating',
                '.stars',
                '.review-rating',
                '[class*="rating"]',
                '[class*="stars"]'
            ]
            
            for selector in rating_selectors:
                rating_elem = soup.select_one(selector)
                if rating_elem:
                    rating_text = rating_elem.get_text()
                    rating_match = re.search(r'(\d+\.?\d*)', rating_text)
                    if rating_match:
                        company_data['reviews_rating'] = float(rating_match.group(1))
                        break
            
            # Project size, hourly rate, employees, etc.
            self._extract_company_stats(soup, company_data)
            
            # Services
            company_data['services'] = self._extract_services(soup)
            
            # Location
            location_selectors = [
                '.location',
                '.address',
                '.company-location',
                '[class*="location"]',
                '[class*="address"]'
            ]
            
            for selector in location_selectors:
                location_elem = soup.select_one(selector)
                if location_elem:
                    company_data['location'] = location_elem.get_text(strip=True)
                    break
            
            # Contact and social media
            company_data['contact_info'] = self._extract_contact_info(soup)
            company_data['social_media'] = self._extract_social_media(soup)
            
            logger.info(f"Successfully extracted data for: {company_data['company_name']}")
            
        except Exception as e:
            logger.error(f"Error extracting company info: {e}")
        
        return company_data
    
    def _extract_company_stats(self, soup: BeautifulSoup, company_data: Dict):
        """Extract company statistics like project size, hourly rate, etc."""
        page_text = soup.get_text()
        
        # Min project size
        project_size_match = re.search(r'\$([0-9,]+\+?)', page_text)
        if project_size_match:
            company_data['min_project_size'] = f"${project_size_match.group(1)}"
        
        # Hourly rate
        hourly_rate_match = re.search(r'\$(\d+)\s*-\s*\$(\d+)\s*/\s*hr', page_text)
        if hourly_rate_match:
            company_data['hourly_rate'] = f"${hourly_rate_match.group(1)} - ${hourly_rate_match.group(2)} / hr"
        
        # Employees
        employees_match = re.search(r'(\d+)\s*-\s*(\d+)', page_text)
        if employees_match:
            company_data['employees'] = f"{employees_match.group(1)} - {employees_match.group(2)}"
        
        # Year founded
        founded_match = re.search(r'Founded\s*(\d{4})', page_text, re.IGNORECASE)
        if founded_match:
            company_data['year_founded'] = founded_match.group(1)
    
    def _extract_services(self, soup: BeautifulSoup) -> List[Dict]:
        """Extract service lines and percentages"""
        services = []
        
        # Look for service percentages in text
        page_text = soup.get_text()
        service_patterns = [
            r'([A-Za-z\s&/]+)\s*(\d+)%',
            r'(\d+)%\s*([A-Za-z\s&/]+)',
        ]
        
        for pattern in service_patterns:
            matches = re.findall(pattern, page_text)
            for match in matches:
                if len(match) == 2:
                    if match[0].isdigit():
                        percentage, service = match[0], match[1]
                    else:
                        service, percentage = match[0], match[1]
                    
                    services.append({
                        'service': service.strip(),
                        'percentage': f"{percentage}%"
                    })
        
        return services
    
    def _extract_contact_info(self, soup: BeautifulSoup) -> Dict:
        """Extract contact information"""
        contact_info = {}
        
        # Email
        email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        emails = re.findall(email_pattern, soup.get_text())
        if emails:
            contact_info['email'] = emails[0]
        
        # Phone
        phone_pattern = r'[\+]?[1-9]?[0-9]{7,14}'
        phones = re.findall(phone_pattern, soup.get_text())
        if phones:
            contact_info['phone'] = phones[0]
        
        # Website
        website_links = soup.find_all('a', href=re.compile(r'^https?://'))
        for link in website_links:
            href = link.get('href', '')
            if 'clutch.co' not in href and any(text in link.get_text().lower() for text in ['website', 'visit']):
                contact_info['website'] = href
                break
        
        return contact_info
    
    def _extract_social_media(self, soup: BeautifulSoup) -> Dict:
        """Extract social media links"""
        social_media = {}
        
        social_platforms = {
            'linkedin': r'linkedin\.com',
            'facebook': r'facebook\.com',
            'twitter': r'twitter\.com|x\.com',
            'instagram': r'instagram\.com'
        }
        
        for platform, pattern in social_platforms.items():
            links = soup.find_all('a', href=re.compile(pattern))
            if links:
                social_media[platform] = links[0].get('href')
        
        return social_media
    
    def scrape_profile(self, url: str) -> Dict:
        """Scrape a single profile and return extracted data"""
        logger.info(f"Scraping profile: {url}")
        
        # Get page content
        html_content = self.get_page_content(url)
        if not html_content:
            return {'error': 'Failed to fetch page content', 'url': url}
        
        # Parse with BeautifulSoup
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Extract company information
        company_data = self.extract_company_info(soup, url)
        
        return company_data
    
    def scrape_multiple_profiles(self, urls: List[str], delay: float = 2.0) -> List[Dict]:
        """Scrape multiple profiles with delay between requests"""
        results = []
        total = len(urls)
        
        # Load existing results if file exists
        if os.path.exists(self.current_output_file):
            try:
                with open(self.current_output_file, 'r', encoding='utf-8') as f:
                    results = json.load(f)
                logger.info(f"Loaded {len(results)} existing results from {self.current_output_file}")
            except Exception as e:
                logger.error(f"Error loading existing results: {e}")
        
        for i, url in enumerate(urls, 1):
            logger.info(f"Processing profile {i}/{total}: {url}")
            
            # Skip if URL already processed
            if any(r.get('url') == url for r in results):
                logger.info(f"Skipping already processed URL: {url}")
                continue
                
            try:
                result = self.scrape_profile(url)
                if result:
                    results.append(result)
                    # Save immediately after each successful scrape
                    self.save_results(results, self.current_output_file)
                    logger.info(f"Saved data for {result.get('company_name', url)}")
            except Exception as e:
                logger.error(f"Error processing {url}: {e}")
            
            if i < total:
                logger.info(f"Waiting {delay} seconds before next request...")
                time.sleep(delay)
        
        return results
    
    def save_results(self, results: List[Dict], output_file: str):
        """Save results to JSON file"""
        try:
            # Store the output file path for incremental saving
            self.current_output_file = output_file
            
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(output_file), exist_ok=True)
            
            # Save with pretty formatting
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Results saved to: {output_file}")
        except Exception as e:
            logger.error(f"Error saving results: {e}")
    
    def __del__(self):
        """Clean up resources"""
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass

def main():
    parser = argparse.ArgumentParser(description='Scrape Clutch.co company profiles')
    parser.add_argument('--url', help='Single URL to scrape')
    parser.add_argument('--batch-file', help='File containing list of URLs to scrape')
    parser.add_argument('--output', help='Output file path (JSON or CSV)')
    parser.add_argument('--delay', type=float, default=2.0, help='Delay between requests in seconds')
    parser.add_argument('--no-selenium', action='store_true', help='Disable Selenium (use requests instead)')
    parser.add_argument('--no-headless', action='store_true', help='Disable headless mode for Selenium')
    parser.add_argument('--batch-size', type=int, default=100, help='Number of URLs to process in each batch')
    args = parser.parse_args()

    if not args.url and not args.batch_file:
        parser.error("Either --url or --batch-file must be provided")

    if not args.output:
        parser.error("--output file path must be provided")

    # Initialize scraper with output file
    scraper = ClutchProfileScraper(
        use_selenium=not args.no_selenium,
        headless=not args.no_headless,
        output_file=args.output
    )

    try:
        if args.url:
            result = scraper.scrape_profile(args.url)
            if result:
                scraper.save_results([result], args.output)
        else:
            with open(args.batch_file, 'r') as f:
                all_urls = [line.strip() for line in f if line.strip()]
            
            # Process URLs in batches
            total_urls = len(all_urls)
            for i in range(0, total_urls, args.batch_size):
                batch_urls = all_urls[i:i + args.batch_size]
                logger.info(f"Processing batch {i//args.batch_size + 1} of {(total_urls + args.batch_size - 1)//args.batch_size}")
                logger.info(f"URLs {i+1} to {min(i+args.batch_size, total_urls)} of {total_urls}")
                
                results = scraper.scrape_multiple_profiles(batch_urls, delay=args.delay)
                scraper.save_results(results, args.output)
                
                # Add a longer delay between batches
                if i + args.batch_size < total_urls:
                    delay = 10  # 10 seconds between batches
                    logger.info(f"Batch completed. Waiting {delay} seconds before next batch...")
                    time.sleep(delay)
    except Exception as e:
        logger.error(f"Error during scraping: {e}")
    finally:
        if scraper.driver:
            scraper.driver.quit()

if __name__ == "__main__":
    main() 