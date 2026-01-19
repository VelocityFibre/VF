#!/usr/bin/env python3
"""
Connect to VF Server and get WhatsApp groups
"""

import subprocess
import json
import sys

def get_whatsapp_groups():
    """Get WhatsApp groups from the service on VF Server"""

    print("Connecting to VF Server WhatsApp service...")

    # SSH to VF Server and query the WhatsApp service
    cmd = [
        "sshpass", "-p", "2025",
        "ssh", "-o", "StrictHostKeyChecking=no",
        "-o", "PreferredAuthentications=password",
        "-o", "PubkeyAuthentication=no",
        "velo@100.96.203.105",
        "curl -s http://localhost:8081/groups"
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)

        if result.returncode != 0:
            print(f"Error connecting: {result.stderr}")
            return None

        # Parse the groups
        try:
            groups = json.loads(result.stdout)
            return groups
        except json.JSONDecodeError:
            # Maybe the endpoint is different, let's try /api/groups
            cmd[-1] = "curl -s http://localhost:8081/api/groups"
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)

            if result.returncode == 0:
                try:
                    groups = json.loads(result.stdout)
                    return groups
                except:
                    pass

            print("Could not parse groups response")
            print("Raw response:", result.stdout[:500])
            return None

    except subprocess.TimeoutExpired:
        print("Connection timeout")
        return None
    except Exception as e:
        print(f"Error: {e}")
        return None

def find_ff_group(groups):
    """Find the FF app group from the list"""

    if not groups:
        return None

    # Look for groups with "FF" in the name
    ff_groups = []
    for group in groups:
        if isinstance(group, dict):
            name = group.get('name', '').lower()
            if 'ff' in name or 'fibre' in name:
                ff_groups.append(group)

    return ff_groups

if __name__ == "__main__":
    # Get all groups
    groups = get_whatsapp_groups()

    if not groups:
        print("\n❌ Could not retrieve WhatsApp groups")
        print("\nTrying alternative: Check if service provides group list...")

        # Try to get service info
        cmd = [
            "sshpass", "-p", "2025",
            "ssh", "-o", "StrictHostKeyChecking=no",
            "-o", "PreferredAuthentications=password",
            "-o", "PubkeyAuthentication=no",
            "velo@100.96.203.105",
            "ls -la ~/whatsapp-sender/ 2>/dev/null | head -10"
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)
        print("WhatsApp sender directory:", result.stdout)
        sys.exit(1)

    print(f"\n✅ Found {len(groups)} total groups")

    # Find FF groups
    ff_groups = find_ff_group(groups)

    if ff_groups:
        print(f"\n📱 Found {len(ff_groups)} potential FF groups:")
        for group in ff_groups:
            print(f"  - Name: {group.get('name')}")
            print(f"    ID: {group.get('id')}")
            print(f"    Participants: {group.get('participants', [])}")
    else:
        print("\n⚠️ No groups with 'FF' found. Here are all groups:")
        for i, group in enumerate(groups[:10]):  # Show first 10
            if isinstance(group, dict):
                print(f"  {i+1}. {group.get('name', 'Unknown')}")
                print(f"      ID: {group.get('id', 'Unknown')}")