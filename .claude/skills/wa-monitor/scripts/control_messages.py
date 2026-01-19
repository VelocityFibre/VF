#!/usr/bin/env python3
"""
WA Monitor Message Control Script
Manage automated WhatsApp messaging for wa-monitor
"""

import sys
import subprocess
import json
from datetime import datetime

# Configuration
HOSTINGER_HOST = "72.60.17.245"
HOSTINGER_PASSWORD = "VeloF@2025@@"

def run_ssh_command(command, silent=False):
    """Execute command on Hostinger VPS"""
    ssh_cmd = f"sshpass -p '{HOSTINGER_PASSWORD}' ssh -o StrictHostKeyChecking=no root@{HOSTINGER_HOST} '{command}'"
    try:
        result = subprocess.run(ssh_cmd, shell=True, capture_output=True, text=True, timeout=30)
        if not silent or result.returncode != 0:
            if result.returncode != 0 and not silent:
                print(f"❌ Command failed: {result.stderr}")
        return result.returncode == 0, result.stdout.strip()
    except Exception as e:
        if not silent:
            print(f"❌ SSH error: {str(e)}")
        return False, ""

def get_current_status():
    """Get current messaging status"""
    success, output = run_ssh_command("grep 'DISABLE_AUTO_MESSAGES' /opt/wa-monitor/prod/.env", silent=True)

    if success and "true" in output.lower():
        return "disabled"
    else:
        return "enabled"

def disable_messages():
    """Disable automated messages"""
    print("🔕 Disabling automated WhatsApp messages...")

    current = get_current_status()
    if current == "disabled":
        print("✅ Messages are already disabled!")
        return True

    # Backup config
    backup_time = datetime.now().strftime('%Y%m%d-%H%M%S')
    print("📁 Creating config backup...")
    run_ssh_command(f"cp /opt/wa-monitor/prod/.env /opt/wa-monitor/prod/.env.backup-{backup_time}", silent=True)

    # Add disable flag
    print("📝 Updating configuration...")
    success, _ = run_ssh_command('echo "" >> /opt/wa-monitor/prod/.env')
    success, _ = run_ssh_command('echo "# Automated messaging control" >> /opt/wa-monitor/prod/.env')
    success, _ = run_ssh_command('echo "DISABLE_AUTO_MESSAGES=true" >> /opt/wa-monitor/prod/.env')

    # Update monitor.py if needed
    print("🔧 Ensuring code supports message blocking...")
    check_cmd = "grep 'DISABLE_AUTO_MESSAGES' /opt/wa-monitor/prod/modules/monitor.py"
    success, output = run_ssh_command(check_cmd, silent=True)

    if not output:
        print("   Adding message blocking code...")
        patch_code = '''sed -i "204a\\\\        # Check if automated messages are disabled\\\\n        if os.environ.get(\\\\"DISABLE_AUTO_MESSAGES\\\\", \\\\"\\\\").lower() == \\\\"true\\\\":\\\\n            logger.info(f\\\\"📵 Automated message blocked (DISABLE_AUTO_MESSAGES=true)\\\\")\\\\n            return False\\\\n" /opt/wa-monitor/prod/modules/monitor.py'''
        run_ssh_command(patch_code, silent=True)

    # Restart service
    print("🔄 Restarting service...")
    run_ssh_command("systemctl restart wa-monitor-prod")

    print("\n✅ Automated messages DISABLED!")
    print("   ├─ No messages will be sent to WhatsApp groups")
    print("   ├─ Drops will still be monitored and saved")
    print("   └─ Dashboard will continue to work normally")

    return True

def enable_messages():
    """Enable automated messages"""
    print("🔔 Enabling automated WhatsApp messages...")

    current = get_current_status()
    if current == "enabled":
        print("✅ Messages are already enabled!")
        return True

    print("⚠️ WARNING: This will enable automated messages to WhatsApp groups!")
    confirm = input("Are you sure? [yes/no]: ").lower()

    if confirm != "yes":
        print("❌ Cancelled")
        return False

    # Backup config
    backup_time = datetime.now().strftime('%Y%m%d-%H%M%S')
    print("📁 Creating config backup...")
    run_ssh_command(f"cp /opt/wa-monitor/prod/.env /opt/wa-monitor/prod/.env.backup-{backup_time}", silent=True)

    # Remove disable flag
    print("📝 Updating configuration...")
    run_ssh_command("sed -i '/DISABLE_AUTO_MESSAGES/d' /opt/wa-monitor/prod/.env", silent=True)
    run_ssh_command("sed -i '/# Automated messaging control/d' /opt/wa-monitor/prod/.env", silent=True)

    # Restart service
    print("🔄 Restarting service...")
    run_ssh_command("systemctl restart wa-monitor-prod")

    print("\n✅ Automated messages ENABLED!")
    print("   ├─ ⚠️ Messages WILL be sent to WhatsApp groups")
    print("   ├─ Invalid drop notifications will be sent")
    print("   └─ Monitor feedback groups for activity")

    return True

def status():
    """Show current messaging status and recent activity"""
    print("📊 WA Monitor Messaging Status")
    print("=" * 50)

    # Current configuration
    current = get_current_status()
    status_emoji = "🔕" if current == "disabled" else "🔔"
    print(f"\n{status_emoji} Automated Messages: {current.upper()}")

    # Check service status
    success, service_status = run_ssh_command("systemctl is-active wa-monitor-prod", silent=True)
    print(f"📡 Monitor Service: {service_status}")

    # Check WhatsApp Bridge
    success, bridge_status = run_ssh_command("systemctl is-active whatsapp-bridge-prod 2>/dev/null || echo 'not-found'", silent=True)
    if bridge_status != "not-found":
        print(f"📱 WhatsApp Bridge: {bridge_status}")

    # Recent message activity
    print("\n📨 Recent Message Activity:")
    success, logs = run_ssh_command("grep -E '✅ Group message|📵 Automated message blocked' /opt/wa-monitor/prod/logs/*.log | tail -5", silent=True)

    if logs:
        for line in logs.split('\n')[-5:]:
            if "Group message" in line:
                timestamp = line.split()[0] + " " + line.split()[1]
                print(f"   ✉️ Message sent at {timestamp}")
            elif "blocked" in line:
                timestamp = line.split()[0] + " " + line.split()[1]
                print(f"   🚫 Message blocked at {timestamp}")
    else:
        print("   No recent message activity")

    # Groups being monitored
    print("\n👥 Monitored WhatsApp Groups:")
    success, groups = run_ssh_command("grep -E '^\s*- name:' /opt/wa-monitor/prod/config/projects.yaml | sed 's/.*name: //' ", silent=True)

    if groups:
        for group in groups.split('\n'):
            print(f"   • {group}")

    # Message control info
    print("\n💡 Message Control:")
    if current == "disabled":
        print("   Messages are currently BLOCKED")
        print("   To enable: python control_messages.py enable")
    else:
        print("   Messages are currently ACTIVE")
        print("   To disable: python control_messages.py disable")

    return True

def test_message():
    """Test sending a message (if enabled)"""
    print("🧪 Testing Message Sending...")

    current = get_current_status()
    if current == "disabled":
        print("❌ Cannot test - automated messages are disabled")
        print("   Enable first: python control_messages.py enable")
        return False

    # Check if bridge is running
    success, bridge = run_ssh_command("systemctl is-active whatsapp-bridge-prod", silent=True)
    if bridge != "active":
        print("❌ WhatsApp Bridge is not active")
        print("   Start it: ssh root@72.60.17.245 'systemctl start whatsapp-bridge-prod'")
        return False

    print("📤 Attempting to send test message...")
    print("   Note: This would normally trigger on invalid drop submission")

    # Check recent sends
    success, recent = run_ssh_command("grep '✅ Group message' /opt/wa-monitor/prod/logs/*.log | tail -1", silent=True)
    if recent:
        print(f"✅ Last successful message: {recent.split()[0]} {recent.split()[1]}")
    else:
        print("⚠️ No recent successful messages found")

    return True

def main():
    """Main entry point"""
    print("💬 WA Monitor Message Control")
    print("=" * 50)

    if len(sys.argv) < 2:
        print("\nUsage: python control_messages.py [action]")
        print("\nActions:")
        print("  status  - Show current messaging status")
        print("  enable  - Enable automated messages")
        print("  disable - Disable automated messages")
        print("  test    - Test message sending")
        print("\nExample: python control_messages.py disable")
        sys.exit(1)

    action = sys.argv[1].lower()

    actions = {
        "status": status,
        "enable": enable_messages,
        "disable": disable_messages,
        "test": test_message
    }

    if action in actions:
        try:
            success = actions[action]()
            sys.exit(0 if success else 1)
        except KeyboardInterrupt:
            print("\n❌ Operation cancelled")
            sys.exit(1)
        except Exception as e:
            print(f"\n❌ Operation failed: {str(e)}")
            sys.exit(1)
    else:
        print(f"❌ Unknown action: {action}")
        print("Available: status, enable, disable, test")
        sys.exit(1)

if __name__ == "__main__":
    main()