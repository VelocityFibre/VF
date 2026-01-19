#!/usr/bin/env python3
"""
Find specific SharePoint file by searching for likely candidates
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
    url = f"https://graph.microsoft.com/v1.0/sites/blitzfibre.sharepoint.com:/sites/Velocity_Manco"
    headers = {'Authorization': f'Bearer {access_token}'}
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()['id']

def search_files(access_token, site_id, keywords):
    """Search for files"""
    search_url = f"https://graph.microsoft.com/v1.0/sites/{site_id}/drive/search(q='{keywords}')"
    headers = {'Authorization': f'Bearer {access_token}'}
    response = requests.get(search_url, headers=headers)
    if response.ok:
        return response.json().get('value', [])
    return []

def get_workbook_sheets(access_token, site_id, file_id):
    """Get all sheets from Excel workbook"""
    url = f"https://graph.microsoft.com/v1.0/sites/{site_id}/drive/items/{file_id}/workbook/worksheets"
    headers = {'Authorization': f'Bearer {access_token}'}
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json().get('value', [])

def main():
    print("=" * 60)
    print("Searching for Main SharePoint File")
    print("=" * 60)

    token = get_access_token()
    site_id = get_site_id(token)

    # Search for likely filenames
    search_terms = [
        "Velocity_Master",
        "Master_Scope",
        "VF_Project",
        "Tracker"
    ]

    print("\n🔍 Searching for Excel files...")
    all_files = {}

    for term in search_terms:
        files = search_files(token, site_id, term)
        for f in files:
            if f.get('name', '').endswith('.xlsx'):
                all_files[f['id']] = f

    # Show unique files
    print(f"\n✅ Found {len(all_files)} unique Excel files:\n")

    files_list = list(all_files.values())
    for i, f in enumerate(files_list[:20], 1):  # Show first 20
        print(f"{i:2d}. {f['name']}")
        print(f"    Size: {f.get('size', 0) / 1024:.1f} KB")
        print(f"    Modified: {f.get('lastModifiedDateTime', 'N/A')[:10]}")
        print()

    # Analyze each file to show sheets
    print("\n" + "=" * 60)
    print("Analyzing Main Files")
    print("=" * 60)

    important_files = [
        "Velocity_Master_Scope Tracker.xlsx",
        "VF_Project_Tracker_Lawley.xlsx",
        "VF_Project_Tracker_Mohadin.xlsx"
    ]

    for file in files_list:
        if file['name'] in important_files:
            print(f"\n📊 {file['name']}")
            print("-" * 60)
            try:
                sheets = get_workbook_sheets(token, site_id, file['id'])
                print(f"   Sheets ({len(sheets)}):")
                for sheet in sheets:
                    print(f"      - {sheet['name']}")
            except Exception as e:
                print(f"   ❌ Could not read sheets: {e}")

    # Save all file info
    with open('all_sharepoint_files.json', 'w') as f:
        json.dump(files_list, f, indent=2)

    print(f"\n💾 All files saved to: all_sharepoint_files.json")
    print("\n" + "=" * 60)

if __name__ == "__main__":
    main()
