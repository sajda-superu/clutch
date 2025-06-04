# Sitemap URL Extractor Tools

This collection of tools helps you extract URLs from XML sitemaps, with special focus on handling sites like Clutch.co that have multiple sitemap files containing profile URLs.

## 🎯 What These Tools Do

These tools solve the problem of extracting all individual URLs (like `https://clutch.co/profile/company-name`) from XML sitemaps. Perfect for:
- Building lists of company profiles from Clutch.co
- Extracting product pages from e-commerce sitemaps  
- Collecting blog post URLs from content sites
- Any bulk URL extraction from XML sitemaps

## 📁 Files Overview

1. **`sitemap_scraper.py`** - Basic sitemap parser (single file focus)
2. **`bulk_sitemap_processor.py`** - Advanced batch processor with retry logic
3. **`download_sitemaps.sh`** - Bash script for downloading protected sitemaps
4. **`example_sitemap_list.txt`** - Template for batch processing

## 🚀 Quick Start

### Option 1: Process a Single Sitemap (Local File)

```bash
# If you have a local XML file
python bulk_sitemap_processor.py --single sitemap.xml

# Process the sample file we created
python bulk_sitemap_processor.py --single sample_sitemap.xml
```

### Option 2: Process Multiple Sitemaps (Batch Mode)

```bash
# 1. Generate example list file
python bulk_sitemap_processor.py --generate-example-list

# 2. Edit example_sitemap_list.txt with your URLs
# 3. Process the batch
python bulk_sitemap_processor.py --batch example_sitemap_list.txt
```

### Option 3: Handle Protected Sites (Like Clutch.co)

```bash
# Method 1: Try direct processing (may fail with 403)
python bulk_sitemap_processor.py --single https://clutch.co/sitemap-profile-9.xml

# Method 2: Download first, then process
./download_sitemaps.sh -u https://clutch.co/sitemap-profile-9.xml -o clutch_profile_9.xml
python bulk_sitemap_processor.py --single clutch_profile_9.xml
```

## 📋 Detailed Usage

### Bulk Sitemap Processor (`bulk_sitemap_processor.py`)

The main tool with comprehensive features:

```bash
# Single sitemap (remote)
python bulk_sitemap_processor.py --single https://example.com/sitemap.xml

# Single sitemap (local)  
python bulk_sitemap_processor.py --single local_sitemap.xml

# Multiple sitemaps from list
python bulk_sitemap_processor.py --batch sitemap_urls.txt

# Multiple local files
python bulk_sitemap_processor.py --local file1.xml file2.xml file3.xml

# Custom output directory
python bulk_sitemap_processor.py --single sitemap.xml --output my_results

# Custom delay between requests (for rate limiting)
python bulk_sitemap_processor.py --batch sitemap_list.txt --delay 5
```

### Download Helper (`download_sitemaps.sh`)

For sites with Cloudflare protection:

```bash
# Download single sitemap
./download_sitemaps.sh -u https://clutch.co/sitemap-profile-9.xml -o clutch9.xml

# Download multiple from list
./download_sitemaps.sh -l example_sitemap_list.txt -d 3

# Custom delay between downloads
./download_sitemaps.sh -l sitemap_list.txt -d 5
```

## 📊 Output Formats

All tools generate results in multiple formats:

### CSV Format (`extracted_urls_TIMESTAMP.csv`)
```csv
url,domain
https://clutch.co/profile/company1,clutch.co
https://clutch.co/profile/company2,clutch.co
```

### Text Format (`extracted_urls_TIMESTAMP.txt`)
```
https://clutch.co/profile/company1
https://clutch.co/profile/company2
https://clutch.co/profile/company3
```

## 🏗️ Clutch.co Specific Workflow

For extracting all Clutch.co profile URLs:

### Step 1: Create Sitemap List
```bash
# Generate template
python bulk_sitemap_processor.py --generate-example-list

# Edit example_sitemap_list.txt to include all Clutch profile sitemaps:
# https://clutch.co/sitemap-profile-1.xml
# https://clutch.co/sitemap-profile-2.xml
# https://clutch.co/sitemap-profile-3.xml
# ... (add more as needed)
```

### Step 2: Download Sitemaps (Bypass Cloudflare)
```bash
# Download all sitemaps from the list
./download_sitemaps.sh -l example_sitemap_list.txt -d 3
```

### Step 3: Process Downloaded Files
```bash
# Process all downloaded XML files
python bulk_sitemap_processor.py --local *.xml
```

### Step 4: Use Results
Your profile URLs will be in:
- `sitemap_results/extracted_urls_TIMESTAMP.csv`
- `sitemap_results/extracted_urls_TIMESTAMP.txt`

## 🔧 Troubleshooting

### 403 Forbidden Errors
```bash
# Try the download helper script
./download_sitemaps.sh -u YOUR_SITEMAP_URL -o downloaded.xml

# Then process locally
python bulk_sitemap_processor.py --single downloaded.xml
```

### XML Parsing Errors
Check if you received HTML instead of XML:
```bash
head -5 downloaded_file.xml
```

If you see HTML (Cloudflare protection), try:
1. Different user agent strings
2. Longer delays between requests
3. Using a VPN
4. Browser extension to export sitemaps

### Rate Limiting
```bash
# Increase delay between requests
python bulk_sitemap_processor.py --batch sitemap_list.txt --delay 10

# Or download manually first
./download_sitemaps.sh -l sitemap_list.txt -d 10
```

## 📈 Performance Tips

1. **Batch Processing**: Use `--batch` mode for multiple sitemaps
2. **Local Processing**: Download first, process locally for better reliability
3. **Rate Limiting**: Use appropriate delays to avoid being blocked
4. **Parallel Downloads**: For large batches, consider splitting the list

## 🎨 Customization

### Adding New Headers
Edit `bulk_sitemap_processor.py` line ~45 to add custom headers:

```python
headers_list = [
    {
        'User-Agent': 'Your-Custom-Bot/1.0',
        'Accept': 'application/xml',
        # Add more headers
    }
]
```

### Custom Output Formats
Modify the `save_results()` method in `BulkSitemapProcessor` class to add JSON, Excel, or other formats.

## 📝 Example Use Cases

### E-commerce Product URLs
```bash
# Extract all product URLs from an e-commerce sitemap
python bulk_sitemap_processor.py --single https://shop.example.com/sitemap-products.xml
```

### Blog Post Collection
```bash
# Get all blog post URLs
python bulk_sitemap_processor.py --single https://blog.example.com/sitemap.xml
```

### Directory Scraping (Like Clutch.co)
```bash
# Get all company profiles
./download_sitemaps.sh -l clutch_sitemaps.txt
python bulk_sitemap_processor.py --local sitemap-profile-*.xml
```

## 🤝 Contributing

Feel free to enhance these tools by:
- Adding new output formats
- Improving error handling
- Adding more retry strategies
- Supporting additional sitemap formats

## ⚠️ Important Notes

1. **Respect robots.txt**: Always check the site's robots.txt file
2. **Rate Limiting**: Use appropriate delays to be respectful
3. **Terms of Service**: Ensure your usage complies with the site's ToS
4. **Data Usage**: Use extracted data responsibly and legally

---

## Quick Command Reference

```bash
# Generate example list
python bulk_sitemap_processor.py --generate-example-list

# Process single sitemap
python bulk_sitemap_processor.py --single sitemap.xml

# Process batch with custom delay
python bulk_sitemap_processor.py --batch list.txt --delay 5

# Download protected sitemap
./download_sitemaps.sh -u URL -o output.xml

# Process multiple local files
python bulk_sitemap_processor.py --local *.xml
``` 