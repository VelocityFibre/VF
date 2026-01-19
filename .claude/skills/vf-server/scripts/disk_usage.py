#!/usr/bin/env python3
"""Check disk usage on VF server"""
import subprocess
import json
import os
from dotenv import load_dotenv

load_dotenv()

HOST = os.getenv('VF_SERVER_HOST', '100.96.203.105')
USER = os.getenv('VF_SERVER_USER', 'louis')
PASSWORD = os.getenv('VF_SERVER_PASSWORD')

def check_disk_usage():
    """Get disk usage information"""
    result = {'filesystems': []}

    # df command for human-readable disk usage
    disk_cmd = "df -h | grep -E '^/dev/|^tmpfs' | awk '{print $1\"|\"$2\"|\"$3\"|\"$4\"|\"$5\"|\"$6}'"

    try:
        if PASSWORD:
            ssh_result = subprocess.run(
                ['sshpass', '-p', PASSWORD, 'ssh', '-o', 'StrictHostKeyChecking=no',
                 f'{USER}@{HOST}', disk_cmd],
                capture_output=True, text=True, timeout=10
            )
        else:
            ssh_result = subprocess.run(
                ['ssh', f'{USER}@{HOST}', disk_cmd],
                capture_output=True, text=True, timeout=10
            )

        if ssh_result.returncode == 0 and ssh_result.stdout:
            for line in ssh_result.stdout.strip().split('\n'):
                if line:
                    parts = line.split('|')
                    if len(parts) >= 6:
                        filesystem = {
                            'filesystem': parts[0],
                            'size': parts[1],
                            'used': parts[2],
                            'available': parts[3],
                            'use_percent': parts[4],
                            'mounted': parts[5]
                        }

                        # Flag if usage is high
                        try:
                            percent = int(parts[4].replace('%', ''))
                            if percent >= 90:
                                filesystem['status'] = 'critical'
                            elif percent >= 80:
                                filesystem['status'] = 'warning'
                            else:
                                filesystem['status'] = 'ok'
                        except:
                            filesystem['status'] = 'unknown'

                        result['filesystems'].append(filesystem)

            result['success'] = True

            # Get total memory usage too
            mem_cmd = "free -h | grep '^Mem:' | awk '{print $2\"|\"$3\"|\"$4}'"

            if PASSWORD:
                mem_result = subprocess.run(
                    ['sshpass', '-p', PASSWORD, 'ssh', '-o', 'StrictHostKeyChecking=no',
                     f'{USER}@{HOST}', mem_cmd],
                    capture_output=True, text=True, timeout=5
                )
            else:
                mem_result = subprocess.run(
                    ['ssh', f'{USER}@{HOST}', mem_cmd],
                    capture_output=True, text=True, timeout=5
                )

            if mem_result.returncode == 0 and mem_result.stdout:
                parts = mem_result.stdout.strip().split('|')
                if len(parts) >= 3:
                    result['memory'] = {
                        'total': parts[0],
                        'used': parts[1],
                        'free': parts[2]
                    }
        else:
            result['success'] = False
            result['error'] = ssh_result.stderr or 'Could not get disk usage'

    except subprocess.TimeoutExpired:
        result['success'] = False
        result['error'] = 'Connection timeout'
    except Exception as e:
        result['success'] = False
        result['error'] = str(e)

    return result

if __name__ == "__main__":
    result = check_disk_usage()
    print(json.dumps(result, indent=2))