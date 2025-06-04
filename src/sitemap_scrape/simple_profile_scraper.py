#!/usr/bin/env python3
"""
Simple Clutch Profile Scraper - Extract basic information from company profiles

This is a lightweight version that works with minimal dependencies.
For full features, use clutch_profile_scraper.py with all dependencies installed.

Usage:
    python simple_profile_scraper.py "https://clutch.co/profile/100-shapes"
"""

import urllib.request
import urllib.parse
import json
import re
import sys
import time
from typing import Dict, Optional

class SimpleClutchScraper:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'DNT': '1',
            'Connection': 'keep-alive',
        }
    
    def fetch_page(self, url: str) -> Optional[str]:
        """Fetch page content using urllib"""
        try:
            print(f"Fetching: {url}")
            
            req = urllib.request.Request(url, headers=self.headers)
            with urllib.request.urlopen(req, timeout=30) as response:
                content = response.read()
                
            # Handle encoding
            if isinstance(content, bytes):
                try:
                    content = content.decode('utf-8')
                except UnicodeDecodeError:
                    content = content.decode('utf-8', errors='ignore')
            
            return content
            
        except Exception as e:
            print(f"Error fetching {url}: {e}")
            return None
    
    def extract_basic_info(self, html: str, url: str) -> Dict:
        """Extract basic company information using regex patterns"""
        data = {
            'url': url,
            'company_name': '',
            'description': '',
            'reviews_count': 0,
            'location': '',
            'min_project_size': '',
            'hourly_rate': '',
            'employees': '',
            'year_founded': '',
            'services': [],
            'contact_website': '',
            'extraction_method': 'regex_patterns'
        }
        
        try:
            # Company name - look for h1 or title tags
            name_patterns = [
                r'<h1[^>]*>([^<]+)</h1>',
                r'<title>([^|<]+)',
                r'"name":"([^"]+)"'
            ]
            
            for pattern in name_patterns:
                match = re.search(pattern, html, re.IGNORECASE)
                if match:
                    name = match.group(1).strip()
                    if name and len(name) < 100:  # Reasonable company name length
                        data['company_name'] = name
                        break
            
            # Reviews count
            review_patterns = [
                r'(\d+)\s*review',
                r'"reviewCount":(\d+)',
                r'reviewCount["\']:\s*(\d+)'
            ]
            
            for pattern in review_patterns:
                match = re.search(pattern, html, re.IGNORECASE)
                if match:
                    data['reviews_count'] = int(match.group(1))
                    break
            
            # Location
            location_patterns = [
                r'([A-Za-z\s]+,\s*[A-Za-z\s]+)',
                r'"location":"([^"]+)"',
                r'Location[^>]*>([^<]+)',
            ]
            
            for pattern in location_patterns:
                matches = re.findall(pattern, html)
                for match in matches:
                    location = match.strip() if isinstance(match, str) else match
                    # Filter out obviously wrong locations
                    if location and ',' in location and len(location) < 50:
                        data['location'] = location
                        break
                if data['location']:
                    break
            
            # Project size
            project_patterns = [
                r'\$([0-9,]+\+?)(?:\s*minimum|\s*min)',
                r'Min.*project.*\$([0-9,]+)',
                r'minimum.*\$([0-9,]+)'
            ]
            
            for pattern in project_patterns:
                match = re.search(pattern, html, re.IGNORECASE)
                if match:
                    data['min_project_size'] = f"${match.group(1)}"
                    break
            
            # Hourly rate
            rate_patterns = [
                r'\$(\d+)\s*-\s*\$(\d+)\s*/?\s*hr',
                r'(\d+)\s*-\s*(\d+)\s*per\s*hour',
                r'"hourlyRate":"([^"]+)"'
            ]
            
            for pattern in rate_patterns:
                match = re.search(pattern, html, re.IGNORECASE)
                if match:
                    if len(match.groups()) >= 2:
                        data['hourly_rate'] = f"${match.group(1)} - ${match.group(2)} / hr"
                    else:
                        data['hourly_rate'] = match.group(1)
                    break
            
            # Employees
            employee_patterns = [
                r'(\d+)\s*-\s*(\d+)\s*employees',
                r'team.*size.*(\d+)\s*-\s*(\d+)',
                r'"employees":"([^"]+)"'
            ]
            
            for pattern in employee_patterns:
                match = re.search(pattern, html, re.IGNORECASE)
                if match:
                    if len(match.groups()) >= 2:
                        data['employees'] = f"{match.group(1)} - {match.group(2)}"
                    else:
                        data['employees'] = match.group(1)
                    break
            
            # Year founded
            founded_patterns = [
                r'Founded\s*(\d{4})',
                r'established\s*(\d{4})',
                r'"founded":(\d{4})'
            ]
            
            for pattern in founded_patterns:
                match = re.search(pattern, html, re.IGNORECASE)
                if match:
                    data['year_founded'] = match.group(1)
                    break
            
            # Services with percentages
            service_patterns = [
                r'([A-Za-z\s&/]+)\s*(\d+)%',
                r'(\d+)%\s*([A-Za-z\s&/]+)'
            ]
            
            services = []
            for pattern in service_patterns:
                matches = re.findall(pattern, html)
                for match in matches:
                    if len(match) == 2:
                        if match[0].isdigit():
                            percentage, service = match[0], match[1]
                        else:
                            service, percentage = match[0], match[1]
                        
                        service = service.strip()
                        if len(service) > 5 and len(service) < 50:  # Reasonable service name
                            services.append({
                                'service': service,
                                'percentage': f"{percentage}%"
                            })
            
            data['services'] = services[:10]  # Limit to first 10 matches
            
            # Website link
            website_patterns = [
                r'href="(https?://[^"]+)"[^>]*[^>]*(?:visit|website)',
                r'"website":"(https?://[^"]+)"'
            ]
            
            for pattern in website_patterns:
                match = re.search(pattern, html, re.IGNORECASE)
                if match:
                    website = match.group(1)
                    if 'clutch.co' not in website:
                        data['contact_website'] = website
                        break
            
            # Basic description - look for meta description or first paragraph
            desc_patterns = [
                r'<meta[^>]*name=["\']description["\'][^>]*content=["\']([^"\']+)["\']',
                r'<p[^>]*>([^<]{50,200})</p>'
            ]
            
            for pattern in desc_patterns:
                match = re.search(pattern, html, re.IGNORECASE)
                if match:
                    desc = match.group(1).strip()
                    if len(desc) > 20:
                        data['description'] = desc
                        break
            
        except Exception as e:
            print(f"Error extracting data: {e}")
        
        return data
    
    def scrape_profile(self, url: str) -> Dict:
        """Scrape a single profile"""
        html = self.fetch_page(url)
        if not html:
            return {'error': 'Failed to fetch page', 'url': url}
        
        data = self.extract_basic_info(html, url)
        
        # Print results
        print(f"\n{'='*60}")
        print(f"EXTRACTED DATA FOR: {data.get('company_name', 'Unknown Company')}")
        print(f"{'='*60}")
        
        for key, value in data.items():
            if value and key != 'url':
                if isinstance(value, list):
                    if value:
                        print(f"{key.replace('_', ' ').title()}: {len(value)} items")
                        for i, item in enumerate(value[:3], 1):
                            print(f"  {i}. {item}")
                        if len(value) > 3:
                            print(f"  ... and {len(value) - 3} more")
                else:
                    print(f"{key.replace('_', ' ').title()}: {value}")
        
        return data

def main():
    scraper = SimpleClutchScraper()
    
    if len(sys.argv) > 1:
        url = sys.argv[1]
    else:
        # Default to the example from the screenshot
        url = "https://clutch.co/profile/100-shapes"
        print(f"No URL provided, using example: {url}")
    
    # Scrape the profile
    result = scraper.scrape_profile(url)
    
    # Save results
    output_file = 'simple_profile_result.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    
    print(f"\nResults saved to: {output_file}")
    
    # If extraction was successful, show some stats
    if result.get('company_name'):
        print(f"\n✓ Successfully extracted data for: {result['company_name']}")
        if result.get('reviews_count'):
            print(f"✓ Found {result['reviews_count']} reviews")
        if result.get('services'):
            print(f"✓ Found {len(result['services'])} services")
        if result.get('location'):
            print(f"✓ Location: {result['location']}")
    else:
        print("\n⚠ Limited data extracted - page might be protected or structure changed")
        print("Consider using the full scraper with Selenium for better results")

if __name__ == "__main__":
    main() 