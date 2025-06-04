# Examples

This directory contains example scripts and usage patterns for the Clutch scraper.

## Files

### `clutch_scraper_simple.py`
A simplified version of the main scraper without Google Sheets integration. Perfect for:
- Quick data processing
- Local-only analysis
- Learning the basic workflow
- Environments where Google API setup isn't feasible

**Usage:**
```bash
python clutch_scraper_simple.py input_data.csv output_results.csv
```

## Sample Workflows

### Basic Data Processing
1. Place your Clutch data CSV in `data/raw/`
2. Run the simple scraper for quick analysis
3. Review output in `output/` directory

### Advanced Analysis with Google Sheets
1. Set up Google API credentials
2. Use the main scraper with sheets integration
3. Share results with team members via Google Sheets

### Custom Scoring
Modify the scoring weights in either script to match your criteria:
- Prioritize ratings over review count
- Weight pricing differently
- Adjust for company size preferences

## Tips

- Always backup your raw data
- Test with small datasets first
- Review the console output for data quality insights
- Use the Google Sheets integration for collaborative analysis 