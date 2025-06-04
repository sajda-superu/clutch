#!/usr/bin/env python3
"""
Bulk Sitemap Processor - Extract URLs from multiple XML sitemaps

This tool helps extract all URLs from XML sitemaps, with support for:
- Single sitemap processing
- Batch processing of multiple sitemaps  
- Local XML files
- Remote URL fetching (when possible)
- Manual download instructions for protected sites

Usage Examples:
    # Process a single sitemap
    python bulk_sitemap_processor.py --single https://example.com/sitemap.xml
    
    # Process multiple sitemaps from a list
    python bulk_sitemap_processor.py --batch sitemap_list.txt
    
    # Process local XML files
    python bulk_sitemap_processor.py --local sitemap1.xml sitemap2.xml
"""

import argparse
import requests
import xml.etree.ElementTree as ET
import csv
import os
import time
from typing import List, Set, Dict
from urllib.parse import urlparse
import sys

class BulkSitemapProcessor:
    def __init__(self, output_dir="sitemap_results"):
        self.current_dir = os.getcwd()
        self.output_dir = os.path.join(self.current_dir, output_dir)
        os.makedirs(self.output_dir, exist_ok=True)
        self.all_urls = set()
        self.failed_sitemaps = []
        self.success_count = 0
        self.total_urls_extracted = 0
        
    def fetch_sitemap_with_retry(self, sitemap_url: str, max_retries: int = 3) -> str:
        """Fetch sitemap XML with multiple retry strategies"""
        headers_list = [
            # Standard browser headers
            {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
            },
            # Simple XML request
            {
                'User-Agent': 'Python-sitemap-parser/1.0',
                'Accept': 'application/xml,text/xml,*/*',
            },
            # Search engine bot
            {
                'User-Agent': 'Googlebot/2.1 (+http://www.google.com/bot.html)',
                'Accept': '*/*',
            }
        ]
        
        for attempt in range(max_retries):
            headers = headers_list[attempt % len(headers_list)]
            try:
                print(f"  Attempt {attempt + 1}/{max_retries} - Fetching: {sitemap_url}")
                
                session = requests.Session()
                response = session.get(sitemap_url, headers=headers, timeout=30, allow_redirects=True)
                response.raise_for_status()
                
                # Check if we got XML content
                content_type = response.headers.get('content-type', '').lower()
                if 'xml' in content_type or response.text.strip().startswith('<?xml'):
                    print(f"  ✓ Successfully fetched XML content ({len(response.text)} bytes)")
                    return response.text
                else:
                    print(f"  ⚠ Warning: Got non-XML content (Content-Type: {content_type})")
                    if attempt < max_retries - 1:
                        time.sleep(2 ** attempt)  # Exponential backoff
                        continue
                    
            except requests.RequestException as e:
                print(f"  ✗ Attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                
        return None
    
    def load_local_xml(self, filepath: str) -> str:
        """Load XML content from local file"""
        try:
            print(f"Loading local XML file: {filepath}")
            if not os.path.exists(filepath):
                print(f"  ✗ File not found: {filepath}")
                return None
                
            with open(filepath, 'r', encoding='utf-8') as file:
                content = file.read()
                print(f"  ✓ Loaded {len(content)} bytes from {filepath}")
                return content
        except Exception as e:
            print(f"  ✗ Error reading file {filepath}: {e}")
            return None
    
    def parse_sitemap_xml(self, xml_content: str, source_name: str = "") -> List[str]:
        """Parse XML content and extract all URLs from <loc> elements"""
        urls = []
        try:
            root = ET.fromstring(xml_content)
            
            # Handle namespaces
            namespaces = {
                'sitemap': 'http://www.sitemaps.org/schemas/sitemap/0.9',
                'xhtml': 'http://www.w3.org/1999/xhtml'
            }
            
            # Try with namespace first
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
            
            # Also check for sitemap index (sitemaps containing other sitemaps)
            sitemap_refs = []
            for sitemap_elem in root.findall('.//sitemap:sitemap', namespaces):
                loc_elem = sitemap_elem.find('sitemap:loc', namespaces)
                if loc_elem is not None and loc_elem.text:
                    sitemap_refs.append(loc_elem.text.strip())
            
            if not sitemap_refs:
                for sitemap_elem in root.findall('.//sitemap'):
                    loc_elem = sitemap_elem.find('loc')
                    if loc_elem is not None and loc_elem.text:
                        sitemap_refs.append(loc_elem.text.strip())
            
            if sitemap_refs:
                print(f"  ℹ Found {len(sitemap_refs)} child sitemaps in {source_name}")
                print("  Child sitemaps:")
                for ref in sitemap_refs[:5]:  # Show first 5
                    print(f"    - {ref}")
                if len(sitemap_refs) > 5:
                    print(f"    ... and {len(sitemap_refs) - 5} more")
                
            print(f"  ✓ Extracted {len(urls)} URLs from {source_name}")
            return urls
            
        except ET.ParseError as e:
            print(f"  ✗ Error parsing XML from {source_name}: {e}")
            # Try to show some context around the error
            lines = xml_content.split('\n')
            if len(lines) > 0:
                print(f"  First few lines of content:")
                for i, line in enumerate(lines[:3]):
                    print(f"    Line {i+1}: {line[:100]}...")
            return []
    
    def process_single_sitemap(self, sitemap_source: str, is_local: bool = False) -> List[str]:
        """Process a single sitemap and return URLs"""
        print(f"\n{'='*50}")
        print(f"Processing: {sitemap_source}")
        print(f"{'='*50}")
        
        if is_local:
            xml_content = self.load_local_xml(sitemap_source)
        else:
            xml_content = self.fetch_sitemap_with_retry(sitemap_source)
            
        if xml_content:
            urls = self.parse_sitemap_xml(xml_content, sitemap_source)
            if urls:
                self.success_count += 1
                self.total_urls_extracted += len(urls)
                return urls
            else:
                self.failed_sitemaps.append(sitemap_source)
        else:
            self.failed_sitemaps.append(sitemap_source)
            
        return []
    
    def process_multiple_sitemaps(self, sitemap_sources: List[str], is_local: bool = False, delay: float = 2.0) -> Set[str]:
        """Process multiple sitemaps and collect all unique URLs"""
        all_urls = set()
        
        print(f"Starting batch processing of {len(sitemap_sources)} sitemaps...")
        print(f"Using delay of {delay} seconds between requests" if not is_local else "Processing local files")
        
        for i, sitemap_source in enumerate(sitemap_sources, 1):
            print(f"\n--- Processing {i}/{len(sitemap_sources)} ---")
            
            urls = self.process_single_sitemap(sitemap_source, is_local=is_local)
            all_urls.update(urls)
            
            print(f"Total unique URLs collected so far: {len(all_urls)}")
            
            # Add delay between requests (only for remote URLs)
            if i < len(sitemap_sources) and not is_local:
                print(f"Waiting {delay} seconds before next request...")
                time.sleep(delay)
        
        return all_urls
    
    def save_results(self, urls: Set[str], prefix: str = "extracted"):
        """Save URLs to both CSV and TXT formats"""
        if not urls:
            print("No URLs to save.")
            return
            
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        
        # Save to CSV
        csv_filename = f"{prefix}_urls_{timestamp}.csv"
        csv_filepath = os.path.join(self.output_dir, csv_filename)
        
        with open(csv_filepath, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['url', 'domain'])  # Headers
            
            for url in sorted(urls):
                domain = urlparse(url).netloc
                writer.writerow([url, domain])
        
        # Save to TXT
        txt_filename = f"{prefix}_urls_{timestamp}.txt"
        txt_filepath = os.path.join(self.output_dir, txt_filename)
        
        with open(txt_filepath, 'w', encoding='utf-8') as txtfile:
            for url in sorted(urls):
                txtfile.write(url + '\n')
        
        print(f"\n✓ Results saved:")
        print(f"  CSV: {csv_filepath}")
        print(f"  TXT: {txt_filepath}")
        
        return csv_filepath, txt_filepath
    
    def print_summary(self, urls: Set[str]):
        """Print processing summary"""
        print(f"\n{'='*60}")
        print("PROCESSING SUMMARY")
        print(f"{'='*60}")
        print(f"Total sitemaps processed: {self.success_count}")
        print(f"Failed sitemaps: {len(self.failed_sitemaps)}")
        print(f"Total unique URLs extracted: {len(urls)}")
        print(f"Total URLs across all sitemaps: {self.total_urls_extracted}")
        
        if urls:
            # Analyze domains
            domains = {}
            for url in urls:
                domain = urlparse(url).netloc
                domains[domain] = domains.get(domain, 0) + 1
            
            print(f"\nTop domains by URL count:")
            for domain, count in sorted(domains.items(), key=lambda x: x[1], reverse=True)[:10]:
                print(f"  {domain}: {count} URLs")
        
        if self.failed_sitemaps:
            print(f"\nFailed sitemaps:")
            for failed in self.failed_sitemaps:
                print(f"  ✗ {failed}")
            
            print(f"\nFor sites with Cloudflare protection, try manual download:")
            for failed in self.failed_sitemaps:
                if 'http' in failed:
                    print(f"  curl -o 'sitemap.xml' '{failed}'")
        
        # Sample URLs
        if urls:
            sample_size = min(10, len(urls))
            sample_urls = list(urls)[:sample_size]
            print(f"\nSample URLs (showing {sample_size} of {len(urls)}):")
            for url in sample_urls:
                print(f"  {url}")
            
            if len(urls) > sample_size:
                print(f"  ... and {len(urls) - sample_size} more URLs")

def load_sitemap_list(filepath: str) -> List[str]:
    """Load sitemap URLs from a text file (one per line)"""
    sitemaps = []
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):  # Skip empty lines and comments
                    sitemaps.append(line)
        return sitemaps
    except FileNotFoundError:
        print(f"Error: File not found: {filepath}")
        return []

def main():
    parser = argparse.ArgumentParser(
        description="Extract URLs from XML sitemaps",
        epilog="""
Examples:
  %(prog)s --single https://example.com/sitemap.xml
  %(prog)s --batch sitemap_list.txt  
  %(prog)s --local sitemap1.xml sitemap2.xml
  %(prog)s --generate-example-list
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument('--single', '-s', help='Process a single sitemap URL or file')
    parser.add_argument('--batch', '-b', help='Process multiple sitemaps from a list file')
    parser.add_argument('--local', '-l', nargs='+', help='Process local XML files')
    parser.add_argument('--delay', '-d', type=float, default=2.0, help='Delay between requests (default: 2.0)')
    parser.add_argument('--output', '-o', help='Output directory (default: sitemap_results)')
    parser.add_argument('--generate-example-list', action='store_true', help='Generate example sitemap list file')
    
    args = parser.parse_args()
    
    if args.generate_example_list:
        example_content = """# Example sitemap list file
# Lines starting with # are comments
# Put one sitemap URL per line

# Clutch.co profile sitemaps
https://clutch.co/sitemap-profile-1.xml
https://clutch.co/sitemap-profile-2.xml
https://clutch.co/sitemap-profile-3.xml

# Add more sitemap URLs here
# https://example.com/sitemap.xml
# https://another-site.com/sitemap.xml
"""
        with open('example_sitemap_list.txt', 'w') as f:
            f.write(example_content)
        print("Generated example_sitemap_list.txt")
        print("Edit this file with your sitemap URLs and use: python bulk_sitemap_processor.py --batch example_sitemap_list.txt")
        return
    
    if not any([args.single, args.batch, args.local]):
        parser.print_help()
        return
    
    # Initialize processor
    output_dir = args.output or "sitemap_results"
    processor = BulkSitemapProcessor(output_dir)
    
    urls = set()
    
    if args.single:
        # Process single sitemap
        is_local = not args.single.startswith('http')
        single_urls = processor.process_single_sitemap(args.single, is_local=is_local)
        urls.update(single_urls)
        
    elif args.batch:
        # Process multiple sitemaps from file
        sitemap_list = load_sitemap_list(args.batch)
        if sitemap_list:
            batch_urls = processor.process_multiple_sitemaps(sitemap_list, delay=args.delay)
            urls.update(batch_urls)
        else:
            print("No valid sitemaps found in the list file.")
            return
            
    elif args.local:
        # Process local files
        local_urls = processor.process_multiple_sitemaps(args.local, is_local=True)
        urls.update(local_urls)
    
    # Save results and print summary
    if urls:
        processor.save_results(urls)
    
    processor.print_summary(urls)

if __name__ == "__main__":
    main() 