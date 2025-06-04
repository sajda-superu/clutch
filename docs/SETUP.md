# Setup Guide

This guide will help you get the Clutch scraper up and running.

## Environment Setup

### 1. Python Installation
Ensure you have Python 3.7 or higher installed:
```bash
python --version
```

### 2. Clone Repository
```bash
git clone <repository-url>
cd clutch-scraper
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

## Google Sheets Integration (Optional)

If you want to use Google Sheets integration, follow these steps:

### 1. Create Google Cloud Project
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable the following APIs:
   - Google Sheets API
   - Google Drive API

### 2. Create Service Account
1. Go to IAM & Admin > Service Accounts
2. Click "Create Service Account"
3. Give it a name and description
4. Skip roles for now (click "Continue")
5. Click "Done"

### 3. Generate Credentials
1. Click on your service account
2. Go to "Keys" tab
3. Click "Add Key" > "Create New Key"
4. Choose JSON format
5. Download the file

### 4. Setup Credentials
1. Rename the downloaded file to `google_creds.json`
2. Place it in the project root directory
3. **Important**: Never commit this file to version control!

### 5. Share Sheets (Optional)
If you want the service account to automatically create and share sheets:
1. Get the service account email from the JSON file
2. Share your Google Sheets with this email
3. Or let the script create new sheets automatically

## Data Preparation

### Input Data Format
Your CSV should contain columns that map to:
- Company profile URLs
- Company names
- Descriptions
- Ratings (numerical)
- Review counts
- Pricing information
- Company size
- Location
- Services offered

### Sample Data Structure
```csv
profile_url,company_name,description,rating,reviews,min_cost,hourly_rate,size,location
https://clutch.co/profile/company1,Company One,Description here,4.8,25,5000,100,50,New York
```

## Testing Installation

Run a quick test with the simple scraper:
```bash
python examples/clutch_scraper_simple.py data/raw/sample.csv output/test_output.csv
```

## Troubleshooting

### Common Issues

#### Permission Errors
- Ensure you have write permissions to the output directory
- Check that `google_creds.json` has correct permissions

#### Import Errors
- Verify all dependencies are installed: `pip list`
- Try upgrading pip: `pip install --upgrade pip`
- Use virtual environment if conflicts arise

#### Google Sheets Errors
- Verify APIs are enabled in Google Cloud Console
- Check service account has correct permissions
- Ensure credentials file is properly formatted JSON

#### Data Processing Errors
- Check input CSV format and encoding
- Verify required columns are present
- Look for special characters or encoding issues

### Getting Help

1. Check the error message carefully
2. Review the console output for data quality issues
3. Test with a smaller dataset first
4. Check GitHub issues for similar problems

## Performance Tips

- Use the simple scraper for large datasets
- Process data in chunks if memory is limited
- Consider parallel processing for very large datasets
- Monitor memory usage during processing 