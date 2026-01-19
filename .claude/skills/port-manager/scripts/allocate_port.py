#!/usr/bin/env python3
"""
Port Allocation Manager for VF Server
Intelligently allocates and manages port assignments
"""

import json
import socket
import argparse
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, List

# Color codes
RED = '\033[91m'
GREEN = '\033[92m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
CYAN = '\033[96m'
RESET = '\033[0m'

class PortAllocator:
    def __init__(self, registry_path: str = None):
        """Initialize port allocator"""
        if registry_path is None:
            registry_path = Path(__file__).parent.parent / 'config' / 'port_registry.json'

        self.registry_path = Path(registry_path)
        self.registry = self.load_registry()

    def load_registry(self) -> dict:
        """Load port registry"""
        if not self.registry_path.exists():
            # Create default registry
            return {
                "version": "1.0.0",
                "last_updated": datetime.now().strftime('%Y-%m-%d'),
                "server": "100.96.203.105",
                "allocations": {},
                "reserved_ranges": {
                    "3000-3099": "Web Applications",
                    "5000-5999": "Database Services",
                    "8000-8099": "API Services",
                    "8100-8199": "ML/AI Services",
                    "9000-9099": "Monitoring & Internal Tools",
                    "10000+": "Dynamic/Temporary Services"
                }
            }

        with open(self.registry_path, 'r') as f:
            return json.load(f)

    def save_registry(self):
        """Save registry back to file"""
        self.registry['last_updated'] = datetime.now().strftime('%Y-%m-%d')

        # Create backup
        if self.registry_path.exists():
            backup_path = self.registry_path.with_suffix('.json.bak')
            backup_path.write_text(self.registry_path.read_text())

        with open(self.registry_path, 'w') as f:
            json.dump(self.registry, f, indent=2)

    def is_port_available(self, port: int) -> bool:
        """Check if port is available for use"""
        # Check if registered
        if str(port) in self.registry.get('allocations', {}):
            return False

        # Check if actually in use
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(0.1)
                result = sock.connect_ex(('localhost', port))
                return result != 0
        except:
            return True

    def get_port_range(self, service_type: str) -> tuple:
        """Get appropriate port range for service type"""
        ranges = {
            'web': (3000, 3099),
            'database': (5000, 5999),
            'api': (8000, 8099),
            'ml': (8100, 8199),
            'ai': (8100, 8199),
            'monitoring': (9000, 9099),
            'internal': (9000, 9099),
            'dynamic': (10000, 10999),
            'temp': (10000, 10999)
        }

        return ranges.get(service_type.lower(), (10000, 10999))

    def find_next_available(self, start: int, end: int) -> Optional[int]:
        """Find next available port in range"""
        for port in range(start, end + 1):
            if self.is_port_available(port):
                return port
        return None

    def allocate_port(
        self,
        service: str,
        service_type: str = 'dynamic',
        environment: str = 'production',
        owner: str = None,
        description: str = None,
        preferred_port: int = None
    ) -> Optional[int]:
        """Allocate a new port for a service"""

        # Try preferred port first
        if preferred_port and self.is_port_available(preferred_port):
            port = preferred_port
        else:
            # Find port in appropriate range
            start, end = self.get_port_range(service_type)
            port = self.find_next_available(start, end)

            if port is None:
                print(f"{RED}Error: No available ports in range {start}-{end}{RESET}")
                return None

        # Register the port
        allocation = {
            'service': service,
            'description': description or f"{service} service",
            'environment': environment,
            'protocol': 'tcp',
            'owner': owner or 'unknown',
            'status': 'allocated',
            'allocated_at': datetime.now().isoformat(),
            'service_type': service_type
        }

        self.registry['allocations'][str(port)] = allocation
        self.save_registry()

        return port

    def release_port(self, port: int) -> bool:
        """Release a previously allocated port"""
        port_str = str(port)

        if port_str not in self.registry.get('allocations', {}):
            print(f"{YELLOW}Warning: Port {port} is not registered{RESET}")
            return False

        # Archive the allocation before removing
        allocation = self.registry['allocations'][port_str]
        allocation['released_at'] = datetime.now().isoformat()

        # Store in archive (optional)
        if 'archive' not in self.registry:
            self.registry['archive'] = []
        self.registry['archive'].append({**allocation, 'port': port})

        # Remove from active allocations
        del self.registry['allocations'][port_str]
        self.save_registry()

        return True

    def update_port_status(self, port: int, status: str, notes: str = None) -> bool:
        """Update the status of an allocated port"""
        port_str = str(port)

        if port_str not in self.registry.get('allocations', {}):
            print(f"{RED}Error: Port {port} is not registered{RESET}")
            return False

        self.registry['allocations'][port_str]['status'] = status
        if notes:
            self.registry['allocations'][port_str]['notes'] = notes
        self.registry['allocations'][port_str]['updated_at'] = datetime.now().isoformat()

        self.save_registry()
        return True

    def suggest_ports(self, service_type: str, count: int = 5) -> List[int]:
        """Suggest available ports for a service type"""
        start, end = self.get_port_range(service_type)
        suggestions = []

        for port in range(start, end + 1):
            if self.is_port_available(port):
                suggestions.append(port)
                if len(suggestions) >= count:
                    break

        return suggestions

    def print_allocation_summary(self):
        """Print summary of current allocations"""
        allocations = self.registry.get('allocations', {})

        print(f"\n{BLUE}═══ Port Allocations Summary ═══{RESET}")
        print(f"Total Allocated: {len(allocations)}\n")

        # Group by service type
        by_type = {}
        for port_str, info in allocations.items():
            stype = info.get('service_type', 'unknown')
            if stype not in by_type:
                by_type[stype] = []
            by_type[stype].append((int(port_str), info))

        for stype, ports in sorted(by_type.items()):
            print(f"{CYAN}▶ {stype.upper()} Services:{RESET}")
            for port, info in sorted(ports):
                status_color = GREEN if info.get('status') == 'active' else YELLOW
                print(f"  {status_color}{port:5d}{RESET}: {info.get('service', 'Unknown')}")
                if info.get('owner') != 'unknown':
                    print(f"         Owner: {info.get('owner')}")
            print()

def main():
    parser = argparse.ArgumentParser(description='Allocate and manage server ports')

    subparsers = parser.add_subparsers(dest='command', help='Commands')

    # Allocate command
    alloc_parser = subparsers.add_parser('allocate', help='Allocate a new port')
    alloc_parser.add_argument('service', help='Service name')
    alloc_parser.add_argument('-t', '--type', default='dynamic',
                             choices=['web', 'api', 'database', 'ml', 'ai', 'monitoring', 'dynamic'],
                             help='Service type')
    alloc_parser.add_argument('-e', '--env', default='production',
                             choices=['production', 'staging', 'development'],
                             help='Environment')
    alloc_parser.add_argument('-o', '--owner', help='Service owner')
    alloc_parser.add_argument('-d', '--description', help='Service description')
    alloc_parser.add_argument('-p', '--port', type=int, help='Preferred port number')

    # Release command
    release_parser = subparsers.add_parser('release', help='Release a port')
    release_parser.add_argument('port', type=int, help='Port to release')

    # Update command
    update_parser = subparsers.add_parser('update', help='Update port status')
    update_parser.add_argument('port', type=int, help='Port to update')
    update_parser.add_argument('status', help='New status')
    update_parser.add_argument('-n', '--notes', help='Additional notes')

    # Suggest command
    suggest_parser = subparsers.add_parser('suggest', help='Suggest available ports')
    suggest_parser.add_argument('-t', '--type', default='dynamic',
                               choices=['web', 'api', 'database', 'ml', 'ai', 'monitoring', 'dynamic'],
                               help='Service type')
    suggest_parser.add_argument('-c', '--count', type=int, default=5, help='Number of suggestions')

    # List command
    list_parser = subparsers.add_parser('list', help='List all allocations')

    # Check command
    check_parser = subparsers.add_parser('check', help='Check if port is available')
    check_parser.add_argument('port', type=int, help='Port to check')

    args = parser.parse_args()
    allocator = PortAllocator()

    if args.command == 'allocate':
        port = allocator.allocate_port(
            service=args.service,
            service_type=args.type,
            environment=args.env,
            owner=args.owner,
            description=args.description,
            preferred_port=args.port
        )

        if port:
            print(f"{GREEN}✓ Successfully allocated port {port} for {args.service}{RESET}")
            print(f"  Type: {args.type}")
            print(f"  Environment: {args.env}")
            if args.owner:
                print(f"  Owner: {args.owner}")
        else:
            print(f"{RED}✗ Failed to allocate port{RESET}")

    elif args.command == 'release':
        if allocator.release_port(args.port):
            print(f"{GREEN}✓ Port {args.port} released successfully{RESET}")
        else:
            print(f"{RED}✗ Failed to release port {args.port}{RESET}")

    elif args.command == 'update':
        if allocator.update_port_status(args.port, args.status, args.notes):
            print(f"{GREEN}✓ Port {args.port} status updated to '{args.status}'{RESET}")
        else:
            print(f"{RED}✗ Failed to update port {args.port}{RESET}")

    elif args.command == 'suggest':
        suggestions = allocator.suggest_ports(args.type, args.count)
        if suggestions:
            print(f"{BLUE}Suggested available ports for {args.type} services:{RESET}")
            for port in suggestions:
                print(f"  • {port}")
        else:
            print(f"{YELLOW}No available ports found in the {args.type} range{RESET}")

    elif args.command == 'list':
        allocator.print_allocation_summary()

    elif args.command == 'check':
        if allocator.is_port_available(args.port):
            print(f"{GREEN}✓ Port {args.port} is available{RESET}")
        else:
            port_str = str(args.port)
            if port_str in allocator.registry.get('allocations', {}):
                info = allocator.registry['allocations'][port_str]
                print(f"{YELLOW}✗ Port {args.port} is allocated to: {info.get('service', 'Unknown')}{RESET}")
            else:
                print(f"{RED}✗ Port {args.port} is in use but not registered{RESET}")

    else:
        parser.print_help()

if __name__ == '__main__':
    main()