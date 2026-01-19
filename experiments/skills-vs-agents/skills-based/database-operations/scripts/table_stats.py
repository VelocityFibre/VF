#!/usr/bin/env python3
"""
Get statistics for a table (row count, size).
"""

import sys
import argparse
from pathlib import Path

# Add scripts dir to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from db_utils import DatabaseConnection, success_output


def get_table_stats(table_name: str):
    """
    Get statistics for a table.

    Args:
        table_name: Name of the table
    """
    db = DatabaseConnection()

    try:
        # Get row count
        count_query = f"SELECT COUNT(*) as count FROM {table_name};"
        count_result = db.execute_query(count_query)

        # Get table size
        size_query = """
            SELECT
                pg_size_pretty(pg_total_relation_size(%s)) as total_size,
                pg_size_pretty(pg_relation_size(%s)) as table_size,
                pg_size_pretty(pg_indexes_size(%s)) as indexes_size
        """
        size_result = db.execute_query(size_query, (table_name, table_name, table_name))

        stats = {
            "table_name": table_name,
            "row_count": count_result[0]["count"] if count_result else 0,
            "total_size": size_result[0]["total_size"] if size_result else "Unknown",
            "table_size": size_result[0]["table_size"] if size_result else "Unknown",
            "indexes_size": size_result[0]["indexes_size"] if size_result else "Unknown"
        }

        success_output(data=stats, message=f"Statistics for '{table_name}'")

    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Get table statistics")
    parser.add_argument("--table", required=True, help="Name of the table")
    args = parser.parse_args()

    get_table_stats(args.table)
