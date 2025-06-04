#!/bin/bash

# Sitemap Download Helper Script
# This script helps download sitemaps that are protected by Cloudflare or other services

# Default headers for requests
USER_AGENT="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

# Function to download a single sitemap
download_sitemap() {
    local url="$1"
    local output_file="$2"
    
    echo "Downloading: $url"
    echo "Output file: $output_file"
    
    curl -H "User-Agent: $USER_AGENT" \
         -H "Accept: application/xml,text/xml,*/*" \
         -H "Accept-Language: en-US,en;q=0.9" \
         -H "Accept-Encoding: gzip, deflate, br" \
         -H "Cache-Control: no-cache" \
         -L \
         --compressed \
         -o "$output_file" \
         "$url"
    
    if [ $? -eq 0 ]; then
        echo "✓ Successfully downloaded $output_file"
        
        # Check if it's actually XML
        if head -1 "$output_file" | grep -q "<?xml"; then
            echo "✓ File appears to be valid XML"
        else
            echo "⚠  Warning: File may not be valid XML (check for Cloudflare protection)"
            echo "First line: $(head -1 "$output_file")"
        fi
    else
        echo "✗ Failed to download $url"
    fi
    echo "---"
}

# Function to download multiple sitemaps from a list
download_from_list() {
    local list_file="$1"
    local delay="${2:-2}"
    
    if [ ! -f "$list_file" ]; then
        echo "Error: List file '$list_file' not found"
        return 1
    fi
    
    echo "Downloading sitemaps from: $list_file"
    echo "Using delay: $delay seconds between requests"
    echo "=================================================="
    
    local counter=1
    while IFS= read -r line; do
        # Skip empty lines and comments
        if [[ -z "$line" || "$line" =~ ^[[:space:]]*# ]]; then
            continue
        fi
        
        # Extract filename from URL
        local filename=$(basename "$line")
        if [[ "$filename" != *.xml ]]; then
            filename="sitemap_$counter.xml"
        fi
        
        download_sitemap "$line" "$filename"
        
        # Add delay between downloads
        if [ $delay -gt 0 ]; then
            echo "Waiting $delay seconds..."
            sleep $delay
        fi
        
        ((counter++))
    done < "$list_file"
}

# Function to show usage
show_usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -u URL          Download single sitemap from URL"
    echo "  -o OUTPUT       Output filename (default: sitemap.xml)"
    echo "  -l LIST_FILE    Download multiple sitemaps from list file"
    echo "  -d DELAY        Delay between downloads in seconds (default: 2)"
    echo "  -h              Show this help"
    echo ""
    echo "Examples:"
    echo "  $0 -u https://example.com/sitemap.xml -o example_sitemap.xml"
    echo "  $0 -l sitemap_list.txt -d 3"
    echo ""
    echo "For Clutch.co specifically:"
    echo "  $0 -u https://clutch.co/sitemap-profile-9.xml -o clutch_profile_9.xml"
}

# Parse command line arguments
OUTPUT_FILE="sitemap.xml"
DELAY=2

while getopts "u:o:l:d:h" opt; do
    case $opt in
        u)
            URL="$OPTARG"
            ;;
        o)
            OUTPUT_FILE="$OPTARG"
            ;;
        l)
            LIST_FILE="$OPTARG"
            ;;
        d)
            DELAY="$OPTARG"
            ;;
        h)
            show_usage
            exit 0
            ;;
        \?)
            echo "Invalid option: -$OPTARG" >&2
            show_usage
            exit 1
            ;;
    esac
done

# Main execution
if [ ! -z "$URL" ]; then
    # Download single sitemap
    download_sitemap "$URL" "$OUTPUT_FILE"
elif [ ! -z "$LIST_FILE" ]; then
    # Download from list
    download_from_list "$LIST_FILE" "$DELAY"
else
    echo "Error: Either -u URL or -l LIST_FILE must be specified"
    show_usage
    exit 1
fi 