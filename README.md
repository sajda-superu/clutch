# Clutch Company Data Scraper & Scorer

A Python tool for processing and scoring Clutch.co company data to help identify top-rated service providers based on multiple criteria.

## 🎯 Overview

This tool processes Clutch.co company data and creates a comprehensive scoring system based on:
- Company ratings (30%)
- Review count (25%) 
- Hourly rates (20%)
- Project cost capabilities (15%)
- Company size (10%)

## 📁 Project Structure

```
clutch/
├── src/                    # Source code
│   └── clutch_scraper.py  # Main scraper with Google Sheets integration
├── data/                  # Data directory
│   └── raw/              # Raw input data
├── output/               # Generated output files
├── examples/             # Example scripts and usage
├── docs/                 # Documentation
├── requirements.txt      # Python dependencies
└── README.md            # This file
```

## 🚀 Quick Start

### Prerequisites

- Python 3.7+
- Required packages (see requirements.txt)

### Installation

1. Clone this repository
2. Install dependencies:
```bash
pip install -r requirements.txt
```

### Basic Usage

```bash
python src/clutch_scraper.py input_data.csv output_results.csv
```

### With Google Sheets Integration

```bash
python src/clutch_scraper.py input_data.csv output_results.csv \
  --sheet_name "Clutch Analysis" \
  --worksheet_name "Companies" \
  --user_email "your-email@domain.com"
```

## 📊 Input Data Format

The script expects CSV data with the following structure:
- Company profile URLs
- Company names and descriptions
- Ratings and review counts
- Pricing information (hourly rates, project costs)
- Company size and location data
- Services offered

## 📈 Output

The tool generates:
- **Scored CSV file** with all company data plus calculated scores
- **Google Sheet** (optional) for collaborative analysis
- **Console output** showing top-ranked companies

### Sample Output

```
Top 5 scored companies:
          company_name  rating  review_count  clutch_score
         Andersen Inc.     4.9         126.0          94.4
              Britenet     4.8          26.0          79.0
             Algoworks     4.9          98.0          74.3
Closeloop Technologies     5.0          40.0          63.4
              DianApps     4.8          73.0          62.8
```

## ⚙️ Configuration

### Scoring Weights

You can modify the scoring weights in the script:

```python
SCORE_WEIGHTS = {
    'rating_score': 0.3,         # Company rating (1-5 stars)
    'review_count_score': 0.25,  # Number of reviews
    'hourly_rate_score': 0.2,    # Hourly rate (lower is better)
    'project_cost_score': 0.15,  # Minimum project cost
    'company_size_score': 0.1    # Employee count
}
```

### Google Sheets Setup

1. Create a Google Cloud Project
2. Enable Google Sheets and Drive APIs
3. Create a service account
4. Download credentials as `google_creds.json`
5. Place in the project root directory

## 🔧 Features

- **Automatic data cleaning** - Handles currency formats, extracts numbers from text
- **Flexible scoring** - Customizable weights for different criteria
- **Google Sheets integration** - Collaborative analysis and sharing
- **Data validation** - Filters invalid entries automatically
- **Comprehensive output** - Detailed CSV with all processed data

## 📝 Examples

See the `examples/` directory for:
- `clutch_scraper_simple.py` - Basic version without Google Sheets
- Sample data processing workflows
- Configuration examples

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For issues or questions:
1. Check existing GitHub issues
2. Create a new issue with detailed description
3. Include sample data and error messages if applicable

## 🔄 Version History

- **v1.0.0** - Initial release with core functionality
- **v1.1.0** - Added Google Sheets integration
- **v1.2.0** - Improved data processing and error handling 