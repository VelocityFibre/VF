#!/usr/bin/env python3
"""
Helper to find WhatsApp group ID
"""

import subprocess
import json

print("=" * 60)
print("🔍 WHATSAPP GROUP ID FINDER")
print("=" * 60)

print("\n📱 METHOD 1: WhatsApp Web (Do this now!)")
print("-" * 40)
print("1. Open https://web.whatsapp.com")
print("2. Click on your 'FF app' group")
print("3. Look at the URL in your browser")
print("4. Copy the part that looks like: 120363XXXXXXXXXX@g.us")
print("\nExample URL:")
print("https://web.whatsapp.com/#chat/120363287462894729@g.us")
print("                               ^^^^^^^^^^^^^^^^^^^^^^")
print("                               This is your group ID")

print("\n📱 METHOD 2: Check Existing Sessions")
print("-" * 40)

# Try to check if WhatsApp sender has any group info stored
try:
    # Check for any stored group configurations
    cmd = [
        "sshpass", "-p", "VeloF@2025@@",
        "ssh", "-o", "StrictHostKeyChecking=no",
        "-o", "PreferredAuthentications=password",
        "root@72.60.17.245",
        "cd /opt/whatsapp-sender && sqlite3 store/whatsapp.db 'SELECT name FROM sqlite_master WHERE type=\"table\";' 2>/dev/null | head -5"
    ]

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
    if result.stdout:
        print("Found WhatsApp database tables:")
        print(result.stdout)
    else:
        print("No WhatsApp session data found")

except Exception as e:
    print(f"Could not check WhatsApp session: {e}")

print("\n📱 METHOD 3: From Mobile App")
print("-" * 40)
print("1. In WhatsApp mobile, go to your FF app group")
print("2. Tap group name at top")
print("3. Scroll down and tap 'Invite via link'")
print("4. The link contains the group ID")
print("   Example: https://chat.whatsapp.com/XXXXXXXXX")

print("\n" + "=" * 60)
print("📝 ONCE YOU HAVE THE GROUP ID:")
print("-" * 40)
print("1. Edit config.json:")
print("   nano /home/louisdup/Agents/claude/agents/ff-team-bridge/config.json")
print("\n2. Replace 'PASTE_YOUR_GROUP_ID_HERE' with your actual ID")
print("\n3. The bridge will then connect automatically!")
print("=" * 60)

# Show current config
print("\n📋 Current Configuration:")
try:
    with open("/home/louisdup/Agents/claude/agents/ff-team-bridge/config.json", 'r') as f:
        config = json.load(f)
        current_id = config.get('whatsapp_config', {}).get('group_id', 'NOT SET')
        print(f"Group ID: {current_id}")

        if current_id == "PASTE_YOUR_GROUP_ID_HERE":
            print("\n⚠️ Group ID not yet configured!")
            print("👆 Please follow the steps above to find your group ID")
        else:
            print("✅ Group ID is configured!")

except Exception as e:
    print(f"Could not read config: {e}")