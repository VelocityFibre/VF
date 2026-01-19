#!/usr/bin/env python3
"""Sync documentation to Hostinger VPS production."""

import os
import sys
import subprocess
import json
from pathlib import Path

def sync_documentation():
    """Sync CLAUDE.md and other docs to Hostinger VPS."""

    HOST = "72.60.17.245"
    USER = "root"
    PASSWORD = os.environ.get("HOSTINGER_PASSWORD", "VeloF@2025@@")
    LOCAL_BASE = "/home/louisdup/Agents/claude"

    print("=" * 60)
    print("📚 SYNCING DOCUMENTATION TO HOSTINGER VPS")
    print("=" * 60)

    # First, find the app directory on Hostinger
    print("\n🔍 Finding FibreFlow directory on Hostinger...")
    ssh_command = [
        "sshpass", "-p", PASSWORD,
        "ssh", "-o", "StrictHostKeyChecking=no",
        f"{USER}@{HOST}",
        "pm2 info fibreflow-prod | grep 'exec cwd' | awk '{print $4}'"
    ]

    try:
        result = subprocess.run(ssh_command, capture_output=True, text=True, timeout=10)
        if result.returncode != 0 or not result.stdout.strip():
            # Fallback: try to find it
            ssh_command[-1] = "find /root /home -name 'package.json' -path '*/fibreflow/*' 2>/dev/null | head -1 | xargs dirname"
            result = subprocess.run(ssh_command, capture_output=True, text=True, timeout=10)

        app_dir = result.stdout.strip()
        if not app_dir:
            print("❌ Could not find FibreFlow directory on Hostinger")
            print("Please run: ssh root@72.60.17.245")
            print("Then: pm2 info fibreflow-prod")
            print("Look for 'exec cwd' path")
            return False

        print(f"✅ Found app directory: {app_dir}")

    except Exception as e:
        print(f"❌ Error finding app directory: {e}")
        return False

    # Files to sync
    files_to_sync = [
        "CLAUDE.md",
        "README.md",
        "docs/OPERATIONS_LOG.md",
        "docs/DECISION_LOG.md",
        ".env.example"
    ]

    print(f"\n📦 Syncing {len(files_to_sync)} files...")

    for file in files_to_sync:
        local_file = Path(LOCAL_BASE) / file
        if not local_file.exists():
            print(f"⚠️  Skipping {file} (not found locally)")
            continue

        remote_path = f"{app_dir}/{file}"
        remote_dir = "/".join(remote_path.split("/")[:-1])

        # Create directory if needed
        ssh_mkdir = [
            "sshpass", "-p", PASSWORD,
            "ssh", "-o", "StrictHostKeyChecking=no",
            f"{USER}@{HOST}",
            f"mkdir -p {remote_dir}"
        ]
        subprocess.run(ssh_mkdir, capture_output=True, timeout=10)

        # Copy file
        scp_command = [
            "sshpass", "-p", PASSWORD,
            "scp", "-o", "StrictHostKeyChecking=no",
            str(local_file),
            f"{USER}@{HOST}:{remote_path}"
        ]

        try:
            result = subprocess.run(scp_command, capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                print(f"✅ Synced: {file}")
            else:
                print(f"❌ Failed: {file} - {result.stderr}")
        except Exception as e:
            print(f"❌ Error syncing {file}: {e}")

    print("\n" + "=" * 60)
    print("📚 Documentation sync complete!")
    print("=" * 60)
    return True

if __name__ == "__main__":
    sync_documentation()