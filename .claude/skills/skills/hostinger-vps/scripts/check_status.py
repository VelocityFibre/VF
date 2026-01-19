#!/usr/bin/env python3
"""Check FibreFlow production status on Hostinger VPS."""

import os
import sys
import subprocess
import json

def check_status():
    """Check the status of FibreFlow on Hostinger VPS."""

    HOST = "72.60.17.245"
    USER = "root"
    PASSWORD = os.environ.get("HOSTINGER_PASSWORD", "VeloF@2025@@")

    commands = [
        ("PM2 Status", "pm2 list"),
        ("FibreFlow Process", "pm2 info fibreflow-prod | grep -E 'status|uptime|restarts'"),
        ("Port 3005", "ss -tlnp | grep :3005"),
        ("HTTPS Response", "curl -s -o /dev/null -w '%{http_code}' https://app.fibreflow.app"),
        ("Disk Usage", "df -h /"),
        ("Memory Usage", "free -h | grep Mem"),
        ("App Directory", "pm2 info fibreflow-prod | grep 'exec cwd'")
    ]

    print("=" * 60)
    print("🔍 HOSTINGER VPS - FIBREFLOW PRODUCTION STATUS")
    print("=" * 60)
    print(f"Server: {HOST}")
    print("-" * 60)

    for label, command in commands:
        ssh_command = [
            "sshpass", "-p", PASSWORD,
            "ssh", "-o", "StrictHostKeyChecking=no",
            "-o", "ConnectTimeout=10",
            f"{USER}@{HOST}",
            command
        ]

        try:
            result = subprocess.run(
                ssh_command,
                capture_output=True,
                text=True,
                timeout=10
            )

            print(f"\n📊 {label}:")
            if result.returncode == 0:
                print(result.stdout.strip())
            else:
                print(f"❌ Error: {result.stderr.strip() if result.stderr else 'Command failed'}")
        except subprocess.TimeoutExpired:
            print(f"\n📊 {label}:")
            print("❌ Command timed out")
        except Exception as e:
            print(f"\n📊 {label}:")
            print(f"❌ Error: {str(e)}")

    print("\n" + "=" * 60)

if __name__ == "__main__":
    check_status()