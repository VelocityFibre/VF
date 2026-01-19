#!/usr/bin/env python3
"""
Get Database Queries
Fetches SQL query library.
"""

import sys
import requests
import argparse

API_BASE = "http://api.docs.fibreflow.app"

def get_queries(format: str = "text"):
    """Get SQL query library."""
    params = {"format": format}

    try:
        response = requests.get(
            f"{API_BASE}/api/v1/database/queries",
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

    except requests.exceptions.RequestException as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Get database query library")
    parser.add_argument("--format", "-f", default="text", choices=["text", "json"], help="Response format")

    args = parser.parse_args()
    get_queries(args.format)
