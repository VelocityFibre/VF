#!/usr/bin/env python3
"""
WA Monitor Quick Fix Script
Automated fixes for common wa-monitor issues
"""

import sys
import subprocess
import time
from datetime import datetime

# Configuration
HOSTINGER_HOST = "72.60.17.245"
HOSTINGER_PASSWORD = "VeloF@2025@@"

def run_ssh_command(command, silent=False):
    """Execute command on Hostinger VPS"""
    ssh_cmd = f"sshpass -p '{HOSTINGER_PASSWORD}' ssh -o StrictHostKeyChecking=no root@{HOSTINGER_HOST} '{command}'"
    try:
        result = subprocess.run(ssh_cmd, shell=True, capture_output=True, text=True, timeout=30)
        if not silent:
            if result.returncode == 0:
                print(f"✅ Command executed successfully")
            else:
                print(f"❌ Command failed: {result.stderr}")
        return result.returncode == 0, result.stdout.strip()
    except Exception as e:
        print(f"❌ SSH error: {str(e)}")
        return False, ""

def fix_auth():
    """Fix Neon database authentication"""
    print("\n🔐 Fixing Database Authentication...")

    # Backup current config
    print("📁 Creating backup...")
    backup_cmd = f"cp /opt/wa-monitor/prod/.env /opt/wa-monitor/prod/.env.backup-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    run_ssh_command(backup_cmd)

    # Update password
    print("🔑 Updating Neon password...")
    update_cmd = "sed -i 's/npg_aRNLhZc1G2CD/npg_MIUZXrg1tEY0/g' /opt/wa-monitor/prod/.env"
    success, _ = run_ssh_command(update_cmd)

    if success:
        print("🔄 Restarting service...")
        run_ssh_command("systemctl restart wa-monitor-prod")
        time.sleep(5)

        # Verify fix
        print("🔍 Verifying fix...")
        success, output = run_ssh_command("grep 'password authentication failed' /opt/wa-monitor/prod/logs/*.log | tail -1", silent=True)

        if "password authentication failed" not in output:
            print("✅ Authentication fixed successfully!")
            return True
        else:
            print("⚠️ Authentication may still have issues. Check logs.")
            return False
    return False

def fix_schema():
    """Fix WhatsApp database schema"""
    print("\n🗄️ Fixing Database Schema...")

    # Check if column exists
    print("🔍 Checking schema...")
    check_cmd = "sqlite3 /opt/velo-test-monitor/services/whatsapp-bridge/store/messages.db '.schema messages' | grep deleted"
    success, output = run_ssh_command(check_cmd, silent=True)

    if "deleted" in output:
        print("✅ Schema already correct!")
        return True

    # Add missing column
    print("📝 Adding missing 'deleted' column...")
    fix_cmd = """sqlite3 /opt/velo-test-monitor/services/whatsapp-bridge/store/messages.db "ALTER TABLE messages ADD COLUMN deleted BOOLEAN DEFAULT FALSE;" """
    success, _ = run_ssh_command(fix_cmd)

    if success:
        print("🔄 Restarting service...")
        run_ssh_command("systemctl restart wa-monitor-prod")
        time.sleep(5)
        print("✅ Schema fixed successfully!")
        return True
    else:
        print("❌ Failed to fix schema")
        return False

def fix_messages():
    """Toggle automated messages on/off"""
    print("\n💬 Managing Automated Messages...")

    # Check current status
    check_cmd = "grep 'DISABLE_AUTO_MESSAGES' /opt/wa-monitor/prod/.env"
    success, output = run_ssh_command(check_cmd, silent=True)

    current_disabled = "true" in output.lower() if output else False

    print(f"Current status: Messages are {'DISABLED' if current_disabled else 'ENABLED'}")

    action = input("Choose action [disable/enable/cancel]: ").lower()

    if action == "disable":
        if current_disabled:
            print("✅ Messages already disabled!")
        else:
            print("🔕 Disabling automated messages...")
            run_ssh_command('echo "DISABLE_AUTO_MESSAGES=true" >> /opt/wa-monitor/prod/.env')
            run_ssh_command("systemctl restart wa-monitor-prod")
            print("✅ Automated messages disabled!")
            print("   No messages will be sent to WhatsApp groups")
        return True

    elif action == "enable":
        if not current_disabled:
            print("✅ Messages already enabled!")
        else:
            print("🔔 Enabling automated messages...")
            run_ssh_command("sed -i '/DISABLE_AUTO_MESSAGES/d' /opt/wa-monitor/prod/.env")
            run_ssh_command("systemctl restart wa-monitor-prod")
            print("✅ Automated messages enabled!")
            print("   ⚠️ Messages will be sent to WhatsApp groups")
        return True

    else:
        print("❌ Cancelled")
        return False

def fix_restart():
    """Safe restart of wa-monitor service"""
    print("\n🔄 Performing Safe Restart...")

    # Stop service
    print("⏹️ Stopping service...")
    run_ssh_command("systemctl stop wa-monitor-prod")
    time.sleep(2)

    # Clear cache
    print("🧹 Clearing Python cache...")
    run_ssh_command("find /opt/wa-monitor/prod -type d -name '__pycache__' -exec rm -rf {} + 2>/dev/null")

    # Clear large logs
    print("📝 Checking log size...")
    success, log_size = run_ssh_command("du -h /opt/wa-monitor/prod/logs/*.log | tail -1 | awk '{print $1}'", silent=True)
    if log_size and 'G' in log_size:
        print(f"   Log is large ({log_size}), rotating...")
        run_ssh_command("mv /opt/wa-monitor/prod/logs/wa-monitor-prod.log /opt/wa-monitor/prod/logs/wa-monitor-prod.log.old")
        run_ssh_command("touch /opt/wa-monitor/prod/logs/wa-monitor-prod.log")

    # Start service
    print("▶️ Starting service...")
    success, _ = run_ssh_command("systemctl start wa-monitor-prod")

    if success:
        time.sleep(5)
        # Check status
        success, status = run_ssh_command("systemctl is-active wa-monitor-prod", silent=True)
        if status == "active":
            print("✅ Service restarted successfully!")

            # Show recent activity
            print("\n📊 Recent activity:")
            run_ssh_command("grep 'Found drop' /opt/wa-monitor/prod/logs/*.log | tail -5")
            return True
        else:
            print(f"❌ Service failed to start properly. Status: {status}")
            return False
    return False

def fix_all():
    """Run all fixes in sequence"""
    print("\n🛠️ Running Complete Fix Sequence...")

    fixes = [
        ("Database Schema", fix_schema),
        ("Authentication", fix_auth),
        ("Service Restart", fix_restart)
    ]

    results = {}
    for name, fix_func in fixes:
        print(f"\n{'='*50}")
        print(f"Running: {name}")
        try:
            results[name] = fix_func()
        except Exception as e:
            print(f"❌ Error in {name}: {str(e)}")
            results[name] = False

    # Summary
    print(f"\n{'='*50}")
    print("📊 FIX SUMMARY:")
    for name, result in results.items():
        status = "✅ Success" if result else "❌ Failed"
        print(f"   {name}: {status}")

    return all(results.values())

def main():
    """Main entry point"""
    print("🔧 WA Monitor Quick Fix Tool")
    print("=" * 50)

    if len(sys.argv) < 2:
        print("\nUsage: python quick_fix.py [issue_type]")
        print("\nAvailable fixes:")
        print("  auth     - Fix database authentication")
        print("  schema   - Fix WhatsApp DB schema")
        print("  messages - Control automated messages")
        print("  restart  - Safe service restart")
        print("  all      - Run all fixes")
        print("\nExample: python quick_fix.py restart")
        sys.exit(1)

    issue_type = sys.argv[1].lower()

    fixes = {
        "auth": fix_auth,
        "schema": fix_schema,
        "messages": fix_messages,
        "restart": fix_restart,
        "all": fix_all
    }

    if issue_type in fixes:
        try:
            success = fixes[issue_type]()
            if success:
                print("\n✅ Fix completed successfully!")
                sys.exit(0)
            else:
                print("\n⚠️ Fix completed with warnings. Check logs.")
                sys.exit(1)
        except KeyboardInterrupt:
            print("\n❌ Fix cancelled by user")
            sys.exit(1)
        except Exception as e:
            print(f"\n❌ Fix failed: {str(e)}")
            sys.exit(1)
    else:
        print(f"❌ Unknown issue type: {issue_type}")
        print("Available: auth, schema, messages, restart, all")
        sys.exit(1)

if __name__ == "__main__":
    main()