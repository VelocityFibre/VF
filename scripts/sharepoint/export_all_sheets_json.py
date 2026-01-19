#!/usr/bin/env python3
"""
Export ALL sheets from SharePoint Excel file to JSON
"""
import requests
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# SharePoint credentials from environment
TENANT_ID = os.getenv('SHAREPOINT_TENANT_ID')
CLIENT_ID = os.getenv('SHAREPOINT_CLIENT_ID')
CLIENT_SECRET = os.getenv('SHAREPOINT_CLIENT_SECRET')
SITE_PATH = os.getenv('SHAREPOINT_SITE_PATH', '/sites/Velocity_Manco')

# The specific file we want
FILE_NAME = "VF_Project_Tracker_Mohadin.xlsx"

def get_access_token():
    """Get access token for Microsoft Graph API"""
    token_url = f"https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/token"

    data = {
        'grant_type': 'client_credentials',
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'scope': 'https://graph.microsoft.com/.default'
    }

    response = requests.post(token_url, data=data)
    return response.json()['access_token']

def get_site_id(access_token):
    """Get SharePoint site ID"""
    url = f"https://graph.microsoft.com/v1.0/sites/blitzfibre.sharepoint.com:{SITE_PATH}"
    headers = {'Authorization': f'Bearer {access_token}'}

    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()['id']

def find_file(access_token, site_id):
    """Find the specific Excel file"""
    headers = {'Authorization': f'Bearer {access_token}'}

    folder_path = "Velocity_Manco_Trackers/Velocity_Tracker_Projects"
    url = f"https://graph.microsoft.com/v1.0/sites/{site_id}/drive/root:/{folder_path}:/children"

    response = requests.get(url, headers=headers)
    results = response.json()

    for item in results.get('value', []):
        if item['name'] == FILE_NAME:
            return item['id']

    raise Exception(f"File '{FILE_NAME}' not found")

def get_sheet_names(access_token, site_id, file_id):
    """Get all sheet names from the Excel file"""
    headers = {'Authorization': f'Bearer {access_token}'}
    url = f"https://graph.microsoft.com/v1.0/sites/{site_id}/drive/items/{file_id}/workbook/worksheets"

    response = requests.get(url, headers=headers)
    sheets = response.json()

    return [sheet['name'] for sheet in sheets.get('value', [])]

def get_sheet_data(access_token, site_id, file_id, sheet_name):
    """Get data from a specific sheet"""
    headers = {'Authorization': f'Bearer {access_token}'}
    url = f"https://graph.microsoft.com/v1.0/sites/{site_id}/drive/items/{file_id}/workbook/worksheets/{sheet_name}/usedRange"

    response = requests.get(url, headers=headers)
    data = response.json()

    return data.get('values', [])

def export_sheet_to_json(sheet_name, sheet_data):
    """Convert sheet to JSON format"""
    if not sheet_data or len(sheet_data) < 2:
        return {"sheet": sheet_name, "rows": 0, "data": []}

    # First row is headers
    headers = sheet_data[0]
    data_rows = sheet_data[1:]

    # Convert rows to dictionaries
    records = []
    for row in data_rows:
        # Skip empty rows
        if not any(cell for cell in row):
            continue

        record = {}
        for i, header in enumerate(headers):
            if i < len(row):
                # Clean header name
                clean_header = str(header).strip().replace(' ', '_').lower()
                if clean_header:
                    record[clean_header] = row[i]

        if record:  # Only add non-empty records
            records.append(record)

    return {
        "sheet": sheet_name,
        "rows": len(records),
        "columns": len(headers),
        "data": records
    }

def main():
    print("=" * 60)
    print("Exporting ALL SharePoint Excel Sheets to JSON")
    print("=" * 60)

    # Get access token
    print("\n🔑 Getting access token...")
    access_token = get_access_token()
    print("✅ Got access token")

    # Get site ID
    print("\n🏢 Getting site ID...")
    site_id = get_site_id(access_token)
    print(f"✅ Got site ID")

    # Find the file
    print(f"\n🔍 Finding file: {FILE_NAME}")
    file_id = find_file(access_token, site_id)
    print(f"✅ Found file")

    # Get all sheet names
    print("\n📋 Getting sheet names...")
    sheet_names = get_sheet_names(access_token, site_id, file_id)
    print(f"✅ Found {len(sheet_names)} sheets")

    # Export each sheet
    print("\n" + "=" * 60)
    print("Exporting sheets...")
    print("=" * 60)

    all_sheets = {}

    for i, sheet_name in enumerate(sheet_names, 1):
        print(f"\n  [{i}/{len(sheet_names)}] Exporting: {sheet_name}")
        try:
            # Get sheet data
            sheet_data = get_sheet_data(access_token, site_id, file_id, sheet_name)

            # Convert to JSON
            json_data = export_sheet_to_json(sheet_name, sheet_data)

            all_sheets[sheet_name] = json_data

            print(f"    ✅ Exported {json_data['rows']} rows, {json_data['columns']} columns")

        except Exception as e:
            print(f"    ❌ Error: {e}")
            all_sheets[sheet_name] = {"error": str(e)}

    # Save to file
    output_file = "all_sharepoint_sheets.json"
    with open(output_file, 'w') as f:
        json.dump(all_sheets, f, indent=2)

    print("\n" + "=" * 60)
    print("✅ Export Complete!")
    print("=" * 60)
    print(f"\nAll sheets exported to: {output_file}")
    print(f"Total sheets: {len(all_sheets)}")

if __name__ == "__main__":
    main()
