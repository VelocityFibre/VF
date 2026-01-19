#!/usr/bin/env python3
"""Quick test of QFieldCloud SSH connection"""

import os
import subprocess
from dotenv import load_dotenv

load_dotenv()

vps_host = os.getenv('QFIELDCLOUD_VPS_HOST', '72.61.166.168')
vps_user = os.getenv('QFIELDCLOUD_VPS_USER', 'root')
ssh_key = os.path.expanduser('~/.ssh/qfield_vps')

print(f"Testing SSH to {vps_user}@{vps_host}...")
print(f"Using SSH key: {ssh_key}")
print(f"Key exists: {os.path.exists(ssh_key)}")

# Build SSH command
ssh_cmd = [
    'ssh',
    '-i', ssh_key,
    '-o', 'StrictHostKeyChecking=no',
    '-o', 'ConnectTimeout=10',
    f'{vps_user}@{vps_host}',
    'cd /opt/qfieldcloud && docker compose ps --format json | head -2'
]

print(f"\nExecuting: {' '.join(ssh_cmd)}\n")

try:
    result = subprocess.run(
        ssh_cmd,
        capture_output=True,
        text=True,
        timeout=15
    )

    print(f"Return code: {result.returncode}")
    print(f"\nStdout:\n{result.stdout}")

    if result.stderr:
        print(f"\nStderr:\n{result.stderr}")

except subprocess.TimeoutExpired:
    print("❌ Command timed out after 15 seconds")
except Exception as e:
    print(f"❌ Error: {e}")
