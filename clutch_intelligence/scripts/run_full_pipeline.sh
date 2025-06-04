#!/bin/bash

# Clutch Intelligence - Full Pipeline Execution Script
# This script runs the complete data extraction pipeline from sitemap to profiles

set -e  # Exit on any error

echo "🧠 Clutch Intelligence - Full Pipeline Starting..."
echo "=================================================="

# Configuration
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
STAGE1_DIR="$PROJECT_ROOT/scrapers/stage1_sitemaps"
STAGE2_DIR="$PROJECT_ROOT/scrapers/stage2_profiles"
DATA_DIR="$PROJECT_ROOT/data"
EXPORTS_DIR="$DATA_DIR/exports"
LOGS_DIR="$PROJECT_ROOT/logs"

# Parameters with defaults
BATCH_SIZE=${1:-100}
DELAY=${2:-5}
MODE=${3:-"full"}  # Options: full, stage1, stage2, sample

echo "📋 Pipeline Configuration:"
echo "   Batch Size: $BATCH_SIZE companies"
echo "   Delay: $DELAY seconds between requests"
echo "   Mode: $MODE"
echo "   Project Root: $PROJECT_ROOT"
echo ""

# Ensure directories exist
mkdir -p "$LOGS_DIR"
mkdir -p "$EXPORTS_DIR"

# Generate timestamp for this run
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
LOG_FILE="$LOGS_DIR/pipeline_run_$TIMESTAMP.log"

# Logging function
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log "🚀 Starting Clutch Intelligence Pipeline Run"
log "Configuration: batch_size=$BATCH_SIZE, delay=$DELAY, mode=$MODE"

# Stage 1: Sitemap Processing (if needed)
if [[ "$MODE" == "full" || "$MODE" == "stage1" ]]; then
    log "📍 Stage 1: Processing Sitemaps..."
    
    cd "$STAGE1_DIR"
    
    # Check if master sitemap list exists
    MASTER_LIST="$DATA_DIR/processed/clutch_profile_sitemaps_master_list.txt"
    if [[ ! -f "$MASTER_LIST" ]]; then
        log "❌ Master sitemap list not found: $MASTER_LIST"
        log "Please ensure Stage 1 setup is complete"
        exit 1
    fi
    
    # Check if URLs already extracted
    EXTRACTED_URLS="$EXPORTS_DIR/sitemap_results/extracted_urls_"*.txt
    if ls $EXTRACTED_URLS 1> /dev/null 2>&1; then
        log "✅ Stage 1 already completed - URLs found"
        LATEST_URLS=$(ls -t $EXTRACTED_URLS | head -n 1)
        URL_COUNT=$(wc -l < "$LATEST_URLS")
        log "   Using existing URL list: $LATEST_URLS ($URL_COUNT URLs)"
    else
        log "🔄 Running sitemap extraction..."
        python bulk_sitemap_processor.py --batch "$MASTER_LIST" --delay 3 2>&1 | tee -a "$LOG_FILE"
        
        # Verify extraction success
        if ls $EXTRACTED_URLS 1> /dev/null 2>&1; then
            LATEST_URLS=$(ls -t $EXTRACTED_URLS | head -n 1)
            URL_COUNT=$(wc -l < "$LATEST_URLS")
            log "✅ Stage 1 completed successfully: $URL_COUNT URLs extracted"
        else
            log "❌ Stage 1 failed - no URLs extracted"
            exit 1
        fi
    fi
    
    cd "$PROJECT_ROOT"
fi

# Stage 2: Profile Data Extraction
if [[ "$MODE" == "full" || "$MODE" == "stage2" || "$MODE" == "sample" ]]; then
    log "📍 Stage 2: Extracting Profile Data..."
    
    cd "$STAGE2_DIR"
    
    # Find the latest URL file if not set from Stage 1
    if [[ -z "$LATEST_URLS" ]]; then
        EXTRACTED_URLS="$EXPORTS_DIR/sitemap_results/extracted_urls_"*.txt
        if ls $EXTRACTED_URLS 1> /dev/null 2>&1; then
            LATEST_URLS=$(ls -t $EXTRACTED_URLS | head -n 1)
            log "📄 Using URL file: $LATEST_URLS"
        else
            log "❌ No URL files found. Run Stage 1 first."
            exit 1
        fi
    fi
    
    # Create batch file based on mode
    BATCH_FILE="batch_urls_$TIMESTAMP.txt"
    
    if [[ "$MODE" == "sample" ]]; then
        # Sample mode: process first 10 URLs for testing
        head -10 "$LATEST_URLS" > "$BATCH_FILE"
        ACTUAL_BATCH_SIZE=10
        log "🧪 Sample mode: processing first 10 URLs"
    else
        # Full/Stage2 mode: process specified batch size
        head -"$BATCH_SIZE" "$LATEST_URLS" > "$BATCH_FILE"
        ACTUAL_BATCH_SIZE=$BATCH_SIZE
        log "🏭 Production mode: processing $BATCH_SIZE URLs"
    fi
    
    # Verify batch file created
    if [[ ! -f "$BATCH_FILE" || ! -s "$BATCH_FILE" ]]; then
        log "❌ Failed to create batch file or file is empty"
        exit 1
    fi
    
    BATCH_COUNT=$(wc -l < "$BATCH_FILE")
    log "📊 Batch created: $BATCH_COUNT URLs to process"
    
    # Run profile extraction
    OUTPUT_FILE="profile_extraction_$TIMESTAMP.json"
    log "🔄 Running profile extraction with $DELAY second delays..."
    log "   Output file: $OUTPUT_FILE"
    log "   Estimated time: $(($BATCH_COUNT * $DELAY / 60)) minutes"
    
    python clutch_profile_scraper.py \
        --batch-file "$BATCH_FILE" \
        --output "$OUTPUT_FILE" \
        --delay "$DELAY" \
        2>&1 | tee -a "$LOG_FILE"
    
    # Verify extraction results
    if [[ -f "$OUTPUT_FILE" ]]; then
        # Count successful extractions (assuming JSON array format)
        SUCCESS_COUNT=$(python -c "
import json
try:
    with open('$OUTPUT_FILE', 'r') as f:
        data = json.load(f)
    if isinstance(data, list):
        success = sum(1 for item in data if item.get('company_name') and item.get('company_name') != 'clutch.co')
    else:
        success = 1 if data.get('company_name') and data.get('company_name') != 'clutch.co' else 0
    print(success)
except:
    print(0)
        ")
        
        SUCCESS_RATE=$(python -c "print(f'{$SUCCESS_COUNT/$BATCH_COUNT*100:.1f}')")
        
        log "✅ Stage 2 completed!"
        log "   Processed: $BATCH_COUNT URLs"
        log "   Successful: $SUCCESS_COUNT extractions"
        log "   Success Rate: $SUCCESS_RATE%"
        log "   Output: $OUTPUT_FILE"
        
        # Move output to exports directory
        mv "$OUTPUT_FILE" "$EXPORTS_DIR/"
        OUTPUT_PATH="$EXPORTS_DIR/$OUTPUT_FILE"
        log "   Final location: $OUTPUT_PATH"
        
    else
        log "❌ Stage 2 failed - no output file generated"
        exit 1
    fi
    
    # Cleanup temporary files
    rm -f "$BATCH_FILE"
    
    cd "$PROJECT_ROOT"
fi

# Final summary
log "🎉 Pipeline completed successfully!"
log "📁 Results available in: $EXPORTS_DIR"
log "📋 Full log available at: $LOG_FILE"

echo ""
echo "🎯 Pipeline Summary:"
echo "   Mode: $MODE"
echo "   Success Rate: ${SUCCESS_RATE:-N/A}%"
echo "   Output: ${OUTPUT_PATH:-N/A}"
echo "   Log: $LOG_FILE"
echo ""
echo "🚀 Ready for production scaling!" 