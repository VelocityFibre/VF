#!/usr/bin/env python3
"""
Dokploy Integration for Port Management
Syncs port allocations with Dokploy deployments
"""

import json
import subprocess
import requests
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

# Color codes
RED = '\033[91m'
GREEN = '\033[92m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
MAGENTA = '\033[95m'
RESET = '\033[0m'

class DokploySync:
    def __init__(self, registry_path: str = None, dokploy_url: str = None):
        """Initialize Dokploy sync"""
        if registry_path is None:
            registry_path = Path(__file__).parent.parent / 'config' / 'port_registry.json'

        self.registry_path = Path(registry_path)
        self.registry = self.load_registry()

        # Dokploy API endpoint (adjust based on your setup)
        self.dokploy_url = dokploy_url or 'http://localhost:3000'

    def load_registry(self) -> dict:
        """Load port registry"""
        if not self.registry_path.exists():
            print(f"{YELLOW}Warning: Registry not found at {self.registry_path}{RESET}")
            return {"allocations": {}}

        with open(self.registry_path, 'r') as f:
            return json.load(f)

    def save_registry(self):
        """Save registry back to file"""
        self.registry['last_updated'] = datetime.now().strftime('%Y-%m-%d')
        with open(self.registry_path, 'w') as f:
            json.dump(self.registry, f, indent=2)

    def scan_docker_compose(self, compose_path: str = None) -> Dict[str, List[int]]:
        """Scan docker-compose files for port mappings"""
        services_ports = {}

        # Common docker-compose locations
        compose_files = []
        if compose_path:
            compose_files.append(Path(compose_path))
        else:
            # Search for docker-compose files
            search_dirs = [
                Path.home() / 'dokploy',
                Path('/opt/dokploy'),
                Path('/srv/dokploy'),
                Path.cwd()
            ]

            for dir in search_dirs:
                if dir.exists():
                    compose_files.extend(dir.glob('**/docker-compose*.y*ml'))
                    compose_files.extend(dir.glob('**/compose*.y*ml'))

        for compose_file in compose_files:
            try:
                import yaml
                with open(compose_file, 'r') as f:
                    compose_data = yaml.safe_load(f)

                if 'services' in compose_data:
                    for service_name, service_config in compose_data['services'].items():
                        if 'ports' in service_config:
                            ports = []
                            for port_mapping in service_config['ports']:
                                # Parse port mappings like "8080:80" or "3000"
                                if isinstance(port_mapping, str):
                                    if ':' in port_mapping:
                                        host_port = port_mapping.split(':')[0]
                                        # Handle IP:port format
                                        if '.' in host_port:
                                            host_port = host_port.split('.')[-1]
                                        try:
                                            ports.append(int(host_port))
                                        except ValueError:
                                            continue
                                    else:
                                        try:
                                            ports.append(int(port_mapping))
                                        except ValueError:
                                            continue
                                elif isinstance(port_mapping, int):
                                    ports.append(port_mapping)

                            if ports:
                                services_ports[service_name] = ports

            except Exception as e:
                print(f"{YELLOW}Warning: Could not parse {compose_file}: {e}{RESET}")

        return services_ports

    def scan_dokploy_apps(self) -> List[Dict]:
        """Scan Dokploy managed applications"""
        apps = []

        try:
            # Try to get Dokploy apps via API
            response = requests.get(f"{self.dokploy_url}/api/apps", timeout=5)
            if response.status_code == 200:
                apps_data = response.json()
                for app in apps_data:
                    app_info = {
                        'name': app.get('name'),
                        'port': app.get('port'),
                        'environment': app.get('environment', 'production'),
                        'status': app.get('status', 'unknown')
                    }
                    apps.append(app_info)
        except:
            # Fallback to docker inspection
            try:
                result = subprocess.run(
                    ['docker', 'ps', '--format', '{{.Names}}\t{{.Ports}}\t{{.Labels}}'],
                    capture_output=True,
                    text=True,
                    check=False
                )

                for line in result.stdout.splitlines():
                    parts = line.split('\t')
                    if len(parts) >= 2:
                        name = parts[0]
                        ports = parts[1]
                        labels = parts[2] if len(parts) > 2 else ''

                        # Check if managed by Dokploy
                        if 'dokploy' in name.lower() or 'dokploy' in labels.lower():
                            import re
                            port_pattern = r'(\d+)->(\d+)'
                            matches = re.findall(port_pattern, ports)
                            for host_port, container_port in matches:
                                apps.append({
                                    'name': name,
                                    'port': int(host_port),
                                    'environment': 'production',
                                    'status': 'running'
                                })
            except Exception as e:
                print(f"{YELLOW}Warning: Could not scan Docker containers: {e}{RESET}")

        return apps

    def sync_with_registry(self, dry_run: bool = False) -> Dict:
        """Sync Dokploy apps with port registry"""
        dokploy_apps = self.scan_dokploy_apps()
        compose_services = self.scan_docker_compose()

        sync_report = {
            'added': [],
            'updated': [],
            'conflicts': [],
            'removed': []
        }

        # Process Dokploy apps
        for app in dokploy_apps:
            if app['port']:
                port_str = str(app['port'])

                if port_str in self.registry.get('allocations', {}):
                    # Update existing allocation
                    existing = self.registry['allocations'][port_str]
                    if existing.get('managed_by') != 'dokploy':
                        sync_report['conflicts'].append({
                            'port': app['port'],
                            'dokploy_app': app['name'],
                            'registered_to': existing.get('service')
                        })
                    else:
                        # Update status
                        if not dry_run:
                            self.registry['allocations'][port_str]['status'] = app['status']
                            self.registry['allocations'][port_str]['updated_at'] = datetime.now().isoformat()
                        sync_report['updated'].append(app['port'])
                else:
                    # Add new allocation
                    if not dry_run:
                        self.registry['allocations'][port_str] = {
                            'service': f"Dokploy: {app['name']}",
                            'description': f"Dokploy managed application",
                            'environment': app['environment'],
                            'protocol': 'tcp',
                            'managed_by': 'dokploy',
                            'owner': 'dokploy',
                            'status': app['status'],
                            'allocated_at': datetime.now().isoformat()
                        }
                    sync_report['added'].append(app['port'])

        # Process docker-compose services
        for service_name, ports in compose_services.items():
            for port in ports:
                port_str = str(port)

                if port_str not in self.registry.get('allocations', {}):
                    if not dry_run:
                        self.registry['allocations'][port_str] = {
                            'service': f"Compose: {service_name}",
                            'description': f"Docker Compose service",
                            'environment': 'production',
                            'protocol': 'tcp',
                            'managed_by': 'docker-compose',
                            'owner': 'docker',
                            'status': 'active',
                            'allocated_at': datetime.now().isoformat()
                        }
                    sync_report['added'].append(port)

        # Check for orphaned Dokploy allocations
        active_ports = set()
        for app in dokploy_apps:
            if app['port']:
                active_ports.add(str(app['port']))

        for port_str, allocation in self.registry.get('allocations', {}).items():
            if allocation.get('managed_by') == 'dokploy' and port_str not in active_ports:
                sync_report['removed'].append(int(port_str))
                if not dry_run:
                    # Mark as inactive rather than delete
                    self.registry['allocations'][port_str]['status'] = 'inactive'
                    self.registry['allocations'][port_str]['notes'] = 'Dokploy app no longer active'

        if not dry_run:
            self.save_registry()

        return sync_report

    def generate_nginx_config(self) -> str:
        """Generate Nginx reverse proxy configuration from registry"""
        nginx_config = []
        nginx_config.append("# Generated Nginx configuration for Dokploy services")
        nginx_config.append(f"# Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

        for port_str, allocation in sorted(self.registry.get('allocations', {}).items()):
            if allocation.get('status') == 'active' and allocation.get('url'):
                service = allocation.get('service', 'Unknown')
                url = allocation.get('url')

                # Parse domain from URL
                domain = url.replace('https://', '').replace('http://', '').split('/')[0]

                nginx_config.append(f"# {service}")
                nginx_config.append(f"server {{")
                nginx_config.append(f"    server_name {domain};")
                nginx_config.append(f"    listen 80;")
                nginx_config.append(f"    listen 443 ssl;")
                nginx_config.append(f"")
                nginx_config.append(f"    location / {{")
                nginx_config.append(f"        proxy_pass http://localhost:{port_str};")
                nginx_config.append(f"        proxy_set_header Host $host;")
                nginx_config.append(f"        proxy_set_header X-Real-IP $remote_addr;")
                nginx_config.append(f"        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;")
                nginx_config.append(f"        proxy_set_header X-Forwarded-Proto $scheme;")
                nginx_config.append(f"    }}")
                nginx_config.append(f"}}\n")

        return '\n'.join(nginx_config)

    def print_sync_report(self, report: Dict, dry_run: bool = False):
        """Print sync report in a formatted way"""
        mode = "DRY RUN" if dry_run else "LIVE"
        print(f"\n{BLUE}═══ Dokploy Sync Report ({mode}) ═══{RESET}")
        print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

        if report['added']:
            print(f"{GREEN}▶ New Ports Added ({len(report['added'])}):{RESET}")
            for port in sorted(report['added']):
                print(f"  • Port {port}")

        if report['updated']:
            print(f"{BLUE}▶ Ports Updated ({len(report['updated'])}):{RESET}")
            for port in sorted(report['updated']):
                print(f"  • Port {port}")

        if report['conflicts']:
            print(f"{RED}▶ Conflicts Detected ({len(report['conflicts'])}):{RESET}")
            for conflict in report['conflicts']:
                print(f"  • Port {conflict['port']}: {conflict['dokploy_app']} vs {conflict['registered_to']}")

        if report['removed']:
            print(f"{YELLOW}▶ Inactive Ports ({len(report['removed'])}):{RESET}")
            for port in sorted(report['removed']):
                print(f"  • Port {port}")

        if not any([report['added'], report['updated'], report['conflicts'], report['removed']]):
            print(f"{GREEN}✓ Registry is in sync with Dokploy{RESET}")

def main():
    parser = argparse.ArgumentParser(description='Sync Dokploy deployments with port registry')
    parser.add_argument('-d', '--dry-run', action='store_true', help='Preview changes without saving')
    parser.add_argument('-n', '--nginx', action='store_true', help='Generate Nginx configuration')
    parser.add_argument('-c', '--compose-path', help='Path to docker-compose file')
    parser.add_argument('-u', '--dokploy-url', help='Dokploy API URL')
    parser.add_argument('-s', '--scan-only', action='store_true', help='Only scan and display Dokploy apps')

    args = parser.parse_args()

    sync = DokploySync(dokploy_url=args.dokploy_url)

    if args.scan_only:
        # Just scan and display
        apps = sync.scan_dokploy_apps()
        compose = sync.scan_docker_compose(args.compose_path)

        print(f"\n{MAGENTA}═══ Dokploy Applications ═══{RESET}")
        if apps:
            for app in apps:
                status_color = GREEN if app['status'] == 'running' else YELLOW
                print(f"{status_color}• {app['name']:30s} Port: {app['port']:5d} [{app['status']}]{RESET}")
        else:
            print(f"{YELLOW}No Dokploy applications found{RESET}")

        if compose:
            print(f"\n{MAGENTA}═══ Docker Compose Services ═══{RESET}")
            for service, ports in compose.items():
                print(f"• {service}: {', '.join(map(str, ports))}")

    elif args.nginx:
        # Generate Nginx config
        config = sync.generate_nginx_config()
        print(config)

        print(f"\n{BLUE}To apply this configuration:{RESET}")
        print(f"  1. Save to: /etc/nginx/sites-available/dokploy-services")
        print(f"  2. Link: ln -s /etc/nginx/sites-available/dokploy-services /etc/nginx/sites-enabled/")
        print(f"  3. Test: nginx -t")
        print(f"  4. Reload: systemctl reload nginx")

    else:
        # Perform sync
        report = sync.sync_with_registry(dry_run=args.dry_run)
        sync.print_sync_report(report, dry_run=args.dry_run)

        if not args.dry_run and any([report['added'], report['updated'], report['removed']]):
            print(f"\n{GREEN}✓ Registry updated successfully{RESET}")
            print(f"  Registry file: {sync.registry_path}")

if __name__ == '__main__':
    main()