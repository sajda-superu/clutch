#!/usr/bin/env python
"""Simple CSV cleaner and scorer for Clutch company data.

This script processes Clutch.co company data with ratings, reviews, pricing, and service information.
"""

import pandas as pd
import argparse

# ---------------------------
# Core Functionality
# ---------------------------
def load_data(input_csv: str) -> pd.DataFrame:
    """Load and validate CSV data with robust error handling."""
    try:
        return pd.read_csv(input_csv, sep=',', encoding='utf-8')
    except FileNotFoundError:
        exit(f"Error: Input file not found at {input_csv}")
    except pd.errors.EmptyDataError:
        exit(f"Error: Empty input file {input_csv}")
    except pd.errors.ParserError:
        exit(f"Error: Malformed data in {input_csv}")

def transform_data(df: pd.DataFrame) -> pd.DataFrame:
    """Perform all data transformations in a single pipeline."""
    return (df
            .pipe(select_and_rename_columns)
            .pipe(process_services)
            .pipe(convert_numerics)
            .pipe(filter_valid_rows)
            .pipe(calculate_scores)
            .pipe(clean_strings)
    )

def select_and_rename_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Select and rename required columns dynamically."""
    print(f"Data shape: {df.shape}")
    print(f"Columns: {list(df.columns[:15])}")
    
    # Map based on actual column structure observed in the data
    # The data has structure: profile_url, redirect_url, website, name, description, rating, rating2, reviews, cost, hourly, size, location...
    column_mapping = {}
    
    if len(df.columns) >= 12:
        column_mapping = {
            df.columns[0]: 'clutch_profile_url',      # sg-provider-logotype-v2 href
            df.columns[1]: 'redirect_url',            # provider__cta-link href 5  
            df.columns[2]: 'company_website',         # actual website URL
            df.columns[3]: 'company_name',            # provider__title-link
            df.columns[4]: 'description',             # provider__description-text-more
            df.columns[5]: 'rating',                  # sg-rating__number
            df.columns[6]: 'rating_secondary',        # sg-rating__number 2
            df.columns[7]: 'review_count',            # sg-rating__reviews
            df.columns[8]: 'min_project_cost',        # provider__highlights-item
            df.columns[9]: 'hourly_rate',             # provider__highlights-item 2
            df.columns[10]: 'company_size',           # provider__highlights-item 3
            df.columns[11]: 'location',               # provider__highlights-item 4
        }
        
        # Add service columns
        for i in range(12, min(len(df.columns), 20)):
            column_mapping[df.columns[i]] = f'service_{i-11}'
    
    # Select available columns and rename
    available_columns = [col for col in column_mapping.keys() if col in df.columns]
    selected_df = df[available_columns].copy()
    selected_df = selected_df.rename(columns=column_mapping)
    
    print(f"Selected {len(selected_df.columns)} columns: {list(selected_df.columns)}")
    return selected_df

def process_services(df: pd.DataFrame) -> pd.DataFrame:
    """Consolidate service columns into a single list."""
    service_cols = [col for col in df.columns if col.startswith('service_')]
    if service_cols:
        df['services'] = df[service_cols].apply(
            lambda x: [str(val) for val in x.dropna() if str(val).strip() and str(val) != 'nan'], 
            axis=1
        )
        df = df.drop(columns=service_cols)
    else:
        df['services'] = [[] for _ in range(len(df))]
    return df

def convert_numerics(df: pd.DataFrame) -> pd.DataFrame:
    """Convert all numeric columns using vectorized operations."""
    df = df.copy()
    
    # Convert rating
    if 'rating' in df.columns:
        df['rating'] = pd.to_numeric(df['rating'], errors='coerce').fillna(0)
    
    # Convert review count (extract number from strings like "126 reviews")
    if 'review_count' in df.columns:
        df['review_count'] = pd.to_numeric(
            df['review_count'].astype(str).str.extract(r'(\d+)')[0],
            errors='coerce'
        ).fillna(0)
    
    # Convert min project cost (handle formats like $50,000+)
    if 'min_project_cost' in df.columns:
        df['min_project_cost'] = df['min_project_cost'].apply(parse_currency)
    
    # Convert hourly rate (extract first number from ranges like $50 - $99 / hr)
    if 'hourly_rate' in df.columns:
        df['hourly_rate'] = pd.to_numeric(
            df['hourly_rate'].astype(str).str.extract(r'\$(\d+)')[0],
            errors='coerce'
        ).fillna(0)
    
    # Convert company size (extract first number from ranges like 1,000 - 9,999)
    if 'company_size' in df.columns:
        df['company_size'] = pd.to_numeric(
            df['company_size'].astype(str).str.replace(',', '').str.extract(r'(\d+)')[0],
            errors='coerce'
        ).fillna(0)
    
    return df

def parse_currency(value: str) -> float:
    """Parse currency values with K/M suffixes and + indicators."""
    if pd.isna(value) or str(value).strip() == '' or str(value) == 'nan':
        return 0.0
    
    value = str(value).replace('$', '').replace('+', '').replace(',', '').strip()
    multiplier = 1
    
    if 'K' in value.upper():
        multiplier = 1000
        value = value.upper().replace('K', '')
    elif 'M' in value.upper():
        multiplier = 1_000_000
        value = value.upper().replace('M', '')
    
    try:
        return float(value) * multiplier
    except ValueError:
        return 0.0

def filter_valid_rows(df: pd.DataFrame) -> pd.DataFrame:
    """Filter rows based on business rules."""
    # Filter companies with ratings and reviews
    valid_df = df.query("rating > 0 and review_count > 0")
    print(f"Filtered from {len(df)} to {len(valid_df)} valid companies")
    return valid_df

def calculate_scores(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate golden scores using vectorized operations."""
    df = df.drop(columns=['clutch_score'], errors='ignore')
    
    if len(df) == 0:
        df['clutch_score'] = []
        return df
    
    # Score weights
    score_weights = {
        'rating_score': 0.3,
        'review_count_score': 0.25,
        'hourly_rate_score': 0.2,
        'project_cost_score': 0.15,
        'company_size_score': 0.1
    }
    
    # Calculate component scores (normalized 0-1)
    max_rating = 5.0  # Clutch uses 5-star rating
    max_reviews = df['review_count'].max() if df['review_count'].max() > 0 else 1
    max_cost = df['min_project_cost'].max() if df['min_project_cost'].max() > 0 else 1
    max_rate = df['hourly_rate'].max() if df['hourly_rate'].max() > 0 else 1
    max_size = df['company_size'].max() if df['company_size'].max() > 0 else 1
    
    # Normalize scores
    norms = pd.DataFrame({
        'rating_score': df['rating'] / max_rating,
        'review_count_score': df['review_count'] / max_reviews,
        'project_cost_score': df['min_project_cost'] / max_cost,
        'hourly_rate_score': 1 - (df['hourly_rate'] / max_rate),  # Lower hourly rate is better
        'company_size_score': df['company_size'] / max_size,
    })
    
    # Calculate weighted score
    df['clutch_score'] = (norms * pd.Series(score_weights)).sum(axis=1).round(3) * 100
    
    return df.sort_values('clutch_score', ascending=False)

def clean_strings(df: pd.DataFrame) -> pd.DataFrame:
    """Escape double quotes in string columns as per RFC 4180."""
    str_cols = df.select_dtypes(include='object').columns
    for col in str_cols:
        if col in df.columns:
            df[col] = df[col].astype(str).str.replace('"', '""', regex=False)
    return df

def save_data(df: pd.DataFrame, output_csv: str) -> None:
    """Save the transformed data to CSV with proper formatting."""
    df.to_csv(output_csv, index=False, quoting=1, quotechar='"', encoding='utf-8')

# ---------------------------
# Main Execution
# ---------------------------
def main():
    parser = argparse.ArgumentParser(description='Process Clutch company data')
    parser.add_argument('input_file', help='Input CSV file path')
    parser.add_argument('output_file', help='Output CSV file path')

    args = parser.parse_args()
    
    print(f"Loading data from: {args.input_file}")
    df = load_data(args.input_file)
    print(f"Loaded {len(df)} companies from {args.input_file}")
    
    transformed_df = transform_data(df)
    print(f"Processed {len(transformed_df)} valid companies")
    
    save_data(transformed_df, args.output_file)
    print(f"Saved processed data to {args.output_file}")
    
    if len(transformed_df) > 0:
        print(f"\nTop 5 scored companies:")
        top_companies = transformed_df[['company_name', 'rating', 'review_count', 'clutch_score']].head()
        print(top_companies.to_string(index=False))
        
        print(f"\nSample company details:")
        print(f"Company: {transformed_df.iloc[0]['company_name']}")
        print(f"Score: {transformed_df.iloc[0]['clutch_score']:.1f}")
        print(f"Rating: {transformed_df.iloc[0]['rating']}")
        print(f"Reviews: {transformed_df.iloc[0]['review_count']}")
        print(f"Location: {transformed_df.iloc[0]['location']}")

if __name__ == '__main__':
    main() 