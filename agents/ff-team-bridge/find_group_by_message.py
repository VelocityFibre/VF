#!/usr/bin/env python3
"""
Find WhatsApp group ID by searching for a unique message
"""

import subprocess
import json
import time
import hashlib
from datetime import datetime

# Generate unique identifier
timestamp = datetime.now().strftime("%H%M%S")
unique_id = f"FFBRIDGE-{timestamp}-{hashlib.md5(timestamp.encode()).hexdigest()[:6]}"

print("=" * 70)
print("🔍 WHATSAPP GROUP FINDER BY MESSAGE")
print("=" * 70)

print(f"\n📱 STEP 1: Send this EXACT message to your FF app WhatsApp group:")
print("-" * 70)
print(f"\n    {unique_id}\n")
print("-" * 70)
print("Copy and paste it exactly as shown above!")
print("\n⏳ Waiting 30 seconds for you to send the message...")

# Give user time to send the message
for i in range(30, 0, -5):
    print(f"   {i} seconds remaining...", end="\r")
    time.sleep(5)

print("\n\n🔍 STEP 2: Searching for your message...")
print("-" * 70)

# Method 1: Check WhatsApp service logs
print("\n📂 Checking WhatsApp service logs...")
try:
    # Check recent WhatsApp sender logs
    cmd = [
        "sshpass", "-p", "VeloF@2025@@",
        "ssh", "-o", "StrictHostKeyChecking=no",
        "-o", "PreferredAuthentications=password",
        "root@72.60.17.245",
        f"grep -i '{unique_id}' /opt/whatsapp-sender/*.log 2>/dev/null | tail -5"
    ]

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
    if unique_id in result.stdout:
        print("✅ Found your message in logs!")
        print(result.stdout)
        # Try to extract group ID from context
        lines = result.stdout.split('\n')
        for line in lines:
            if '@g.us' in line:
                import re
                group_match = re.search(r'([0-9-]+@g\.us)', line)
                if group_match:
                    group_id = group_match.group(1)
                    print(f"\n🎉 FOUND YOUR GROUP ID: {group_id}")
                    print(f"\n📝 To configure the bridge, run:")
                    print(f"   sed -i 's/PASTE_YOUR_GROUP_ID_HERE/{group_id}/' /home/louisdup/Agents/claude/agents/ff-team-bridge/config.json")
    else:
        print("Message not found in sender logs")

except Exception as e:
    print(f"Could not check sender logs: {e}")

# Method 2: Check WhatsApp bridge monitoring logs
print("\n📂 Checking WhatsApp bridge logs...")
try:
    cmd = [
        "sshpass", "-p", "VeloF@2025@@",
        "ssh", "-o", "StrictHostKeyChecking=no",
        "-o", "PreferredAuthentications=password",
        "root@72.60.17.245",
        f"grep -r '{unique_id}' /opt/velo-test-monitor/ 2>/dev/null | head -5"
    ]

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
    if unique_id in result.stdout:
        print("✅ Found your message in bridge logs!")
        print(result.stdout[:500])
    else:
        print("Message not found in bridge logs")

except Exception as e:
    print(f"Could not check bridge logs: {e}")

# Method 3: Check database for recent messages
print("\n📂 Checking database for recent messages...")
try:
    # Check if we can query the WhatsApp database
    cmd = [
        "sshpass", "-p", "VeloF@2025@@",
        "ssh", "-o", "StrictHostKeyChecking=no",
        "-o", "PreferredAuthentications=password",
        "root@72.60.17.245",
        "cd /opt/whatsapp-sender && sqlite3 store/whatsapp.db '.tables' 2>/dev/null"
    ]

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
    if result.stdout:
        print(f"Database tables available: {result.stdout}")

        # Try to query for messages
        cmd = [
            "sshpass", "-p", "VeloF@2025@@",
            "ssh", "-o", "StrictHostKeyChecking=no",
            "-o", "PreferredAuthentications=password",
            "root@72.60.17.245",
            "cd /opt/whatsapp-sender && sqlite3 store/whatsapp.db 'SELECT * FROM whatsmeow_messages LIMIT 5' 2>/dev/null || echo 'No message table'"
        ]

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        print(f"Message query result: {result.stdout[:200]}")

except Exception as e:
    print(f"Could not check database: {e}")

# Method 4: Check VF Server for any monitoring
print("\n📂 Checking VF Server for monitoring...")
try:
    cmd = [
        "sshpass", "-p", "2025",
        "ssh", "-o", "StrictHostKeyChecking=no",
        "-o", "PreferredAuthentications=password",
        "velo@100.96.203.105",
        f"grep -i '{unique_id}' ~/whatsapp-sender/*.log 2>/dev/null || echo 'No logs with message'"
    ]

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
    if unique_id in result.stdout:
        print("✅ Found your message on VF Server!")
        print(result.stdout)
    else:
        print("Message not found on VF Server")

except Exception as e:
    print(f"Could not check VF Server: {e}")

print("\n" + "=" * 70)
print("💡 ALTERNATIVE APPROACHES:")
print("-" * 70)

print("\n1. Check WhatsApp Web manually:")
print("   - The URL when you click on the group contains the ID")
print("   - Format: https://web.whatsapp.com/#chat/XXXXX@g.us")

print("\n2. Use WhatsApp Business API (if available):")
print("   - Some business accounts can list all groups via API")

print("\n3. Export chat and check header:")
print("   - Export the FF app chat")
print("   - The exported file header sometimes contains the group ID")

print("\n4. Ask someone else in the group:")
print("   - If Hein can access WhatsApp Web, he can find the ID")

print("\n" + "=" * 70)