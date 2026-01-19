#!/usr/bin/env python3
"""
Sync ALL sheets from SharePoint Excel file to Convex
Each sheet becomes a separate Convex table
"""
import requests
import json
from convex import ConvexClient
import os
from dotenv import load_dotenv

load_dotenv()

# SharePoint credentials from environment
TENANT_ID = os.getenv('SHAREPOINT_TENANT_ID')
CLIENT_ID = os.getenv('SHAREPOINT_CLIENT_ID')
CLIENT_SECRET = os.getenv('SHAREPOINT_CLIENT_SECRET')
SITE_PATH = os.getenv('SHAREPOINT_SITE_PATH', '/sites/Velocity_Manco')

# The specific file we want
FILE_NAME = "VF_Project_Tracker_Mohadin.xlsx"

# Initialize Convex client
client = ConvexClient(os.getenv("CONVEX_URL"))

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

    # Search in Velocity_Manco_Trackers/Velocity_Tracker_Projects folder
    folder_path = "Velocity_Manco_Trackers/Velocity_Tracker_Projects"
    url = f"https://graph.microsoft.com/v1.0/sites/{site_id}/drive/root:/{folder_path}:/children"

    response = requests.get(url, headers=headers)
    results = response.json()

    print(f"  Found {len(results.get('value', []))} items in {folder_path}")

    for item in results.get('value', []):
        item_type = "📁" if 'folder' in item else "📄"
        print(f"    {item_type} {item['name']}")

        if item['name'].endswith('.xlsx') and item['name'] == FILE_NAME:
            return item['id']

    raise Exception(f"File '{FILE_NAME}' not found in {folder_path}")

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

def clean_sheet_name_for_table(sheet_name):
    """Convert sheet name to valid Convex table name"""
    # Remove spaces, special chars, convert to snake_case
    cleaned = sheet_name.lower()
    cleaned = cleaned.replace(' ', '_')
    cleaned = ''.join(c for c in cleaned if c.isalnum() or c == '_')
    return cleaned

def sync_sheet_to_convex(sheet_name, sheet_data):
    """Sync a single sheet to Convex as a table"""
    if not sheet_data or len(sheet_data) < 2:
        print(f"  ⚠️  Sheet '{sheet_name}' is empty or has no data rows")
        return

    # First row is headers
    headers = sheet_data[0]
    data_rows = sheet_data[1:]

    # Convert to table name
    table_name = clean_sheet_name_for_table(sheet_name)

    print(f"\n  📊 Syncing sheet: {sheet_name}")
    print(f"  📝 Table name: {table_name}")
    print(f"  📈 Columns: {len(headers)}")
    print(f"  📉 Rows: {len(data_rows)}")

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

    print(f"  ✅ Prepared {len(records)} records")

    # Send to Convex
    for record in records:
        try:
            client.mutation(f"{table_name}:add", record)
        except Exception as e:
            print(f"  ⚠️  Error adding record: {e}")

    print(f"  ✅ Synced {len(records)} records to Convex table '{table_name}'")

def main():
    print("=" * 60)
    print("Syncing ALL SharePoint Excel Sheets to Convex")
    print("=" * 60)

    # Get access token
    print("\n🔑 Getting access token...")
    access_token = get_access_token()
    print("✅ Got access token")

    # Get site ID
    print("\n🏢 Getting site ID...")
    site_id = get_site_id(access_token)
    print(f"✅ Got site ID: {site_id}")

    # Find the file
    print(f"\n🔍 Finding file: {FILE_NAME}")
    file_id = find_file(access_token, site_id)
    print(f"✅ Found file (ID: {file_id})")

    # Get all sheet names
    print("\n📋 Getting sheet names...")
    sheet_names = get_sheet_names(access_token, site_id, file_id)
    print(f"✅ Found {len(sheet_names)} sheets:")
    for i, name in enumerate(sheet_names, 1):
        print(f"   {i}. {name}")

    # Sync each sheet
    print("\n" + "=" * 60)
    print("Starting sync to Convex...")
    print("=" * 60)

    for sheet_name in sheet_names:
        try:
            # Get sheet data
            sheet_data = get_sheet_data(access_token, site_id, file_id, sheet_name)

            # Sync to Convex
            sync_sheet_to_convex(sheet_name, sheet_data)

        except Exception as e:
            print(f"\n  ❌ Error syncing sheet '{sheet_name}': {e}")

    print("\n" + "=" * 60)
    print("✅ Sync Complete!")
    print("=" * 60)
    print("\nAll sheets have been synced to Convex.")
    print("Each sheet is now a separate table in Convex.")

if __name__ == "__main__":
    main()
