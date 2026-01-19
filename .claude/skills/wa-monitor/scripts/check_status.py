#!/usr/bin/env python3
"""
WA Monitor Status Checker
Checks the health of all WA Monitor components
"""

import requests
import psycopg2
import json
import sys
from datetime import datetime

# Configuration
VF_SERVER = "100.96.203.105"
NEON_URL = "postgresql://neondb_owner:npg_aRNLhZc1G2CD@ep-dry-night-a9qyh4sj-pooler.gwc.azure.neon.tech/neondb?sslmode=require"

def check_nextjs():
    """Check Next.js API health"""
    try:
        response = requests.get(f"http://{VF_SERVER}:3005/api/foto-reviews/pending?limit=1", timeout=5)
        if response.status_code == 200:
            data = response.json()
            total = data.get('data', {}).get('total', 0)
            return True, f"Next.js API: ✅ Working ({total} pending reviews)"
        else:
            return False, f"Next.js API: ❌ Error {response.status_code}"
    except Exception as e:
        return False, f"Next.js API: ❌ Not responding - {str(e)}"

def check_vlm():
    """Check VLM service health"""
    try:
        response = requests.get(f"http://{VF_SERVER}:8100/health", timeout=5)
        if response.status_code == 200:
            return True, "VLM Service: ✅ Running (Qwen model on port 8100)"
        else:
            return False, f"VLM Service: ❌ Error {response.status_code}"
    except:
        return False, "VLM Service: ❌ Not responding"

def check_whatsapp():
    """Check WhatsApp service health"""
    try:
        response = requests.get(f"http://{VF_SERVER}:8081/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            connected = data.get('connected', False)
            phone = data.get('phone', 'Unknown')
            if connected:
                return True, f"WhatsApp: ✅ Connected (Phone: {phone})"
            else:
                return False, f"WhatsApp: ⚠️  Disconnected (Phone needs pairing: {phone})"
        else:
            return False, f"WhatsApp: ❌ Error {response.status_code}"
    except:
        return False, "WhatsApp: ❌ Not responding"

def check_database():
    """Check database connection and stats"""
    try:
        conn = psycopg2.connect(NEON_URL)
        cur = conn.cursor()

        # Get statistics
        cur.execute("""
            SELECT
                COUNT(*) as total,
                SUM(CASE WHEN feedback_sent = false THEN 1 ELSE 0 END) as pending,
                SUM(CASE WHEN feedback_sent = true THEN 1 ELSE 0 END) as sent,
                AVG(average_score) as avg_score
            FROM foto_ai_reviews
        """)

        stats = cur.fetchone()
        cur.close()
        conn.close()

        return True, f"Database: ✅ Connected (Total: {stats[0]}, Pending: {stats[1]}, Sent: {stats[2]}, Avg Score: {stats[3]:.1f}/10)"
    except Exception as e:
        return False, f"Database: ❌ Error - {str(e)}"

def main():
    """Run all health checks"""
    print("\n" + "="*60)
    print("WA MONITOR SYSTEM STATUS CHECK")
    print("="*60)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Server: {VF_SERVER}")
    print("-"*60)

    all_good = True

    # Run checks
    checks = [
        check_database(),
        check_nextjs(),
        check_vlm(),
        check_whatsapp()
    ]

    for success, message in checks:
        print(f"\n{message}")
        if not success:
            all_good = False

    # URLs
    print("\n" + "-"*60)
    print("Access URLs:")
    print(f"  Dashboard: http://{VF_SERVER}:3005/foto-reviews")
    print(f"  Pending API: http://{VF_SERVER}:3005/api/foto-reviews/pending")
    print(f"  VLM Health: http://{VF_SERVER}:8100/health")
    print(f"  WhatsApp Health: http://{VF_SERVER}:8081/health")

    print("\n" + "="*60)
    if all_good:
        print("✅ ALL SYSTEMS OPERATIONAL")
    else:
        print("⚠️  SOME SYSTEMS NEED ATTENTION")
    print("="*60 + "\n")

    return 0 if all_good else 1

if __name__ == "__main__":
    sys.exit(main())