#!/usr/bin/env python3
"""Check VF server status and health"""
import subprocess
import json
import os
from dotenv import load_dotenv

load_dotenv()

# Server configuration from environment
HOST = os.getenv('VF_SERVER_HOST', '100.96.203.105')
USER = os.getenv('VF_SERVER_USER', 'louis')
PASSWORD = os.getenv('VF_SERVER_PASSWORD')

def check_server_status():
    """Check server health and running services"""
    result = {
        'server': HOST,
        'status': {},
        'services': {}
    }

    # Check if server is reachable
    ping_result = subprocess.run(
        ['ping', '-c', '1', '-W', '2', HOST],
        stdout=subprocess.PIPE, stderr=subprocess.DEVNULL
    )
    result['status']['reachable'] = ping_result.returncode == 0

    if not result['status']['reachable']:
        result['error'] = 'Server not reachable'
        return result

    # Check SSH connectivity
    ssh_command = f'echo "SSH OK"'

    if PASSWORD:
        ssh_result = subprocess.run(
            ['sshpass', '-p', PASSWORD, 'ssh', '-o', 'StrictHostKeyChecking=no',
             '-o', 'ConnectTimeout=5', f'{USER}@{HOST}', ssh_command],
            capture_output=True, text=True
        )
    else:
        ssh_result = subprocess.run(
            ['ssh', '-o', 'ConnectTimeout=5', f'{USER}@{HOST}', ssh_command],
            capture_output=True, text=True
        )

    result['status']['ssh'] = 'SSH OK' in ssh_result.stdout

    # Check web services
    services = {
        'portainer': f'http://{HOST}:9443',
        'grafana': f'http://{HOST}:3000',
        'ollama': f'http://{HOST}:11434',
        'qdrant': f'http://{HOST}:6333/dashboard',
        'fibreflow': f'http://{HOST}:80/health'
    }

    for service, url in services.items():
        try:
            check = subprocess.run(
                ['curl', '-s', '-o', '/dev/null', '-w', '%{http_code}',
                 '--connect-timeout', '2', url],
                capture_output=True, text=True
            )
            status_code = check.stdout.strip()
            result['services'][service] = {
                'url': url,
                'status': 'up' if status_code in ['200', '301', '302', '401'] else 'down',
                'code': status_code
            }
        except:
            result['services'][service] = {
                'url': url,
                'status': 'error'
            }

    # Get server uptime and load if SSH works
    if result['status']['ssh']:
        uptime_cmd = 'uptime'

        if PASSWORD:
            uptime_result = subprocess.run(
                ['sshpass', '-p', PASSWORD, 'ssh', '-o', 'StrictHostKeyChecking=no',
                 f'{USER}@{HOST}', uptime_cmd],
                capture_output=True, text=True
            )
        else:
            uptime_result = subprocess.run(
                ['ssh', f'{USER}@{HOST}', uptime_cmd],
                capture_output=True, text=True
            )

        if uptime_result.returncode == 0:
            result['status']['uptime'] = uptime_result.stdout.strip()

    return result

if __name__ == "__main__":
    result = check_server_status()
    print(json.dumps(result, indent=2))