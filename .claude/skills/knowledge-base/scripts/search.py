#!/usr/bin/env python3
"""
Search Knowledge Base
Searches across all documentation files.
"""

import sys
import json
import requests
import argparse

API_BASE = "http://api.docs.fibreflow.app"

def search_docs(query: str, category: str = None, format: str = "json"):
    """Search documentation."""
    params = {"q": query, "format": format}
    if category:
        params["category"] = category

    try:
        response = requests.get(f"{API_BASE}/api/v1/search", params=params, timeout=10)
        response.raise_for_status()

        results = response.json()

        if not results:
            print(f"No results found for '{query}'")
            return

        print(f"Found {len(results)} results for '{query}':\n")

        for result in results:
            print(f"📄 {result['file']} ({result['category']})")
            print(f"   Matches: {result['score']}")
            for match in result['matches'][:3]:  # Show first 3 matches
                print(f"   - {match}")
            print()

    except requests.exceptions.RequestException as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Search knowledge base")
    parser.add_argument("--query", "-q", required=True, help="Search query")
    parser.add_argument("--category", "-c", help="Filter by category")
    parser.add_argument("--format", "-f", default="json", choices=["json", "text"], help="Response format")

    args = parser.parse_args()
    search_docs(args.query, args.category, args.format)
