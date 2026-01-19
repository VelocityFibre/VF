#!/usr/bin/env python3
"""
WA Monitor Health Check Script
Comprehensive health status of the WhatsApp monitoring system
"""

import json
import subprocess
import sys
from datetime import datetime
import psycopg2
import requests

# Configuration
HOSTINGER_HOST = "72.60.17.245"
HOSTINGER_PASSWORD = "VeloF@2025@@"
NEON_HOST = "ep-dry-night-a9qyh4sj-pooler.gwc.azure.neon.tech"
NEON_DB = "neondb"
NEON_USER = "neondb_owner"
NEON_PASSWORD = "npg_MIUZXrg1tEY0"
API_BASE = "https://app.fibreflow.app"

def run_ssh_command(command):
    """Execute command on Hostinger VPS"""
    ssh_cmd = f"sshpass -p '{HOSTINGER_PASSWORD}' ssh -o StrictHostKeyChecking=no root@{HOSTINGER_HOST} '{command}'"
    try:
        result = subprocess.run(ssh_cmd, shell=True, capture_output=True, text=True, timeout=10)
        return result.stdout.strip() if result.returncode == 0 else None
    except Exception as e:
        return None

def check_service_status():
    """Check wa-monitor-prod service status"""
    status = run_ssh_command("systemctl is-active wa-monitor-prod")
    uptime = run_ssh_command("systemctl status wa-monitor-prod | grep 'Active:' | sed 's/.*since //; s/;.*//'")
    memory = run_ssh_command("systemctl status wa-monitor-prod | grep 'Memory:' | awk '{print $2}'")

    return {
        "status": status or "unknown",
        "uptime": uptime or "unknown",
        "memory": memory or "unknown",
        "healthy": status == "active"
    }

def check_database():
    """Check database connectivity and recent drops"""
    try:
        conn = psycopg2.connect(
            host=NEON_HOST,
            database=NEON_DB,
            user=NEON_USER,
            password=NEON_PASSWORD,
            sslmode='require'
        )
        cur = conn.cursor()

        # Count today's drops
        cur.execute("""
            SELECT project, COUNT(*) as count
            FROM qa_photo_reviews
            WHERE DATE(created_at) = CURRENT_DATE
            GROUP BY project
        """)
        today_drops = dict(cur.fetchall())

        # Get total drops
        cur.execute("SELECT COUNT(*) FROM qa_photo_reviews")
        total_drops = cur.fetchone()[0]

        # Get latest drop time
        cur.execute("SELECT MAX(created_at) FROM qa_photo_reviews")
        latest_drop = cur.fetchone()[0]

        cur.close()
        conn.close()

        return {
            "connected": True,
            "total_drops": total_drops,
            "today_drops": today_drops,
            "latest_drop": latest_drop.isoformat() if latest_drop else None,
            "healthy": True
        }
    except Exception as e:
        return {
            "connected": False,
            "error": str(e),
            "healthy": False
        }

def check_recent_errors():
    """Check for recent errors in logs"""
    errors = run_ssh_command(
        "grep 'ERROR' /opt/wa-monitor/prod/logs/*.log | tail -5 | wc -l"
    )
    last_error = run_ssh_command(
        "grep 'ERROR' /opt/wa-monitor/prod/logs/*.log | tail -1 | cut -d' ' -f1-3"
    )

    return {
        "error_count": int(errors) if errors else 0,
        "last_error_time": last_error or "No recent errors",
        "healthy": int(errors) < 10 if errors else True
    }

def check_whatsapp_bridge():
    """Check WhatsApp Bridge service status"""
    status = run_ssh_command("systemctl is-active whatsapp-bridge-prod 2>/dev/null || echo 'not-found'")
    port_8080 = run_ssh_command("netstat -an | grep ':8080.*LISTEN' | wc -l")

    return {
        "status": status or "unknown",
        "port_8080_listening": int(port_8080) > 0 if port_8080 else False,
        "healthy": status == "active" or int(port_8080) > 0 if port_8080 else False
    }

def check_api_endpoints():
    """Check API endpoint availability"""
    endpoints_status = {}
    endpoints = [
        "/api/wa-monitor-health",
        "/api/wa-monitor-drops?limit=1",
        "/api/wa-monitor-daily-drops"
    ]

    for endpoint in endpoints:
        try:
            response = requests.get(f"{API_BASE}{endpoint}", timeout=5)
            endpoints_status[endpoint] = {
                "status_code": response.status_code,
                "healthy": response.status_code == 200
            }
        except Exception as e:
            endpoints_status[endpoint] = {
                "status_code": 0,
                "healthy": False,
                "error": str(e)
            }

    return endpoints_status

def check_messaging_status():
    """Check if automated messaging is enabled"""
    config = run_ssh_command("grep 'DISABLE_AUTO_MESSAGES' /opt/wa-monitor/prod/.env")

    if config and "true" in config.lower():
        return {
            "automated_messages": "disabled",
            "config": "DISABLE_AUTO_MESSAGES=true",
            "info": "Automated WhatsApp messages are disabled"
        }
    else:
        return {
            "automated_messages": "enabled",
            "config": "DISABLE_AUTO_MESSAGES not set or false",
            "warning": "Automated messages will be sent to WhatsApp groups"
        }

def generate_report():
    """Generate comprehensive health report"""
    print("🔍 WA Monitor Health Check")
    print("=" * 50)

    # Service Status
    print("\n📊 SERVICE STATUS")
    service = check_service_status()
    status_emoji = "✅" if service["healthy"] else "❌"
    print(f"{status_emoji} Service: {service['status']}")
    print(f"   Uptime: {service['uptime']}")
    print(f"   Memory: {service['memory']}")

    # Database Status
    print("\n🗄️ DATABASE STATUS")
    db = check_database()
    db_emoji = "✅" if db["healthy"] else "❌"
    if db["connected"]:
        print(f"{db_emoji} Connected to Neon PostgreSQL")
        print(f"   Total drops: {db['total_drops']}")
        print(f"   Today's drops: {json.dumps(db['today_drops'])}")
        print(f"   Latest drop: {db['latest_drop']}")
    else:
        print(f"{db_emoji} Database connection failed")
        print(f"   Error: {db.get('error', 'Unknown error')}")

    # WhatsApp Bridge
    print("\n📱 WHATSAPP BRIDGE")
    bridge = check_whatsapp_bridge()
    bridge_emoji = "✅" if bridge["healthy"] else "❌"
    print(f"{bridge_emoji} Bridge: {bridge['status']}")
    print(f"   Port 8080: {'Listening' if bridge['port_8080_listening'] else 'Not listening'}")

    # Recent Errors
    print("\n⚠️ RECENT ERRORS")
    errors = check_recent_errors()
    error_emoji = "✅" if errors["healthy"] else "❌"
    print(f"{error_emoji} Errors in last check: {errors['error_count']}")
    print(f"   Last error: {errors['last_error_time']}")

    # Messaging Status
    print("\n💬 MESSAGING CONFIG")
    messaging = check_messaging_status()
    print(f"   Status: {messaging['automated_messages']}")
    print(f"   {messaging.get('info', messaging.get('warning', ''))}")

    # API Endpoints
    print("\n🌐 API ENDPOINTS")
    endpoints = check_api_endpoints()
    for endpoint, status in endpoints.items():
        endpoint_emoji = "✅" if status["healthy"] else "❌"
        print(f"{endpoint_emoji} {endpoint}: {status['status_code']}")

    # Overall Health
    print("\n" + "=" * 50)
    overall_healthy = (
        service["healthy"] and
        db["healthy"] and
        errors["healthy"] and
        any(ep["healthy"] for ep in endpoints.values())
    )

    if overall_healthy:
        print("✅ OVERALL STATUS: HEALTHY")
    else:
        print("❌ OVERALL STATUS: ISSUES DETECTED")
        print("\nRecommended actions:")
        if not service["healthy"]:
            print("- Restart service: ssh root@72.60.17.245 'systemctl restart wa-monitor-prod'")
        if not db["healthy"]:
            print("- Check database credentials in /opt/wa-monitor/prod/.env")
        if not errors["healthy"]:
            print("- Review error logs: ssh root@72.60.17.245 'tail -100 /opt/wa-monitor/prod/logs/*.log'")

    print("\n📝 Full troubleshooting guide: .claude/skills/wa-monitor/TROUBLESHOOTING.md")

if __name__ == "__main__":
    try:
        generate_report()
    except Exception as e:
        print(f"❌ Health check failed: {str(e)}")
        sys.exit(1)