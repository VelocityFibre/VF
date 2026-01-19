#!/usr/bin/env python3
"""
Get Server Documentation
Fetches documentation for a specific server.
"""

import sys
import requests
import argparse

API_BASE = "http://api.docs.fibreflow.app"

def get_server_docs(server_name: str, format: str = "markdown"):
    """Get server documentation."""
    params = {"format": format}

    try:
        response = requests.get(
            f"{API_BASE}/api/v1/servers/{server_name}",
            params=params,
            timeout=10
        )
        response.raise_for_status()

        if format == "text":
            print(response.text)
        else:
            data = response.json()
            print(f"📄 {data['path']}\n")
            print(data['content'])

    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            print(f"Server '{server_name}' not found.", file=sys.stderr)
            print("Available: vf-server, hostinger-vps, vf, hostinger", file=sys.stderr)
        else:
            print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Get server documentation")
    parser.add_argument("--server", "-s", required=True, help="Server name (vf-server, hostinger-vps)")
    parser.add_argument("--format", "-f", default="markdown", choices=["markdown", "text"], help="Response format")

    args = parser.parse_args()
    get_server_docs(args.server, args.format)
