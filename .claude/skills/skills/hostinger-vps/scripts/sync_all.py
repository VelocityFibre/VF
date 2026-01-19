#!/usr/bin/env python3
"""Complete sync script for Hostinger VPS - docs, code, and restart if needed."""

import os
import sys
import subprocess
import json
from pathlib import Path
from datetime import datetime

def sync_to_hostinger(include_code=False, restart=False):
    """Sync documentation (and optionally code) to Hostinger VPS."""

    HOST = "72.60.17.245"
    USER = "root"
    PASSWORD = os.environ.get("HOSTINGER_PASSWORD", "VeloF@2025@@")
    LOCAL_BASE = "/home/louisdup/Agents/claude"
    REMOTE_APP_DIR = "/var/www/fibreflow"

    print("=" * 60)
    print("🚀 HOSTINGER VPS SYNC")
    print("=" * 60)
    print(f"📅 Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🎯 Target: {HOST} ({REMOTE_APP_DIR})")
    print(f"📦 Mode: {'Full (Docs + Code)' if include_code else 'Documentation Only'}")
    print("-" * 60)

    # Documentation files to always sync
    doc_files = [
        "CLAUDE.md",
        "docs/OPERATIONS_LOG.md",
        "docs/DECISION_LOG.md",
        "docs/DOCUMENTATION_FRAMEWORK.md",
        ".env.example",
        "README.md"
    ]

    # Code directories to sync (if requested)
    code_dirs = [
        ".claude/skills",
        "api",
        "pages",
        "lib",
        "components",
        "styles",
        "public"
    ]

    success_count = 0
    fail_count = 0

    # Sync documentation
    print("\n📚 Syncing Documentation...")
    for file in doc_files:
        local_file = Path(LOCAL_BASE) / file
        if not local_file.exists():
            print(f"⚠️  Skipping {file} (not found)")
            continue

        remote_path = f"{REMOTE_APP_DIR}/{file}"
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
                print(f"  ✅ {file}")
                success_count += 1
            else:
                print(f"  ❌ {file}")
                fail_count += 1
        except Exception as e:
            print(f"  ❌ {file}: {str(e)}")
            fail_count += 1

    # Sync code if requested
    if include_code:
        print("\n🔧 Syncing Code Directories...")
        print("  ⚠️  WARNING: This will overwrite production code!")

        for dir_name in code_dirs:
            local_dir = Path(LOCAL_BASE) / dir_name
            if not local_dir.exists():
                print(f"  ⚠️  Skipping {dir_name} (not found)")
                continue

            # Use rsync for directories
            rsync_command = [
                "sshpass", "-p", PASSWORD,
                "rsync", "-avz",
                "--exclude=node_modules",
                "--exclude=.next",
                "--exclude=.git",
                "-e", "ssh -o StrictHostKeyChecking=no",
                f"{local_dir}/",
                f"{USER}@{HOST}:{REMOTE_APP_DIR}/{dir_name}/"
            ]

            try:
                result = subprocess.run(rsync_command, capture_output=True, text=True, timeout=120)
                if result.returncode == 0:
                    print(f"  ✅ {dir_name}/")
                    success_count += 1
                else:
                    print(f"  ❌ {dir_name}/: {result.stderr}")
                    fail_count += 1
            except Exception as e:
                print(f"  ❌ {dir_name}/: {str(e)}")
                fail_count += 1

    # Restart if requested
    if restart:
        print("\n♻️  Restarting FibreFlow...")
        restart_command = [
            "sshpass", "-p", PASSWORD,
            "ssh", "-o", "StrictHostKeyChecking=no",
            f"{USER}@{HOST}",
            "pm2 restart fibreflow-prod"
        ]

        try:
            result = subprocess.run(restart_command, capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                print("  ✅ FibreFlow restarted")
            else:
                print(f"  ❌ Restart failed: {result.stderr}")
        except Exception as e:
            print(f"  ❌ Restart error: {str(e)}")

    # Summary
    print("\n" + "=" * 60)
    print("📊 SYNC SUMMARY")
    print("-" * 60)
    print(f"✅ Success: {success_count} items")
    print(f"❌ Failed: {fail_count} items")
    print("=" * 60)

    return fail_count == 0

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Sync to Hostinger VPS")
    parser.add_argument("--code", action="store_true", help="Include code directories")
    parser.add_argument("--restart", action="store_true", help="Restart PM2 after sync")
    args = parser.parse_args()

    success = sync_to_hostinger(include_code=args.code, restart=args.restart)
    sys.exit(0 if success else 1)