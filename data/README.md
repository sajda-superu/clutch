# Data Directory

This directory contains the data files used by the Clutch scraper.

## Structure

```
data/
├── raw/          # Raw input CSV files from Clutch scraping
└── processed/    # Processed and cleaned data (optional)
```

## File Formats

### Raw Data (`raw/` directory)
Contains CSV files scraped from Clutch.co with company information including:
- Company profiles and URLs
- Ratings and review counts
- Pricing information (hourly rates, minimum project costs)
- Company size and location
- Services offered
- Client testimonials and highlights

### Processed Data (`processed/` directory)
Contains cleaned and scored data files:
- Standardized column names
- Converted numeric fields
- Calculated scores
- Filtered valid entries

## Usage

1. **Place your raw CSV files** in the `raw/` directory
2. **Run the scraper** to process the data
3. **Check output** in the `output/` directory or Google Sheets

## Data Privacy

- Raw data files contain public information from Clutch.co
- No personal or sensitive information should be stored here
- Be mindful of Clutch.co's terms of service when using scraped data
- Consider data freshness as Clutch data changes frequently

## Sample Data

The `raw/` directory includes sample data files for testing:
- `list1.csv` - Sample company data from Clutch.co

## File Naming Convention

Use descriptive names for your data files:
- `clutch_companies_YYYY-MM-DD.csv` for dated snapshots
- `category_specific_companies.csv` for filtered datasets
- `region_companies.csv` for geographic filtering 