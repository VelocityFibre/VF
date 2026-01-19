#!/usr/bin/env python3
"""
Port Scanner and Conflict Detector for VF Server
Scans active ports and detects conflicts with registry
"""

import json
import subprocess
import socket
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple

# Color codes for terminal output
RED = '\033[91m'
GREEN = '\033[92m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

class PortScanner:
    def __init__(self, registry_path: str = None):
        """Initialize port scanner with registry"""
        if registry_path is None:
            registry_path = Path(__file__).parent.parent / 'config' / 'port_registry.json'

        self.registry_path = Path(registry_path)
        self.registry = self.load_registry()

    def load_registry(self) -> dict:
        """Load port registry from JSON file"""
        if not self.registry_path.exists():
            print(f"{YELLOW}Warning: Registry not found at {self.registry_path}{RESET}")
            return {"allocations": {}}

        with open(self.registry_path, 'r') as f:
            return json.load(f)

    def scan_active_ports(self, start_port: int = 3000, end_port: int = 10000) -> List[int]:
        """Scan for active ports using netstat"""
        active_ports = []

        try:
            # Use netstat to get all listening ports
            result = subprocess.run(
                ['netstat', '-tlpn'],
                capture_output=True,
                text=True,
                check=False
            )

            # Parse netstat output
            for line in result.stdout.splitlines():
                if 'LISTEN' in line:
                    parts = line.split()
                    if len(parts) >= 4:
                        addr = parts[3]
                        if ':' in addr:
                            port_str = addr.split(':')[-1]
                            try:
                                port = int(port_str)
                                if start_port <= port <= end_port:
                                    active_ports.append(port)
                            except ValueError:
                                continue
        except Exception as e:
            print(f"{RED}Error scanning ports with netstat: {e}{RESET}")
            print(f"{YELLOW}Falling back to socket scanning...{RESET}")

            # Fallback to socket scanning
            for port in range(start_port, min(end_port + 1, start_port + 1000)):
                if self.is_port_open('localhost', port):
                    active_ports.append(port)

        return sorted(active_ports)

    def is_port_open(self, host: str, port: int) -> bool:
        """Check if a specific port is open"""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(0.1)
                result = sock.connect_ex((host, port))
                return result == 0
        except:
            return False

    def scan_docker_ports(self) -> Dict[int, str]:
        """Scan Docker containers for exposed ports"""
        docker_ports = {}

        try:
            result = subprocess.run(
                ['docker', 'ps', '--format', '{{.Names}}\t{{.Ports}}'],
                capture_output=True,
                text=True,
                check=False
            )

            for line in result.stdout.splitlines():
                if '\t' in line:
                    name, ports = line.split('\t', 1)
                    # Parse port mappings like "0.0.0.0:8082->80/tcp"
                    import re
                    port_pattern = r'(\d+)->(\d+)'
                    matches = re.findall(port_pattern, ports)
                    for host_port, container_port in matches:
                        docker_ports[int(host_port)] = f"Docker: {name}"
        except Exception as e:
            print(f"{YELLOW}Warning: Could not scan Docker ports: {e}{RESET}")

        return docker_ports

    def detect_conflicts(self) -> List[Dict]:
        """Detect conflicts between active ports and registry"""
        conflicts = []
        active_ports = self.scan_active_ports()
        docker_ports = self.scan_docker_ports()
        registered_ports = {int(k): v for k, v in self.registry.get('allocations', {}).items()}

        # Check for unregistered active ports
        for port in active_ports:
            if port not in registered_ports:
                conflict = {
                    'type': 'unregistered',
                    'port': port,
                    'status': 'active',
                    'docker': docker_ports.get(port, None)
                }
                conflicts.append(conflict)

        # Check for registered but inactive ports
        for port, info in registered_ports.items():
            if info.get('status') == 'active' and port not in active_ports:
                conflict = {
                    'type': 'inactive',
                    'port': port,
                    'service': info.get('service', 'Unknown'),
                    'expected': 'active',
                    'actual': 'inactive'
                }
                conflicts.append(conflict)

        return conflicts

    def print_report(self, detailed: bool = False):
        """Print comprehensive port report"""
        print(f"\n{BLUE}═══ VF Server Port Management Report ═══{RESET}")
        print(f"Server: {self.registry.get('server', 'Unknown')}")
        print(f"Scan Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

        # Active ports
        active_ports = self.scan_active_ports()
        docker_ports = self.scan_docker_ports()
        registered_ports = {int(k): v for k, v in self.registry.get('allocations', {}).items()}

        print(f"{GREEN}▶ Active Ports ({len(active_ports)} found):{RESET}")
        for port in active_ports:
            info = registered_ports.get(port, {})
            docker_info = docker_ports.get(port, '')

            if port in registered_ports:
                status = f"✓ {info.get('service', 'Unknown')}"
                color = GREEN
            else:
                status = f"⚠ UNREGISTERED {docker_info}"
                color = YELLOW

            print(f"  {color}{port:5d}: {status}{RESET}")

            if detailed and port in registered_ports:
                print(f"         Owner: {info.get('owner', 'Unknown')}")
                print(f"         Environment: {info.get('environment', 'Unknown')}")
                if info.get('url'):
                    print(f"         URL: {info.get('url')}")

        # Conflicts
        conflicts = self.detect_conflicts()
        if conflicts:
            print(f"\n{RED}▶ Conflicts Detected ({len(conflicts)}):{RESET}")
            for conflict in conflicts:
                if conflict['type'] == 'unregistered':
                    print(f"  {YELLOW}Port {conflict['port']}: Active but not registered{RESET}")
                    if conflict.get('docker'):
                        print(f"    → {conflict['docker']}")
                elif conflict['type'] == 'inactive':
                    print(f"  {RED}Port {conflict['port']}: {conflict['service']} is inactive{RESET}")
        else:
            print(f"\n{GREEN}✓ No conflicts detected{RESET}")

        # Summary
        print(f"\n{BLUE}▶ Summary:{RESET}")
        print(f"  Total Active: {len(active_ports)}")
        print(f"  Registered: {len([p for p in active_ports if p in registered_ports])}")
        print(f"  Unregistered: {len([p for p in active_ports if p not in registered_ports])}")
        print(f"  Docker Managed: {len(docker_ports)}")

        # Reserved ranges
        if detailed:
            print(f"\n{BLUE}▶ Reserved Port Ranges:{RESET}")
            for range_str, purpose in self.registry.get('reserved_ranges', {}).items():
                print(f"  {range_str:15s}: {purpose}")

def main():
    parser = argparse.ArgumentParser(description='Scan and manage server ports')
    parser.add_argument('-d', '--detailed', action='store_true', help='Show detailed information')
    parser.add_argument('-j', '--json', action='store_true', help='Output as JSON')
    parser.add_argument('-c', '--check-port', type=int, help='Check specific port')
    parser.add_argument('-r', '--registry', help='Path to registry file')

    args = parser.parse_args()

    scanner = PortScanner(args.registry)

    if args.check_port:
        # Check specific port
        is_open = scanner.is_port_open('localhost', args.check_port)
        registered = str(args.check_port) in scanner.registry.get('allocations', {})

        if args.json:
            result = {
                'port': args.check_port,
                'open': is_open,
                'registered': registered
            }
            print(json.dumps(result, indent=2))
        else:
            status = f"{GREEN}OPEN{RESET}" if is_open else f"{RED}CLOSED{RESET}"
            reg_status = f"{GREEN}REGISTERED{RESET}" if registered else f"{YELLOW}UNREGISTERED{RESET}"
            print(f"Port {args.check_port}: {status}, {reg_status}")

            if registered:
                info = scanner.registry['allocations'][str(args.check_port)]
                print(f"  Service: {info.get('service', 'Unknown')}")
                print(f"  Owner: {info.get('owner', 'Unknown')}")

    elif args.json:
        # JSON output
        result = {
            'timestamp': datetime.now().isoformat(),
            'active_ports': scanner.scan_active_ports(),
            'docker_ports': scanner.scan_docker_ports(),
            'conflicts': scanner.detect_conflicts()
        }
        print(json.dumps(result, indent=2))

    else:
        # Regular report
        scanner.print_report(detailed=args.detailed)

if __name__ == '__main__':
    main()