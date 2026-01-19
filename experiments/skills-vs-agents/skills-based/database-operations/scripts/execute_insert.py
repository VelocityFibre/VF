#!/usr/bin/env python3
"""
Execute INSERT query to add new data.
Warning: Modifies database.
"""

import sys
import argparse
from pathlib import Path

# Add scripts dir to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from db_utils import DatabaseConnection, success_output, json_output


def execute_insert(query: str):
    """
    Execute an INSERT query.

    Args:
        query: SQL INSERT statement
    """
    # Safety check: only allow INSERT queries
    query_upper = query.strip().upper()
    if not query_upper.startswith("INSERT"):
        json_output({
            "error": "Only INSERT queries allowed with this tool",
            "success": False
        })
        sys.exit(1)

    db = DatabaseConnection()

    try:
        result = db.execute_mutation(query)
        success_output(
            data=result,
            message=f"Inserted {result['rows_affected']} row(s)"
        )

    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Execute INSERT query")
    parser.add_argument("--query", required=True, help="SQL INSERT query")
    args = parser.parse_args()

    execute_insert(args.query)
