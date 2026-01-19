#!/usr/bin/env python3
"""Get VF server connection commands"""
import json
import os
from dotenv import load_dotenv

load_dotenv()

HOST = os.getenv('VF_SERVER_HOST', '100.96.203.105')
USER = os.getenv('VF_SERVER_USER', 'louis')

def get_connection_info():
    """Get connection commands (without exposing password)"""
    result = {
        'primary': {
            'method': 'Tailscale',
            'command': f'ssh {USER}@{HOST}',
            'host': HOST,
            'user': USER
        },
        'alternatives': [
            {
                'method': 'Tailscale (hostname)',
                'command': f'ssh {USER}@velo-server'
            },
            {
                'method': 'Local Network',
                'command': f'ssh {USER}@192.168.1.150'
            }
        ],
        'services': {
            'portainer': f'http://{HOST}:9443',
            'grafana': f'http://{HOST}:3000',
            'ollama': f'http://{HOST}:11434',
            'qdrant': f'http://{HOST}:6333/dashboard',
            'fibreflow_api': f'http://{HOST}/health'
        },
        'note': 'Password stored securely in environment variables'
    }

    return result

if __name__ == "__main__":
    result = get_connection_info()
    print(json.dumps(result, indent=2))