#!/usr/bin/env python3
"""
Read SharePoint Excel file and list all sheets
Uses Microsoft Graph API with existing credentials
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
SITE_URL = os.getenv('SHAREPOINT_SITE_URL', 'https://blitzfibre.sharepoint.com/sites/Velocity_Manco')
FILE_URL = os.getenv('SHAREPOINT_FILE_URL', 'https://blitzfibre.sharepoint.com/:x:/s/Velocity_Manco/EYm7g0w6Y1dFgGB_m4YlBxgBeVJpoDXAYjdvK-ZfgHoOqA?e=PaRb5T')

def get_access_token():
    """Get Microsoft Graph API access token"""
    token_url = f"https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/token"

    data = {
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'scope': 'https://graph.microsoft.com/.default',
        'grant_type': 'client_credentials'
    }

    response = requests.post(token_url, data=data)
    response.raise_for_status()
    return response.json()['access_token']

def get_site_id(access_token):
    """Get SharePoint site ID"""
    # Extract site path from URL
    site_path = "/sites/Velocity_Manco"

    url = f"https://graph.microsoft.com/v1.0/sites/blitzfibre.sharepoint.com:{site_path}"
    headers = {'Authorization': f'Bearer {access_token}'}

    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()['id']

def list_files(access_token, site_id):
    """List files in SharePoint site"""
    url = f"https://graph.microsoft.com/v1.0/sites/{site_id}/drive/root/children"
    headers = {'Authorization': f'Bearer {access_token}'}

    response = requests.get(url, headers=headers)
    response.raise_for_status()

    files = response.json().get('value', [])
    print("\n📁 Files in SharePoint:")
    for file in files:
        if file.get('name', '').endswith('.xlsx'):
            print(f"   - {file['name']} (ID: {file['id']})")

    return files

def get_workbook_sheets(access_token, site_id, file_id):
    """Get all sheets from Excel workbook"""
    url = f"https://graph.microsoft.com/v1.0/sites/{site_id}/drive/items/{file_id}/workbook/worksheets"
    headers = {'Authorization': f'Bearer {access_token}'}

    response = requests.get(url, headers=headers)
    response.raise_for_status()

    sheets = response.json().get('value', [])
    return sheets

def main():
    print("=" * 60)
    print("SharePoint Excel File Analysis")
    print("=" * 60)

    try:
        # Step 1: Get access token
        print("\n🔐 Authenticating...")
        token = get_access_token()
        print("   ✅ Authenticated")

        # Step 2: Get site ID
        print("\n🌐 Getting site info...")
        site_id = get_site_id(token)
        print(f"   ✅ Site ID: {site_id}")

        # Step 3: List files
        print("\n📂 Listing files...")
        files = list_files(token, site_id)

        # Try to find the Excel file by searching
        excel_files = [f for f in files if f.get('name', '').endswith('.xlsx')]

        if not excel_files:
            print("\n⚠️  No Excel files found in root. Searching shared files...")
            # Try to search for shared files
            search_url = f"https://graph.microsoft.com/v1.0/sites/{site_id}/drive/search(q='.xlsx')"
            headers = {'Authorization': f'Bearer {token}'}
            response = requests.get(search_url, headers=headers)
            if response.ok:
                excel_files = response.json().get('value', [])
                print(f"\n📁 Found {len(excel_files)} Excel files:")
                for f in excel_files[:10]:  # Show first 10
                    print(f"   - {f.get('name')}")

        if excel_files:
            # Use the first Excel file or prompt user
            file_to_analyze = excel_files[0]
            file_id = file_to_analyze['id']
            file_name = file_to_analyze['name']

            print(f"\n📊 Analyzing: {file_name}")
            print("-" * 60)

            # Get sheets
            sheets = get_workbook_sheets(token, site_id, file_id)

            print(f"\n✅ Found {len(sheets)} sheets:")
            for i, sheet in enumerate(sheets, 1):
                print(f"\n{i}. {sheet['name']}")
                print(f"   ID: {sheet['id']}")
                print(f"   Visible: {sheet.get('visibility', 'N/A')}")
                print(f"   Position: {sheet.get('position', 'N/A')}")

            # Save sheet info to file
            with open('sharepoint_sheets.json', 'w') as f:
                json.dump(sheets, f, indent=2)

            print(f"\n💾 Sheet info saved to: sharepoint_sheets.json")

        else:
            print("\n❌ No Excel files found")

        print("\n" + "=" * 60)
        print("✅ Analysis Complete")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
