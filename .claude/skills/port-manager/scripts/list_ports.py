#!/usr/bin/env python3
"""
Quick Port Listing Tool
Simple, fast port overview for VF Server
"""

import json
import argparse
from pathlib import Path
from datetime import datetime

# Color codes
RED = '\033[91m'
GREEN = '\033[92m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
CYAN = '\033[96m'
RESET = '\033[0m'

def load_registry():
    """Load the port registry"""
    registry_path = Path(__file__).parent.parent / 'config' / 'port_registry.json'

    if not registry_path.exists():
        print(f"{RED}Error: Registry not found at {registry_path}{RESET}")
        return {}

    with open(registry_path, 'r') as f:
        return json.load(f)

def print_simple_list():
    """Print a simple list of all allocated ports"""
    registry = load_registry()
    allocations = registry.get('allocations', {})

    if not allocations:
        print(f"{YELLOW}No ports allocated yet{RESET}")
        return

    print(f"\n{BLUE}PORT   SERVICE{RESET}")
    print("─" * 50)

    for port_str in sorted(allocations.keys(), key=int):
        info = allocations[port_str]
        service = info.get('service', 'Unknown')
        status = info.get('status', 'unknown')

        # Color based on status
        if status == 'active':
            color = GREEN
        elif status == 'inactive':
            color = RED
        else:
            color = YELLOW

        # Truncate long service names
        if len(service) > 40:
            service = service[:37] + "..."

        print(f"{color}{port_str:5s}  {service}{RESET}")

def print_detailed_list():
    """Print detailed information about all ports"""
    registry = load_registry()
    allocations = registry.get('allocations', {})

    print(f"\n{BLUE}═══ VF Server Port Registry ═══{RESET}")
    print(f"Server: {registry.get('server', 'Unknown')}")
    print(f"Last Updated: {registry.get('last_updated', 'Unknown')}")
    print(f"Total Ports: {len(allocations)}\n")

    # Group by environment
    by_env = {'production': [], 'staging': [], 'development': [], 'other': []}

    for port_str, info in allocations.items():
        env = info.get('environment', 'other')
        if env not in by_env:
            env = 'other'
        by_env[env].append((int(port_str), info))

    for env, ports in by_env.items():
        if not ports:
            continue

        env_color = {
            'production': RED,
            'staging': YELLOW,
            'development': GREEN,
            'other': CYAN
        }.get(env, RESET)

        print(f"{env_color}▶ {env.upper()} ({len(ports)} ports):{RESET}")

        for port, info in sorted(ports):
            status = info.get('status', 'unknown')
            service = info.get('service', 'Unknown')
            owner = info.get('owner', 'unknown')

            # Status indicator
            if status == 'active':
                status_icon = '●'
                status_color = GREEN
            elif status == 'inactive':
                status_icon = '○'
                status_color = RED
            else:
                status_icon = '◐'
                status_color = YELLOW

            print(f"  {status_color}{status_icon}{RESET} {port:5d}: {service[:40]}")

            # Show URL if available
            if info.get('url'):
                print(f"           URL: {info['url']}")

            # Show owner if not default
            if owner not in ['unknown', 'velo']:
                print(f"           Owner: {owner}")

        print()

def print_by_range():
    """Print ports grouped by their assigned ranges"""
    registry = load_registry()
    allocations = registry.get('allocations', {})
    ranges = registry.get('reserved_ranges', {})

    print(f"\n{BLUE}═══ Ports by Range ═══{RESET}\n")

    # Parse ranges
    range_map = {}
    for range_str, purpose in ranges.items():
        if '-' in range_str:
            start, end = range_str.split('-')
            start = int(start)
            end = int(end) if '+' not in end else 99999
            range_map[(start, end)] = purpose

    # Group ports by range
    by_range = {purpose: [] for purpose in ranges.values()}
    by_range['Unassigned'] = []

    for port_str, info in allocations.items():
        port = int(port_str)
        assigned = False

        for (start, end), purpose in range_map.items():
            if start <= port <= end:
                by_range[purpose].append((port, info))
                assigned = True
                break

        if not assigned:
            by_range['Unassigned'].append((port, info))

    # Print each range
    for purpose, ports in by_range.items():
        if not ports:
            continue

        print(f"{CYAN}▶ {purpose} ({len(ports)} ports):{RESET}")

        for port, info in sorted(ports):
            service = info.get('service', 'Unknown')
            status = '✓' if info.get('status') == 'active' else '✗'
            color = GREEN if status == '✓' else RED

            print(f"  {color}{status}{RESET} {port:5d}: {service[:40]}")

        print()

def print_csv_format():
    """Export port list as CSV"""
    registry = load_registry()
    allocations = registry.get('allocations', {})

    print("Port,Service,Status,Environment,Owner,URL")

    for port_str in sorted(allocations.keys(), key=int):
        info = allocations[port_str]

        service = info.get('service', '').replace(',', ';')
        status = info.get('status', '')
        env = info.get('environment', '')
        owner = info.get('owner', '')
        url = info.get('url', '')

        print(f"{port_str},{service},{status},{env},{owner},{url}")

def main():
    parser = argparse.ArgumentParser(description='List allocated server ports')
    parser.add_argument('-d', '--detailed', action='store_true', help='Show detailed information')
    parser.add_argument('-r', '--by-range', action='store_true', help='Group by port ranges')
    parser.add_argument('-c', '--csv', action='store_true', help='Output as CSV')
    parser.add_argument('-e', '--env', help='Filter by environment (production/staging/development)')

    args = parser.parse_args()

    if args.csv:
        print_csv_format()
    elif args.by_range:
        print_by_range()
    elif args.detailed:
        print_detailed_list()
    else:
        print_simple_list()

if __name__ == '__main__':
    main()