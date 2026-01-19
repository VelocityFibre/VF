#!/usr/bin/env python3
"""Execute command on VF server"""
import subprocess
import json
import sys
import os
from dotenv import load_dotenv

load_dotenv()

HOST = os.getenv('VF_SERVER_HOST', '100.96.203.105')
USER = os.getenv('VF_SERVER_USER', 'louis')
PASSWORD = os.getenv('VF_SERVER_PASSWORD')

def execute_command(command):
    """Execute a command on the VF server"""
    result = {}

    try:
        if PASSWORD:
            ssh_result = subprocess.run(
                ['sshpass', '-p', PASSWORD, 'ssh', '-o', 'StrictHostKeyChecking=no',
                 f'{USER}@{HOST}', command],
                capture_output=True, text=True, timeout=30
            )
        else:
            ssh_result = subprocess.run(
                ['ssh', f'{USER}@{HOST}', command],
                capture_output=True, text=True, timeout=30
            )

        result['success'] = ssh_result.returncode == 0
        result['output'] = ssh_result.stdout
        result['error'] = ssh_result.stderr if ssh_result.stderr else None
        result['command'] = command

    except subprocess.TimeoutExpired:
        result['success'] = False
        result['error'] = 'Command timed out after 30 seconds'
    except Exception as e:
        result['success'] = False
        result['error'] = str(e)

    return result

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({'error': 'Please provide a command to execute'}))
        sys.exit(1)

    command = ' '.join(sys.argv[1:])
    result = execute_command(command)
    print(json.dumps(result, indent=2))