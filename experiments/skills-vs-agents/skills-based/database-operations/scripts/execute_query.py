#!/usr/bin/env python3
"""
Execute a SELECT query and return results.
Read-only, safe for data retrieval.
"""

import sys
import argparse
from pathlib import Path

# Add scripts dir to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from db_utils import DatabaseConnection, success_output, json_output


def execute_query(query: str, limit: int = 100):
    """
    Execute a SELECT query.

    Args:
        query: SQL SELECT statement
        limit: Maximum rows to return (default: 100)
    """
    # Safety check: only allow SELECT queries
    query_upper = query.strip().upper()
    if not query_upper.startswith("SELECT"):
        json_output({
            "error": "Only SELECT queries allowed with this tool",
            "hint": "Use execute_insert/execute_update/execute_delete for mutations",
            "success": False
        })
        sys.exit(1)

    db = DatabaseConnection()

    try:
        # Add LIMIT if not already present
        if "LIMIT" not in query_upper and limit:
            query = f"{query.rstrip(';')} LIMIT {limit};"

        results = db.execute_query(query)

        success_output(
            data={
                "query": query,
                "rows": results,
                "row_count": len(results)
            },
            message=f"Query returned {len(results)} rows"
        )

    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Execute SELECT query")
    parser.add_argument("--query", required=True, help="SQL SELECT query")
    parser.add_argument("--limit", type=int, default=100, help="Row limit (default: 100)")
    args = parser.parse_args()

    execute_query(args.query, args.limit)
