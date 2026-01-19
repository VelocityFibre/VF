#!/usr/bin/env python3
"""
Execute UPDATE query to modify existing data.
Warning: Modifies database. Use WHERE clause.
"""

import sys
import argparse
from pathlib import Path

# Add scripts dir to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from db_utils import DatabaseConnection, success_output, json_output


def execute_update(query: str):
    """
    Execute an UPDATE query.

    Args:
        query: SQL UPDATE statement
    """
    # Safety check: only allow UPDATE queries
    query_upper = query.strip().upper()
    if not query_upper.startswith("UPDATE"):
        json_output({
            "error": "Only UPDATE queries allowed with this tool",
            "success": False
        })
        sys.exit(1)

    # Warn if no WHERE clause (potential mass update)
    if "WHERE" not in query_upper:
        json_output({
            "error": "UPDATE without WHERE clause is dangerous",
            "hint": "Add a WHERE clause to target specific rows",
            "query": query,
            "success": False
        })
        sys.exit(1)

    db = DatabaseConnection()

    try:
        result = db.execute_mutation(query)
        success_output(
            data=result,
            message=f"Updated {result['rows_affected']} row(s)"
        )

    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Execute UPDATE query")
    parser.add_argument("--query", required=True, help="SQL UPDATE query")
    args = parser.parse_args()

    execute_update(args.query)
