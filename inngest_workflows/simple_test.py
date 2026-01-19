#!/usr/bin/env python3
"""
SUPER SIMPLE INNGEST TEST
Just checks if a server is alive
"""

import requests
from datetime import datetime

def check_server():
    """Check if VF server is alive"""
    try:
        # Try to reach the VF server
        response = requests.get("http://100.96.203.105:3005", timeout=3)

        if response.status_code == 200:
            print(f"✅ Server is ALIVE at {datetime.now().strftime('%H:%M:%S')}")
            return "alive"
        else:
            print(f"⚠️ Server responded with code {response.status_code}")
            return "error"

    except Exception as e:
        print(f"❌ Server is DOWN - {e}")
        return "down"

# Test it directly
if __name__ == "__main__":
    print("\n🔍 Checking server...")
    result = check_server()
    print(f"\nResult: {result}")
    print("\n✨ That's what Inngest will run for you automatically!")