#!/usr/bin/env python3
"""
Clutch Intelligence - Central Configuration

This file contains all configuration settings for the Clutch Intelligence project.
Modify these settings to customize behavior for different environments.
"""

import os
from pathlib import Path

# Project structure
PROJECT_ROOT = Path(__file__).parent.parent
SCRAPERS_DIR = PROJECT_ROOT / "scrapers"
DATA_DIR = PROJECT_ROOT / "data"
LOGS_DIR = PROJECT_ROOT / "logs"
EXPORTS_DIR = DATA_DIR / "exports"

# Data directories
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"

# Stage-specific directories
STAGE1_DIR = SCRAPERS_DIR / "stage1_sitemaps"
STAGE2_DIR = SCRAPERS_DIR / "stage2_profiles"

# File paths
SITEMAP_MASTER_LIST = PROCESSED_DATA_DIR / "clutch_profile_sitemaps_master_list.txt"
EXTRACTED_URLS_CSV = EXPORTS_DIR / "sitemap_results" / "extracted_urls_20250604_161856.csv"
EXTRACTED_URLS_TXT = EXPORTS_DIR / "sitemap_results" / "extracted_urls_20250604_161856.txt"

# Scraping configuration
SCRAPING_CONFIG = {
    # Request delays (seconds)
    "default_delay": 3.0,
    "conservative_delay": 10.0,
    "aggressive_delay": 1.0,
    
    # Batch sizes
    "small_batch": 10,
    "medium_batch": 100,
    "large_batch": 500,
    
    # Timeouts
    "request_timeout": 30,
    "page_load_timeout": 10,
    
    # User agents
    "user_agents": [
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ],
    
    # Selenium settings
    "headless": True,
    "window_size": (1920, 1080),
    
    # Retry settings
    "max_retries": 3,
    "retry_delay": 2.0,
}

# Output configuration
OUTPUT_CONFIG = {
    "default_format": "json",
    "timestamp_format": "%Y%m%d_%H%M%S",
    "csv_encoding": "utf-8",
    "json_indent": 2,
    
    # File naming patterns
    "sitemap_results_pattern": "sitemap_extraction_{timestamp}",
    "profile_results_pattern": "profile_extraction_{timestamp}",
    "batch_results_pattern": "batch_{batch_id}_{timestamp}",
}

# Logging configuration
LOGGING_CONFIG = {
    "level": "INFO",
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    "file_handler": True,
    "console_handler": True,
    "log_file": LOGS_DIR / "clutch_intelligence.log",
    "max_file_size": 10485760,  # 10MB
    "backup_count": 5,
}

# Target URLs and domains
CLUTCH_CONFIG = {
    "base_url": "https://clutch.co",
    "sitemap_url": "https://clutch.co/sitemap.xml",
    "profile_url_pattern": "https://clutch.co/profile/{company_slug}",
    
    # Expected data fields for validation
    "required_profile_fields": [
        "company_name", "url", "reviews_count", "location"
    ],
    "optional_profile_fields": [
        "tagline", "description", "min_project_size", "hourly_rate",
        "employees", "year_founded", "services", "contact_info", "social_media"
    ],
}

# Database configuration (if needed for future expansion)
DATABASE_CONFIG = {
    "enabled": False,
    "type": "sqlite",
    "path": DATA_DIR / "clutch_intelligence.db",
    "tables": {
        "companies": "companies",
        "services": "services", 
        "contacts": "contacts",
        "extraction_runs": "extraction_runs"
    }
}

# Performance monitoring
PERFORMANCE_CONFIG = {
    "track_metrics": True,
    "metrics_file": LOGS_DIR / "performance_metrics.json",
    "alert_thresholds": {
        "success_rate_min": 0.8,  # 80% minimum success rate
        "avg_response_time_max": 15.0,  # 15 seconds max average
        "error_rate_max": 0.2,  # 20% maximum error rate
    }
}

def ensure_directories():
    """Create all necessary directories if they don't exist."""
    directories = [
        PROJECT_ROOT, SCRAPERS_DIR, DATA_DIR, LOGS_DIR, EXPORTS_DIR,
        RAW_DATA_DIR, PROCESSED_DATA_DIR, STAGE1_DIR, STAGE2_DIR
    ]
    
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)

def get_output_path(pattern: str, **kwargs) -> Path:
    """Generate output file path based on pattern and parameters."""
    from datetime import datetime
    
    timestamp = datetime.now().strftime(OUTPUT_CONFIG["timestamp_format"])
    filename = pattern.format(timestamp=timestamp, **kwargs)
    
    return EXPORTS_DIR / f"{filename}.{OUTPUT_CONFIG['default_format']}"

if __name__ == "__main__":
    # Create directories when run directly
    ensure_directories()
    print("✓ Clutch Intelligence directory structure created")
    print(f"✓ Project root: {PROJECT_ROOT}")
    print(f"✓ Data directory: {DATA_DIR}")
    print(f"✓ Logs directory: {LOGS_DIR}") 