#!/usr/bin/env python3
"""Execute commands on Hostinger VPS via SSH."""

import os
import sys
import subprocess
import json

def execute_remote_command(command):
    """Execute a command on the Hostinger VPS."""

    HOST = "72.60.17.245"
    USER = "root"
    PASSWORD = os.environ.get("HOSTINGER_PASSWORD", "VeloF@2025@@")

    # Build the SSH command
    ssh_command = [
        "sshpass",
        "-p", PASSWORD,
        "ssh",
        "-o", "StrictHostKeyChecking=no",
        "-o", "ConnectTimeout=10",
        f"{USER}@{HOST}",
        command
    ]

    try:
        result = subprocess.run(
            ssh_command,
            capture_output=True,
            text=True,
            timeout=30
        )

        return {
            "success": result.returncode == 0,
            "output": result.stdout,
            "error": result.stderr if result.stderr else None,
            "command": command
        }
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "output": "",
            "error": "Command timed out after 30 seconds",
            "command": command
        }
    except Exception as e:
        return {
            "success": False,
            "output": "",
            "error": str(e),
            "command": command
        }

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({
            "success": False,
            "error": "No command provided"
        }))
        sys.exit(1)

    command = sys.argv[1]
    result = execute_remote_command(command)
    print(json.dumps(result, indent=2))