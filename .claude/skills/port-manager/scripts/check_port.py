#!/usr/bin/env python3
"""
Port Checker Tool
Quick port status and conflict checking
"""

import sys
import json
import socket
import argparse
import subprocess
from pathlib import Path

# Color codes
RED = '\033[91m'
GREEN = '\033[92m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

def check_port_status(port: int):
    """Comprehensive port status check"""

    # Load registry
    registry_path = Path(__file__).parent.parent / 'config' / 'port_registry.json'
    registry = {}

    if registry_path.exists():
        with open(registry_path, 'r') as f:
            registry = json.load(f)

    print(f"\n{BLUE}═══ Port {port} Status ═══{RESET}\n")

    # 1. Check if port is registered
    port_str = str(port)
    if port_str in registry.get('allocations', {}):
        allocation = registry['allocations'][port_str]
        print(f"{GREEN}✓ REGISTERED{RESET}")
        print(f"  Service: {allocation.get('service', 'Unknown')}")
        print(f"  Status: {allocation.get('status', 'Unknown')}")
        print(f"  Environment: {allocation.get('environment', 'Unknown')}")
        print(f"  Owner: {allocation.get('owner', 'Unknown')}")

        if allocation.get('url'):
            print(f"  URL: {allocation.get('url')}")

        if allocation.get('description'):
            print(f"  Description: {allocation.get('description')}")
    else:
        print(f"{YELLOW}✗ NOT REGISTERED{RESET}")

    # 2. Check if port is actually in use
    print(f"\n{BLUE}Network Status:{RESET}")

    is_open = False
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(1)
            result = sock.connect_ex(('localhost', port))
            is_open = (result == 0)
    except Exception as e:
        print(f"{RED}Error checking port: {e}{RESET}")

    if is_open:
        print(f"{GREEN}✓ PORT IS OPEN (Service is running){RESET}")

        # Try to identify the process
        try:
            result = subprocess.run(
                ['lsof', '-i', f':{port}'],
                capture_output=True,
                text=True,
                check=False
            )

            if result.stdout:
                lines = result.stdout.strip().split('\n')
                if len(lines) > 1:
                    print(f"\n{BLUE}Process Information:{RESET}")
                    # Parse lsof output
                    for line in lines[1:]:  # Skip header
                        parts = line.split()
                        if len(parts) >= 2:
                            print(f"  Process: {parts[0]} (PID: {parts[1]})")
        except:
            pass

        # Try netstat as fallback
        try:
            result = subprocess.run(
                ['netstat', '-tlpn'],
                capture_output=True,
                text=True,
                check=False
            )

            for line in result.stdout.splitlines():
                if f':{port}' in line and 'LISTEN' in line:
                    print(f"  Netstat: {line.strip()}")
        except:
            pass
    else:
        print(f"{RED}✗ PORT IS CLOSED (No service listening){RESET}")

    # 3. Check Docker containers
    print(f"\n{BLUE}Docker Status:{RESET}")

    try:
        result = subprocess.run(
            ['docker', 'ps', '--format', '{{.Names}}\t{{.Ports}}'],
            capture_output=True,
            text=True,
            check=False
        )

        found_in_docker = False
        for line in result.stdout.splitlines():
            if f':{port}->' in line or f'{port}/tcp' in line:
                parts = line.split('\t')
                if len(parts) >= 1:
                    print(f"{GREEN}✓ Container: {parts[0]}{RESET}")
                    found_in_docker = True

        if not found_in_docker:
            print(f"{YELLOW}✗ Not found in Docker containers{RESET}")
    except Exception as e:
        print(f"{YELLOW}Could not check Docker: {e}{RESET}")

    # 4. Summary and recommendations
    print(f"\n{BLUE}Summary:{RESET}")

    registered = port_str in registry.get('allocations', {})
    reg_status = registry['allocations'][port_str].get('status') if registered else None

    if registered and is_open:
        if reg_status == 'active':
            print(f"{GREEN}✓ Port is properly registered and active{RESET}")
        else:
            print(f"{YELLOW}⚠ Port is active but marked as {reg_status} in registry{RESET}")
            print(f"  → Run: python3 update_status.py {port} active")

    elif registered and not is_open:
        if reg_status == 'active':
            print(f"{RED}⚠ Port is registered as active but service is down!{RESET}")
            print(f"  → Check service logs and restart if needed")
        else:
            print(f"{YELLOW}Port is registered but not active (status: {reg_status}){RESET}")

    elif not registered and is_open:
        print(f"{RED}⚠ Port is in use but not registered!{RESET}")
        print(f"  → Register with: python3 allocate_port.py allocate [service-name] -p {port}")

    else:
        print(f"{GREEN}✓ Port is available for use{RESET}")
        print(f"  → Allocate with: python3 allocate_port.py allocate [service-name] -p {port}")

    return 0 if (registered and is_open) else 1

def main():
    parser = argparse.ArgumentParser(description='Check port status')
    parser.add_argument('port', type=int, help='Port number to check')
    parser.add_argument('-j', '--json', action='store_true', help='Output as JSON')

    args = parser.parse_args()

    if args.json:
        # JSON output for automation
        registry_path = Path(__file__).parent.parent / 'config' / 'port_registry.json'
        registry = {}

        if registry_path.exists():
            with open(registry_path, 'r') as f:
                registry = json.load(f)

        is_open = False
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(1)
                result = sock.connect_ex(('localhost', args.port))
                is_open = (result == 0)
        except:
            pass

        result = {
            'port': args.port,
            'registered': str(args.port) in registry.get('allocations', {}),
            'open': is_open,
            'allocation': registry.get('allocations', {}).get(str(args.port), None)
        }

        print(json.dumps(result, indent=2))
        return 0

    else:
        return check_port_status(args.port)

if __name__ == '__main__':
    sys.exit(main())
