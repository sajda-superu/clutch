#!/usr/bin/env python
"""Smart CSV cleaner and scorer for Clutch company data using modular pipelines.

This script processes Clutch.co company data with ratings, reviews, pricing, and service information.
It applies business scoring logic to rank companies based on multiple factors.
"""

import pandas as pd
import argparse
import gspread
import json
import os
import re
from googleapiclient.discovery import build
from google.oauth2 import service_account

# ---------------------------
# Constants & Configurations
# ---------------------------
COLUMN_MAP = {
    'sg-provider-logotype-v2 href': 'clutch_profile_url',
    'provider__cta-link href 5': 'redirect_url',
    'https://andersenlab.com': 'company_website',  # This will be dynamically mapped
    'provider__title-link': 'company_name',
    'provider__description-text-more': 'description',
    'sg-rating__number': 'rating',
    'sg-rating__number 2': 'rating_secondary',
    'sg-rating__reviews': 'review_count',
    'provider__highlights-item': 'min_project_cost',
    'provider__highlights-item 2': 'hourly_rate',
    'provider__highlights-item 3': 'company_size',
    'provider__highlights-item 4': 'location',
    'provider__services-list-item': 'service_1',
    'provider__services-list-item 2': 'service_2',
    'provider__services-list-item 3': 'service_3',
    'provider__services-list-item 4': 'service_4',
    'provider__services-list-item 5': 'service_5',
}

# Services columns to consolidate
SERVICE_COLUMNS = [f'service_{i}' for i in range(1, 21)]  # Extended to cover more services

SCORE_WEIGHTS = {
    'rating_score': 0.3,
    'review_count_score': 0.25,
    'hourly_rate_score': 0.2,
    'project_cost_score': 0.15,
    'company_size_score': 0.1
}

# ---------------------------
# Core Functionality
# ---------------------------
def load_data(input_csv: str) -> pd.DataFrame:
    """Load and validate CSV data with robust error handling."""
    try:
        return pd.read_csv(input_csv, sep='\t', encoding='utf-8')
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
    # Get the first few columns which should contain key data
    columns_to_use = df.columns[:20].tolist()  # Take first 20 columns
    
    # Create a basic mapping
    basic_mapping = {
        df.columns[0]: 'clutch_profile_url',
        df.columns[1]: 'redirect_url', 
        df.columns[2]: 'company_website',
        df.columns[3]: 'company_name',
        df.columns[4]: 'description',
        df.columns[5]: 'rating',
        df.columns[6]: 'rating_secondary',
        df.columns[7]: 'review_count',
        df.columns[8]: 'min_project_cost',
        df.columns[9]: 'hourly_rate',
        df.columns[10]: 'company_size',
        df.columns[11]: 'location',
    }
    
    # Add service columns
    for i in range(12, min(20, len(df.columns))):
        basic_mapping[df.columns[i]] = f'service_{i-11}'
    
    # Select available columns and rename
    available_columns = [col for col in basic_mapping.keys() if col in df.columns]
    selected_df = df[available_columns].copy()
    selected_df = selected_df.rename(columns=basic_mapping)
    
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
    return df.query("rating > 0 and review_count > 0")

def calculate_scores(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate golden scores using vectorized operations."""
    df = df.drop(columns=['clutch_score'], errors='ignore')
    
    if len(df) == 0:
        df['clutch_score'] = []
        return df
    
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
    df['clutch_score'] = (norms * pd.Series(SCORE_WEIGHTS)).sum(axis=1).round(3) * 100
    
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

# --- Google Sheets Integration ---
def connect_to_google_sheets():
    credentials = service_account.Credentials.from_service_account_file(
        'google_creds.json',
        scopes=[
            'https://www.googleapis.com/auth/spreadsheets',
            'https://www.googleapis.com/auth/drive'
        ]
    )
    return gspread.authorize(credentials)

def save_to_google_sheets(df: pd.DataFrame, spreadsheet_name: str, worksheet_name: str = 'Sheet1', user_email: str = None):
    """Saves the DataFrame to a Google Sheet using official Google API methods."""
    try:
        credentials = service_account.Credentials.from_service_account_file(
            'google_creds.json',
            scopes=[
                'https://www.googleapis.com/auth/spreadsheets',
                'https://www.googleapis.com/auth/drive'
            ]
        )
        
        gc = gspread.authorize(credentials)
        drive_service = build('drive', 'v3', credentials=credentials)

        # Spreadsheet handling
        try:
            sh = gc.open(spreadsheet_name)
        except gspread.SpreadsheetNotFound:
            sh = gc.create(spreadsheet_name)
            sh.share(
                credentials.service_account_email,
                perm_type='user', 
                role='writer'
            )

        # Worksheet handling
        try:
            worksheet = sh.worksheet(worksheet_name)
        except gspread.WorksheetNotFound:
            worksheet = sh.add_worksheet(
                title=worksheet_name, 
                rows=max(df.shape[0]+1, 100),
                cols=max(df.shape[1]+1, 20)
            )

        # Data upload
        worksheet.clear()
        worksheet.update(
            [df.columns.values.tolist()] + df.fillna('').values.tolist(),
            value_input_option='USER_ENTERED'
        )

        # User sharing
        if user_email:
            drive_service.permissions().create(
                fileId=sh.id,
                body={'type': 'user', 'role': 'writer', 'emailAddress': user_email},
                fields='id',
                sendNotificationEmail=True
            ).execute()

        print(f"Success: {sh.url}")

    except gspread.exceptions.APIError as e:
        print(f"Google API Error: {e.response.json()['error']['message']}")
    except Exception as e:
        print(f"General Error: {str(e)}")

# ---------------------------
# Main Execution
# ---------------------------
def main():
    parser = argparse.ArgumentParser(description='Process Clutch company data')
    parser.add_argument('input_file', help='Input CSV file path')
    parser.add_argument('output_file', help='Output CSV file path')
    parser.add_argument('--sheet_name', help='Google Sheet name', default='Clutch Company Data')
    parser.add_argument('--worksheet_name', help='Google Sheet worksheet name', default='Sheet1')
    parser.add_argument('--user_email', help='Email to share the sheet with', default=None)

    args = parser.parse_args()
    
    df = load_data(args.input_file)
    print(f"Loaded {len(df)} companies from {args.input_file}")
    
    transformed_df = transform_data(df)
    print(f"Processed {len(transformed_df)} valid companies")
    
    save_data(transformed_df, args.output_file)
    print(f"Saved processed data to {args.output_file}")
    
    # Save to Google Sheets if credentials available
    if os.path.exists('google_creds.json'):
        save_to_google_sheets(transformed_df, args.sheet_name, args.worksheet_name, args.user_email)
    else:
        print("Google credentials not found. Skipping Google Sheets upload.")
    
    print(f"Successfully processed {len(df)} companies to {args.output_file}")
    if len(transformed_df) > 0:
        print(f"Top scored company: {transformed_df.iloc[0]['company_name']} (Score: {transformed_df.iloc[0]['clutch_score']:.1f})")

if __name__ == '__main__':
    main() 