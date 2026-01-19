#!/usr/bin/env python3
"""
Get Database Schema
Fetches Neon PostgreSQL schema overview.
"""

import sys
import requests
import argparse

API_BASE = "http://api.docs.fibreflow.app"

def get_schema(format: str = "markdown"):
    """Get database schema overview."""
    params = {"format": format}

    try:
        response = requests.get(
            f"{API_BASE}/api/v1/database/schema",
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
    parser = argparse.ArgumentParser(description="Get database schema")
    parser.add_argument("--format", "-f", default="markdown", choices=["markdown", "text"], help="Response format")

    args = parser.parse_args()
    get_schema(args.format)
