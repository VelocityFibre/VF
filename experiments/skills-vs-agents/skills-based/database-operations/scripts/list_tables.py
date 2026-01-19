#!/usr/bin/env python3
"""
List all tables in the database.
Returns table names and types as JSON.
"""

import sys
from pathlib import Path

# Add scripts dir to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from db_utils import DatabaseConnection, success_output


def list_tables():
    """List all tables in public schema."""
    db = DatabaseConnection()

    query = """
        SELECT
            table_name,
            table_type
        FROM information_schema.tables
        WHERE table_schema = 'public'
        ORDER BY table_name;
    """

    try:
        results = db.execute_query(query)
        success_output(
            data=results,
            message=f"Found {len(results)} tables"
        )
    finally:
        db.close()


if __name__ == "__main__":
    list_tables()
