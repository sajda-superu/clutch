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

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ClutchProfileScraper:
    def __init__(self, use_selenium=True, headless=True):
        self.use_selenium = use_selenium
        self.headless = headless
        self.session = None
        self.driver = None
        
        if use_selenium:
            self.setup_selenium()
        else:
            self.setup_requests()
    
    def setup_selenium(self):
        """Setup Selenium WebDriver for handling JavaScript and anti-bot measures"""
        chrome_options = Options()
        if self.headless:
            chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        try:
            self.driver = webdriver.Chrome(options=chrome_options)
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
                # Wait for page to load
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
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
            # Company name
            name_elem = soup.find('h1') or soup.find('h2')
            if name_elem:
                company_data['company_name'] = name_elem.get_text(strip=True)
            
            # Tagline/Description
            tagline_elem = soup.find('h2', {'class': re.compile(r'tagline|subtitle|description')})
            if tagline_elem:
                company_data['tagline'] = tagline_elem.get_text(strip=True)
            
            # Main description
            desc_selectors = [
                'div[class*="description"]',
                'div[class*="about"]',
                'p[class*="description"]',
                '.company-description',
                '.profile-description'
            ]
            for selector in desc_selectors:
                desc_elem = soup.select_one(selector)
                if desc_elem:
                    company_data['description'] = desc_elem.get_text(strip=True)
                    break
            
            # Reviews
            reviews_text = soup.get_text()
            review_match = re.search(r'(\d+)\s*review', reviews_text, re.IGNORECASE)
            if review_match:
                company_data['reviews_count'] = int(review_match.group(1))
            
            # Rating (look for star ratings)
            rating_elem = soup.find(attrs={'class': re.compile(r'rating|stars')})
            if rating_elem:
                rating_text = rating_elem.get_text()
                rating_match = re.search(r'(\d+\.?\d*)', rating_text)
                if rating_match:
                    company_data['reviews_rating'] = float(rating_match.group(1))
            
            # Project size, hourly rate, employees, etc.
            self._extract_company_stats(soup, company_data)
            
            # Services
            company_data['services'] = self._extract_services(soup)
            
            # Location
            location_patterns = [
                r'([A-Za-z\s]+,\s*[A-Za-z\s]+)',  # City, Country
                r'([A-Za-z\s]+,\s*[A-Z]{2})',     # City, State
            ]
            page_text = soup.get_text()
            for pattern in location_patterns:
                location_match = re.search(pattern, page_text)
                if location_match:
                    company_data['location'] = location_match.group(1).strip()
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
        
        for i, url in enumerate(urls, 1):
            logger.info(f"Processing profile {i}/{len(urls)}: {url}")
            
            result = self.scrape_profile(url)
            results.append(result)
            
            # Add delay between requests
            if i < len(urls):
                logger.info(f"Waiting {delay} seconds before next request...")
                time.sleep(delay)
        
        return results
    
    def save_results(self, results: List[Dict], output_file: str):
        """Save results to JSON or CSV file"""
        if not results:
            logger.warning("No results to save")
            return
        
        file_ext = os.path.splitext(output_file)[1].lower()
        
        if file_ext == '.json':
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
        elif file_ext == '.csv':
            # Flatten the data for CSV
            fieldnames = set()
            for result in results:
                fieldnames.update(result.keys())
            
            with open(output_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=list(fieldnames))
                writer.writeheader()
                for result in results:
                    # Convert complex fields to strings
                    flattened = {}
                    for key, value in result.items():
                        if isinstance(value, (dict, list)):
                            flattened[key] = json.dumps(value)
                        else:
                            flattened[key] = value
                    writer.writerow(flattened)
        
        logger.info(f"Results saved to: {output_file}")
    
    def __del__(self):
        """Clean up resources"""
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass

def main():
    parser = argparse.ArgumentParser(description="Scrape Clutch.co company profiles")
    parser.add_argument('--url', help='Single profile URL to scrape')
    parser.add_argument('--batch-file', help='File containing list of URLs to scrape')
    parser.add_argument('--output', default='clutch_profiles.json', help='Output file (JSON or CSV)')
    parser.add_argument('--delay', type=float, default=2.0, help='Delay between requests (seconds)')
    parser.add_argument('--no-selenium', action='store_true', help='Use requests instead of Selenium')
    parser.add_argument('--sample-size', type=int, help='Limit number of profiles to scrape (for testing)')
    
    args = parser.parse_args()
    
    # Initialize scraper
    scraper = ClutchProfileScraper(use_selenium=not args.no_selenium)
    
    try:
        if args.url:
            # Single URL
            result = scraper.scrape_profile(args.url)
            scraper.save_results([result], args.output)
            
        elif args.batch_file:
            # Multiple URLs from file
            try:
                with open(args.batch_file, 'r', encoding='utf-8') as f:
                    urls = [line.strip() for line in f if line.strip() and not line.startswith('#')]
                
                # Limit sample size if specified
                if args.sample_size:
                    urls = urls[:args.sample_size]
                    logger.info(f"Limited to {args.sample_size} profiles for testing")
                
                results = scraper.scrape_multiple_profiles(urls, delay=args.delay)
                scraper.save_results(results, args.output)
                
            except FileNotFoundError:
                logger.error(f"File not found: {args.batch_file}")
        else:
            # Demo with sample URL
            sample_url = "https://clutch.co/profile/100-shapes"
            logger.info(f"Demo mode: scraping {sample_url}")
            result = scraper.scrape_profile(sample_url)
            scraper.save_results([result], 'demo_profile.json')
            
    except KeyboardInterrupt:
        logger.info("Scraping interrupted by user")
    except Exception as e:
        logger.error(f"Error during scraping: {e}")
    finally:
        # Cleanup
        del scraper

if __name__ == "__main__":
    main() 