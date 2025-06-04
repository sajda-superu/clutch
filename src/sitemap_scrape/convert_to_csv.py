import json
import csv

def json_to_csv(input_file, output_file):
    # Read the JSON file
    with open(input_file, 'r') as json_file:
        data = json.load(json_file)

    # Open the CSV file for writing
    with open(output_file, 'w', newline='') as csv_file:
        # Create a CSV writer object
        csv_writer = csv.writer(csv_file)

        # Write the header row
        if data:
            csv_writer.writerow(data[0].keys())

        # Write the data rows
        for item in data:
            csv_writer.writerow(item.values())

    print(f"CSV file '{output_file}' has been created successfully.")

# Usage
input_json = 'salesforce_consulting_companies.json'
output_csv = 'salesforce_consulting_companies.csv'
json_to_csv(input_json, output_csv)
