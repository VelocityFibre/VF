"""
Server Documentation Generation Tool

Extract server configuration details for documentation.
"""

from typing import Dict, Any, List
import json
import yaml
import os
import subprocess
from pathlib import Path


class ServerDocumentationTool:
    """
    Generate comprehensive server documentation
    Supports multiple server types and configurations
    """

    @staticmethod
    def extract_server_details(server_name: str) -> Dict[str, Any]:
        """
        Extract server details based on server name
        
        Supports predefined server configurations
        
        Args:
            server_name (str): Name of the server (e.g., 'hostinger_vps', 'vf_server')
        
        Returns:
            Dict with server configuration details
        """
        server_configs = {
            'hostinger_vps': {
                'name': 'Hostinger VPS',
                'host': '100.96.203.105',
                'type': 'Virtual Private Server',
                'ports': {
                    'ssh': 22,
                    'http': 80,
                    'https': 443,
                    'docker': 2375
                },
                'services': [
                    'ssh',
                    'nginx',
                    'docker',
                    'cloudflared'
                ],
                'paths': {
                    'home': '/home/louisdup',
                    'projects': '/home/louisdup/Agents',
                    'logs': '/home/louisdup/logs'
                }
            },
            'vf_server': {
                'name': 'Velocity Fibre Server',
                'host': '100.96.203.106',
                'type': 'Dedicated Production Server',
                'ports': {
                    'ssh': 22,
                    'http': 80,
                    'https': 443,
                    'postgresql': 5432
                },
                'services': [
                    'ssh',
                    'nginx',
                    'postgresql',
                    'redis',
                    'cloudflared'
                ],
                'paths': {
                    'home': '/home/vf_admin',
                    'projects': '/home/vf_admin/projects',
                    'databases': '/var/lib/postgresql'
                }
            }
        }
        
        return server_configs.get(server_name, {})

    @staticmethod
    def generate_markdown(server_details: Dict[str, Any]) -> str:
        """
        Convert server details to Markdown documentation
        
        Args:
            server_details (Dict): Server configuration details
        
        Returns:
            str: Markdown documentation
        """
        if not server_details:
            return "# Server Configuration\n\n*No details available*"

        markdown = f"""# {server_details['name']} Configuration

## Overview

- **Type**: {server_details['type']}
- **Host IP**: `{server_details['host']}`

## Network Configuration

### Ports
{' '.join([f'- **{k.upper()}**: `{v}`' for k, v in server_details['ports'].items()])}

### Services
{' '.join([f'- `{service}`' for service in server_details['services']])}

## File System Paths
{' '.join([f'- **{k.capitalize()}**: `{v}`' for k, v in server_details['paths'].items()])}

## Access & Security

### SSH Connection
```bash
ssh louisdup@{server_details['host']}
```

### Recommended Firewall Rules
- Restrict SSH to specific IP ranges
- Use key-based authentication
- Disable root login
"""
        return markdown

    def document_server(self, server_name: str) -> Dict[str, str]:
        """
        Complete server documentation workflow
        
        Args:
            server_name (str): Server to document
        
        Returns:
            Dict with different documentation formats
        """
        server_details = self.extract_server_details(server_name)
        markdown_doc = self.generate_markdown(server_details)
        
        return {
            'raw': json.dumps(server_details),
            'markdown': markdown_doc
        }