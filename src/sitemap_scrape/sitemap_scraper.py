import requests
import xml.etree.ElementTree as ET
import csv
import os
from urllib.parse import urljoin, urlparse
import time
from typing import List, Set

class SitemapScraper:
    def __init__(self, output_dir="sitemap_output"):
        self.current_dir = os.getcwd()
        self.output_dir = os.path.join(self.current_dir, output_dir)
        os.makedirs(self.output_dir, exist_ok=True)
        self.all_urls = set()  # Use set to avoid duplicates
        
    def fetch_sitemap(self, sitemap_url: str) -> str:
        """Fetch sitemap XML content from URL"""
        try:
            print(f"Fetching sitemap: {sitemap_url}")
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate, br',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            }
            
            session = requests.Session()
            session.headers.update(headers)
            
            response = session.get(sitemap_url, timeout=30)
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            print(f"Error fetching sitemap {sitemap_url}: {e}")
            print("This might be due to rate limiting or access restrictions.")
            print("Consider using a local XML file or adding delays between requests.")
            return None
    
    def load_local_xml(self, filepath: str) -> str:
        """Load XML content from local file"""
        try:
            print(f"Loading local XML file: {filepath}")
            with open(filepath, 'r', encoding='utf-8') as file:
                return file.read()
        except FileNotFoundError:
            print(f"Error: File not found: {filepath}")
            return None
        except Exception as e:
            print(f"Error reading file {filepath}: {e}")
            return None
    
    def parse_sitemap_xml(self, xml_content: str) -> List[str]:
        """Parse XML content and extract all URLs from <loc> elements"""
        urls = []
        try:
            root = ET.fromstring(xml_content)
            
            # Handle namespaces - common sitemap namespace
            namespaces = {
                'sitemap': 'http://www.sitemaps.org/schemas/sitemap/0.9'
            }
            
            # Find all <url><loc> elements
            for url_elem in root.findall('.//sitemap:url', namespaces):
                loc_elem = url_elem.find('sitemap:loc', namespaces)
                if loc_elem is not None and loc_elem.text:
                    urls.append(loc_elem.text.strip())
            
            # If no namespace URLs found, try without namespace
            if not urls:
                for url_elem in root.findall('.//url'):
                    loc_elem = url_elem.find('loc')
                    if loc_elem is not None and loc_elem.text:
                        urls.append(loc_elem.text.strip())
                        
            print(f"Extracted {len(urls)} URLs from sitemap")
            return urls
            
        except ET.ParseError as e:
            print(f"Error parsing XML: {e}")
            return []
    
    def scrape_single_sitemap(self, sitemap_url: str, is_local_file: bool = False) -> List[str]:
        """Scrape a single sitemap and return list of URLs"""
        if is_local_file:
            xml_content = self.load_local_xml(sitemap_url)
        else:
            xml_content = self.fetch_sitemap(sitemap_url)
            
        if xml_content:
            return self.parse_sitemap_xml(xml_content)
        return []
    
    def scrape_multiple_sitemaps(self, sitemap_urls: List[str], delay: float = 2.0, is_local_files: bool = False) -> Set[str]:
        """Scrape multiple sitemaps and collect all unique URLs"""
        all_urls = set()
        
        for i, sitemap_url in enumerate(sitemap_urls, 1):
            print(f"\n--- Processing sitemap {i}/{len(sitemap_urls)} ---")
            urls = self.scrape_single_sitemap(sitemap_url, is_local_file=is_local_files)
            all_urls.update(urls)
            print(f"Total unique URLs collected so far: {len(all_urls)}")
            
            # Add delay between requests to be respectful (only for remote URLs)
            if i < len(sitemap_urls) and not is_local_files:
                print(f"Waiting {delay} seconds before next request...")
                time.sleep(delay)
        
        return all_urls
    
    def save_urls_to_csv(self, urls: Set[str], filename: str = "extracted_urls.csv"):
        """Save URLs to CSV file"""
        filepath = os.path.join(self.output_dir, filename)
        
        with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['url'])  # Header
            
            for url in sorted(urls):  # Sort for consistent output
                writer.writerow([url])
        
        print(f"\nSaved {len(urls)} URLs to: {filepath}")
        return filepath
    
    def save_urls_to_txt(self, urls: Set[str], filename: str = "extracted_urls.txt"):
        """Save URLs to text file (one per line)"""
        filepath = os.path.join(self.output_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as txtfile:
            for url in sorted(urls):
                txtfile.write(url + '\n')
        
        print(f"Saved {len(urls)} URLs to: {filepath}")
        return filepath
    
    def print_sample_urls(self, urls: Set[str], sample_size: int = 10):
        """Print a sample of extracted URLs"""
        sample_urls = list(urls)[:sample_size]
        print(f"\nSample of extracted URLs (showing {len(sample_urls)} of {len(urls)}):")
        for url in sample_urls:
            print(f"  {url}")
        
        if len(urls) > sample_size:
            print(f"  ... and {len(urls) - sample_size} more URLs")

def create_sample_sitemap():
    """Create a sample sitemap XML file for testing"""
    sample_xml = '''<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">
<url>
<loc>https://clutch.co/profile/studio-mcgee</loc>
<lastmod>2025-05-31T06:31:10Z</lastmod>
</url>
<url>
<loc>https://clutch.co/profile/tolo-architecture</loc>
<lastmod>2025-05-31T06:31:10Z</lastmod>
</url>
<url>
<loc>https://clutch.co/profile/wm-shirley</loc>
<lastmod>2025-05-31T06:31:10Z</lastmod>
</url>
<url>
<loc>https://clutch.co/profile/enterprise-staffing-group</loc>
<lastmod>2025-05-31T06:31:10Z</lastmod>
</url>
<url>
<loc>https://clutch.co/profile/murdock-mailing-company</loc>
<lastmod>2025-05-31T06:31:10Z</lastmod>
</url>
<url>
<loc>https://clutch.co/profile/martsolf-architecture</loc>
<lastmod>2025-05-31T06:31:10Z</lastmod>
</url>
<url>
<loc>https://clutch.co/profile/finelines-design-studio</loc>
<lastmod>2025-05-31T06:31:10Z</lastmod>
</url>
<url>
<loc>https://clutch.co/profile/pizzulli-associates-pai</loc>
<lastmod>2025-05-31T06:31:10Z</lastmod>
</url>
<url>
<loc>https://clutch.co/profile/palkiper</loc>
<lastmod>2025-05-31T06:31:10Z</lastmod>
</url>
<url>
<loc>https://clutch.co/profile/kaim-architecture</loc>
<lastmod>2025-05-31T06:31:10Z</lastmod>
</url>
<url>
<loc>https://clutch.co/profile/prodigy-staff-advisors</loc>
<lastmod>2025-05-31T06:31:10Z</lastmod>
</url>
<url>
<loc>https://clutch.co/profile/harker-design</loc>
<lastmod>2025-05-31T06:31:10Z</lastmod>
</url>
</urlset>'''
    
    with open('sample_sitemap.xml', 'w', encoding='utf-8') as f:
        f.write(sample_xml)
    print("Created sample_sitemap.xml for testing")

def main():
    # Example usage
    scraper = SitemapScraper()
    
    # Create a sample sitemap for testing
    create_sample_sitemap()
    
    print("=== Testing with Sample Sitemap (Local File) ===")
    urls = scraper.scrape_single_sitemap("sample_sitemap.xml", is_local_file=True)
    if urls:
        scraper.print_sample_urls(set(urls))
        scraper.save_urls_to_csv(set(urls), "sample_sitemap_urls.csv")
        scraper.save_urls_to_txt(set(urls), "sample_sitemap_urls.txt")
    
    # Try remote sitemap with better error handling
    print("\n=== Attempting Remote Sitemap ===")
    remote_sitemap_url = "https://clutch.co/sitemap-profile-9.xml"
    remote_urls = scraper.scrape_single_sitemap(remote_sitemap_url, is_local_file=False)
    if remote_urls:
        scraper.print_sample_urls(set(remote_urls))
        scraper.save_urls_to_csv(set(remote_urls), "remote_sitemap_urls.csv")
        scraper.save_urls_to_txt(set(remote_urls), "remote_sitemap_urls.txt")
    else:
        print("Remote sitemap failed. You can:")
        print("1. Try with different headers or delay")
        print("2. Download the XML manually and use as local file")
        print("3. Use a tool like curl to fetch the sitemap first")
    
    # Multiple sitemaps example (commented out by default)
    """
    print("\n=== Scraping Multiple Sitemaps ===")
    multiple_sitemap_urls = [
        "https://clutch.co/sitemap-profile-1.xml",
        "https://clutch.co/sitemap-profile-2.xml", 
        "https://clutch.co/sitemap-profile-3.xml",
        # Add more sitemap URLs here
    ]
    
    all_urls = scraper.scrape_multiple_sitemaps(multiple_sitemap_urls, delay=3.0)
    if all_urls:
        scraper.print_sample_urls(all_urls)
        scraper.save_urls_to_csv(all_urls, "all_sitemap_urls.csv")
        scraper.save_urls_to_txt(all_urls, "all_sitemap_urls.txt")
    """

if __name__ == "__main__":
    main() 