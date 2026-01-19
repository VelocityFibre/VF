#!/usr/bin/env python3
"""
Execute DELETE query to remove data.
Warning: DESTRUCTIVE. Always use WHERE clause.
"""

import sys
import argparse
from pathlib import Path

# Add scripts dir to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from db_utils import DatabaseConnection, success_output, json_output


def execute_delete(query: str):
    """
    Execute a DELETE query.

    Args:
        query: SQL DELETE statement
    """
    # Safety check: only allow DELETE queries
    query_upper = query.strip().upper()
    if not query_upper.startswith("DELETE"):
        json_output({
            "error": "Only DELETE queries allowed with this tool",
            "success": False
        })
        sys.exit(1)

    # Require WHERE clause (prevent mass deletion)
    if "WHERE" not in query_upper:
        json_output({
            "error": "DELETE without WHERE clause is EXTREMELY dangerous",
            "hint": "Add a WHERE clause to target specific rows. This prevents accidental mass deletion.",
            "query": query,
            "success": False
        })
        sys.exit(1)

    db = DatabaseConnection()

    try:
        result = db.execute_mutation(query)
        success_output(
            data=result,
            message=f"Deleted {result['rows_affected']} row(s)"
        )

    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Execute DELETE query")
    parser.add_argument("--query", required=True, help="SQL DELETE query")
    args = parser.parse_args()

    execute_delete(args.query)
