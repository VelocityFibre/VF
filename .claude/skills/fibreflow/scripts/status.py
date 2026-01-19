#!/usr/bin/env python3
"""
Simple status check for FibreFlow - tells you what's broken
"""

import requests
import sys
from datetime import datetime

def check_status():
    """Check if FibreFlow services are up"""

    print(f"FibreFlow Status Check - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("-" * 50)

    all_good = True

    # Check production app
    print("Production (app.fibreflow.app)...", end=" ")
    try:
        r = requests.get("https://app.fibreflow.app", timeout=5)
        if r.status_code == 200:
            print("✅ UP")
        else:
            print(f"⚠️ Status {r.status_code}")
            all_good = False
    except Exception as e:
        print(f"❌ DOWN - {e}")
        all_good = False

    # Check staging (VF)
    print("Staging (vf.fibreflow.app)...", end=" ")
    try:
        r = requests.get("https://vf.fibreflow.app", timeout=5)
        if r.status_code == 200:
            print("✅ UP")
        else:
            print(f"⚠️ Status {r.status_code}")
    except:
        print("❌ DOWN")

    # Check storage API (replaced Firebase)
    print("Storage API (port 8091)...", end=" ")
    try:
        r = requests.get("http://100.96.203.105:8091/health", timeout=5)
        if r.status_code == 200:
            print("✅ UP")
        else:
            print(f"⚠️ Status {r.status_code}")
            all_good = False
    except:
        print("❌ DOWN")
        all_good = False

    # Check WhatsApp sender
    print("WhatsApp Sender (port 8081)...", end=" ")
    try:
        r = requests.get("http://100.96.203.105:8081/", timeout=5)
        print("✅ UP")
    except:
        print("⚠️ May be down")

    print("-" * 50)

    if all_good:
        print("✅ All critical services operational")
        return 0
    else:
        print("⚠️ Some services need attention")
        return 1

if __name__ == "__main__":
    sys.exit(check_status())