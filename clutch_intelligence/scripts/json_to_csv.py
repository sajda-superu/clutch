import json
import csv
import os
from typing import Dict, List

def flatten_dict(d: Dict, parent_key: str = '', sep: str = '_') -> Dict:
    """Flatten nested dictionary with custom separator"""
    items: List = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        elif isinstance(v, list):
            items.append((new_key, ', '.join(str(x) for x in v)))
        else:
            items.append((new_key, v))
    return dict(items)

def json_to_csv(json_file: str, csv_file: str):
    """Convert JSON file to CSV with flattened structure"""
    # Read JSON data
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    if not data:
        print("No data found in JSON file")
        return
    
    # Flatten all records
    flattened_data = [flatten_dict(record) for record in data]
    
    # Get all possible fields
    fieldnames = set()
    for record in flattened_data:
        fieldnames.update(record.keys())
    fieldnames = sorted(list(fieldnames))
    
    # Write to CSV
    with open(csv_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(flattened_data)
    
    print(f"Successfully converted {json_file} to {csv_file}")
    print(f"Number of records: {len(data)}")
    print(f"Number of fields: {len(fieldnames)}")

if __name__ == "__main__":
    json_file = "data/exports/scraped_profiles/all_results.json"
    csv_file = "data/exports/scraped_profiles/all_results.csv"
    
    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(csv_file), exist_ok=True)
    
    json_to_csv(json_file, csv_file) 