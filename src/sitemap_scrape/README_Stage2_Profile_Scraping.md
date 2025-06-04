# Stage 2: Profile Data Extraction Guide

## 🎯 Objective
Extract detailed company information from individual Clutch.co profile pages, including all the data visible in the screenshot you provided for "100 Shapes":

- Company name, tagline, description
- Review count and ratings
- Service lines with percentages
- Pricing information (min project size, hourly rate)
- Company details (employees, location, year founded)
- Contact information and social media links

## 🚧 Challenge: Cloudflare Protection
Clutch.co uses Cloudflare protection that blocks automated requests with 403 Forbidden errors. We need specialized approaches to bypass this.

## 📋 Available Solutions

### Option 1: Browser Automation with Selenium (Recommended)
**Requirements:** Chrome/ChromeDriver, Selenium
**Success Rate:** High
**Speed:** Moderate

```bash
# Install Chrome and ChromeDriver first
brew install --cask google-chrome
brew install chromedriver

# Install Python packages (if possible on your system)
pip3 install --break-system-packages selenium beautifulsoup4 requests

# Run the full scraper
python3 clutch_profile_scraper.py --url "https://clutch.co/profile/100-shapes"
```

### Option 2: Manual Browser Extension Method
**Requirements:** Browser extension for data extraction
**Success Rate:** High
**Speed:** Manual but reliable

1. Install a web scraper browser extension (like Web Scraper, Data Miner, or Scraper)
2. Navigate to profile pages manually
3. Set up extraction rules for the data fields
4. Export results to CSV/JSON

### Option 3: Playwright (Alternative to Selenium)
**Requirements:** Playwright library
**Success Rate:** High
**Speed:** Fast

```bash
pip3 install --break-system-packages playwright
playwright install chromium

# Use playwright instead of selenium in the scraper
```

### Option 4: API/Network Inspection Method
**Requirements:** Browser developer tools
**Success Rate:** Variable
**Speed:** Fast if successful

1. Open browser developer tools
2. Navigate to a profile page
3. Check Network tab for API calls
4. Look for JSON endpoints that return profile data
5. Replicate API calls in Python

### Option 5: Proxy/VPN Rotation
**Requirements:** Proxy service or VPN
**Success Rate:** Moderate
**Speed:** Slow

Use rotating IP addresses to avoid rate limiting and detection.

## 🛠️ Implementation Steps

### Step 1: Set Up Browser Automation
First, let's get Selenium working:

```bash
# Check if Chrome is installed
google-chrome --version

# Install ChromeDriver if not present
brew install chromedriver

# Test ChromeDriver
chromedriver --version
```

### Step 2: Test Single Profile Extraction
```bash
# Use the comprehensive scraper
python3 clutch_profile_scraper.py --url "https://clutch.co/profile/100-shapes" --output test_result.json

# Check results
cat test_result.json
```

### Step 3: Batch Processing
Once single profile extraction works:

```bash
# Create a small sample from our URL list
head -10 sitemap_results/extracted_urls_20250604_161856.txt > sample_urls.txt

# Process the sample
python3 clutch_profile_scraper.py --batch-file sample_urls.txt --output sample_profiles.json --delay 5

# Check results
ls -la sample_profiles.json
```

### Step 4: Scale Up Production Run
```bash
# Process larger batches with proper delays
python3 clutch_profile_scraper.py --batch-file sitemap_results/extracted_urls_20250604_161856.txt --output all_profiles.json --delay 10 --sample-size 100
```

## 📊 Expected Data Structure

Each profile will extract to this JSON structure:

```json
{
  "url": "https://clutch.co/profile/100-shapes",
  "company_name": "100 Shapes",
  "tagline": "Digital Innovators & Problem-Solvers", 
  "description": "Innovation with user-centered design and development...",
  "reviews_count": 0,
  "reviews_rating": 0.0,
  "min_project_size": "$25,000+",
  "hourly_rate": "$100 - $149 / hr",
  "employees": "10 - 49",
  "year_founded": "2011",
  "location": "London, England",
  "services": [
    {"service": "UX/UI Design", "percentage": "40%"},
    {"service": "Custom Software Development", "percentage": "20%"},
    {"service": "Digital Strategy", "percentage": "20%"},
    {"service": "Web Development", "percentage": "20%"}
  ],
  "contact_info": {
    "email": "contact@100shapes.com",
    "website": "https://100shapes.com"
  },
  "social_media": {
    "linkedin": "https://linkedin.com/company/100shapes",
    "facebook": "https://facebook.com/100shapes"
  }
}
```

## 🔧 Troubleshooting Common Issues

### Issue 1: ChromeDriver Not Found
```bash
# Install via Homebrew
brew install chromedriver

# Or download manually from https://chromedriver.chromium.org/
```

### Issue 2: 403 Forbidden Errors
- Increase delays between requests (--delay 10 or higher)
- Use different user agent strings
- Try headless vs non-headless browser mode
- Consider proxy rotation

### Issue 3: Incomplete Data Extraction
- Page structure may have changed
- JavaScript elements not fully loaded
- Need to adjust CSS selectors or regex patterns

### Issue 4: Rate Limiting
```bash
# Use longer delays
python3 clutch_profile_scraper.py --delay 30

# Process smaller batches
python3 clutch_profile_scraper.py --sample-size 10
```

## ⚡ Quick Start (Minimal Setup)

If you want to test immediately without installing dependencies:

1. **Manual Method**: Copy profile URLs and manually visit each page, copy data to spreadsheet
2. **Browser Console**: Use browser developer console to run JavaScript extraction
3. **Browser Extension**: Install a web scraper extension and create extraction rules

## 📈 Performance Expectations

With 10,000 URLs from Stage 1:

- **Selenium Method**: ~2-5 hours (with 2-second delays)
- **Manual Method**: Several days
- **API Method**: ~30 minutes (if available)
- **Browser Extension**: 1-2 hours of manual work

## 🎯 Next Steps

1. **Get Selenium Working**: Install Chrome + ChromeDriver
2. **Test Single Profile**: Verify data extraction quality
3. **Small Batch Test**: Process 10-20 profiles to test stability
4. **Production Run**: Process all 10,000 URLs with appropriate delays
5. **Data Analysis**: Analyze extracted company data for insights

## 💡 Pro Tips

1. **Start Small**: Always test with 5-10 profiles first
2. **Monitor Resources**: Check CPU/memory usage during batch processing
3. **Save Incrementally**: Save results after every 100 profiles
4. **Handle Failures**: Implement retry logic for failed extractions
5. **Respect Rate Limits**: Use delays of 5-10 seconds minimum

---

**Ready to proceed?** Start with installing ChromeDriver and testing the Selenium-based scraper on a single profile URL! 