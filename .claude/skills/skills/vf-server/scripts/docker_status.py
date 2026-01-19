#!/usr/bin/env python3
"""Check Docker containers status on VF server"""
import subprocess
import json
import os
from dotenv import load_dotenv

load_dotenv()

HOST = os.getenv('VF_SERVER_HOST', '100.96.203.105')
USER = os.getenv('VF_SERVER_USER', 'louis')
PASSWORD = os.getenv('VF_SERVER_PASSWORD')

def check_docker_status():
    """Get Docker container status"""
    result = {'containers': []}

    # Docker ps command with formatting
    docker_cmd = 'docker ps --format "{\\"name\\":\\"{{.Names}}\\",\\"status\\":\\"{{.Status}}\\",\\"ports\\":\\"{{.Ports}}\\",\\"image\\":\\"{{.Image}}\\"}"'

    try:
        if PASSWORD:
            ssh_result = subprocess.run(
                ['sshpass', '-p', PASSWORD, 'ssh', '-o', 'StrictHostKeyChecking=no',
                 f'{USER}@{HOST}', docker_cmd],
                capture_output=True, text=True, timeout=10
            )
        else:
            ssh_result = subprocess.run(
                ['ssh', f'{USER}@{HOST}', docker_cmd],
                capture_output=True, text=True, timeout=10
            )

        if ssh_result.returncode == 0 and ssh_result.stdout:
            # Parse each line as JSON
            for line in ssh_result.stdout.strip().split('\n'):
                if line:
                    try:
                        container = json.loads(line)
                        # Clean up status to be more readable
                        if 'Up' in container['status']:
                            container['running'] = True
                        else:
                            container['running'] = False
                        result['containers'].append(container)
                    except:
                        pass

            result['success'] = True
            result['total'] = len(result['containers'])
            result['running'] = sum(1 for c in result['containers'] if c.get('running'))
        else:
            result['success'] = False
            result['error'] = ssh_result.stderr or 'No containers found'

    except subprocess.TimeoutExpired:
        result['success'] = False
        result['error'] = 'Connection timeout'
    except Exception as e:
        result['success'] = False
        result['error'] = str(e)

    return result

if __name__ == "__main__":
    result = check_docker_status()
    print(json.dumps(result, indent=2))