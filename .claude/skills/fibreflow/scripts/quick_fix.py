#!/usr/bin/env python3
"""
Quick fixes for common FibreFlow issues
Updated 2026-01-14: Now uses louis account with limited sudo (safer)
"""

import os
import sys
import subprocess

def print_fix(number, description):
    print(f"[{number}] {description}")

def main():
    print("FibreFlow Quick Fixes")
    print("-" * 30)
    print_fix(1, "Restart production app")
    print_fix(2, "Restart staging app")
    print_fix(3, "Check logs")
    print_fix(4, "Clear Cloudflare cache")
    print_fix(5, "Restart storage API")
    print("-" * 30)

    choice = input("Select fix (1-5) or q to quit: ").strip()

    if choice == "1":
        print("Restarting production...")
        # Using louis account with sudo (requires password)
        os.system("ssh -i ~/.ssh/vf_server_key louis@100.96.203.105 'cd ~/fibreflow && echo \"VeloBoss@2026\" | sudo -S -u velo npx pm2 restart fibreflow'")
        print("✅ Done")

    elif choice == "2":
        print("Restarting staging...")
        # Using louis account with sudo
        os.system("ssh -i ~/.ssh/vf_server_key louis@100.96.203.105 'cd ~/fibreflow-louis && echo \"VeloBoss@2026\" | sudo -S -u velo npx pm2 restart fibreflow-louis'")
        print("✅ Done")

    elif choice == "3":
        print("Recent logs:")
        # Reading logs doesn't need admin
        os.system("ssh -i ~/.ssh/vf_server_key louis@100.96.203.105 'cd ~/fibreflow && npx pm2 logs fibreflow --lines 20 --nostream'")

    elif choice == "4":
        print("To clear Cloudflare cache:")
        print("1. Go to https://dash.cloudflare.com")
        print("2. Select fibreflow.app domain")
        print("3. Caching → Configuration → Purge Everything")
        print("(Automated API coming soon)")

    elif choice == "5":
        print("Restarting storage API...")
        # Using louis with password for restart
        os.system("ssh -i ~/.ssh/vf_server_key louis@100.96.203.105 'echo \"VeloBoss@2026\" | sudo -S systemctl restart storage-api'")
        print("✅ Done")

    elif choice.lower() == "q":
        sys.exit(0)
    else:
        print("Invalid choice")

if __name__ == "__main__":
    main()