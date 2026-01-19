#!/usr/bin/env python3
"""
Describe table schema in detail.
Shows columns, data types, constraints, nullability.
"""

import sys
import argparse
from pathlib import Path

# Add scripts dir to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from db_utils import DatabaseConnection, success_output


def describe_table(table_name: str):
    """
    Get detailed schema information for a table.

    Args:
        table_name: Name of the table to describe
    """
    db = DatabaseConnection()

    query = """
        SELECT
            column_name,
            data_type,
            character_maximum_length,
            is_nullable,
            column_default
        FROM information_schema.columns
        WHERE table_schema = 'public'
          AND table_name = %s
        ORDER BY ordinal_position;
    """

    try:
        results = db.execute_query(query, (table_name,))

        if not results:
            success_output(
                data=[],
                message=f"Table '{table_name}' not found or has no columns"
            )
        else:
            success_output(
                data={
                    "table_name": table_name,
                    "columns": results,
                    "column_count": len(results)
                },
                message=f"Table '{table_name}' has {len(results)} columns"
            )
    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Describe table schema")
    parser.add_argument("--table", required=True, help="Name of the table")
    args = parser.parse_args()

    describe_table(args.table)
