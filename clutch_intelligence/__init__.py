"""
Clutch Intelligence - Advanced Company Profile Extraction & Intelligence System

A comprehensive data intelligence platform for extracting and analyzing 
company information from Clutch.co.

Version: 1.0.0
Author: Clutch Intelligence Team
"""

__version__ = "1.0.0"
__author__ = "Clutch Intelligence Team"
__description__ = "Advanced Company Profile Extraction & Intelligence System"

from .config.config import (
    PROJECT_ROOT,
    SCRAPING_CONFIG,
    OUTPUT_CONFIG,
    CLUTCH_CONFIG,
    ensure_directories
)

# Initialize directory structure on import
ensure_directories()

__all__ = [
    "PROJECT_ROOT",
    "SCRAPING_CONFIG", 
    "OUTPUT_CONFIG",
    "CLUTCH_CONFIG",
    "ensure_directories"
] 