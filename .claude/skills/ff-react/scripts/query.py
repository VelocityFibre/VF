#!/home/louisdup/Agents/claude/venv/bin/python3
"""
FF_React Database Query Tool
Query FF_React specific database tables
"""

import os
import sys
import json
import argparse
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime, timedelta
from tabulate import tabulate

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

class FFReactDatabase:
    def __init__(self):
        # Get database URL from environment
        self.db_url = os.getenv('FF_REACT_DB_URL', os.getenv('NEON_DATABASE_URL'))
        if not self.db_url:
            self.db_url = "postgresql://neondb_owner:npg_aRNLhZc1G2CD@ep-dry-night-a9qyh4sj-pooler.gwc.azure.neon.tech/neondb?sslmode=require"

        # Common FF_React tables
        self.tables = {
            'contractors': 'Contractor information',
            'projects': 'Project details',
            'drops': 'SOW drop points from Excel imports',
            'qa_photo_reviews': 'WhatsApp QA photo review data',
            'fibre': 'Fiber cable segments',
            'poles': 'Pole infrastructure',
            'action_items': 'Meeting action items',
            'meetings': 'Meeting records',
            'users': 'Application users',
            'client_contractors': 'Client-contractor relationships'
        }

    def get_connection(self):
        """Create database connection"""
        try:
            return psycopg2.connect(self.db_url)
        except Exception as e:
            print(f"❌ Failed to connect to database: {e}")
            sys.exit(1)

    def list_tables(self):
        """List all FF_React related tables"""
        print("\n📊 FF_React Database Tables")
        print("=" * 60)

        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT tablename,
                           pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size,
                           n_live_tup as row_count
                    FROM pg_tables t
                    LEFT JOIN pg_stat_user_tables s ON t.tablename = s.relname
                    WHERE schemaname = 'public'
                    ORDER BY tablename
                """)

                tables = cur.fetchall()

                print(f"\nFound {len(tables)} tables:\n")

                for table, size, rows in tables:
                    description = self.tables.get(table, '')
                    # Highlight FF_React specific tables
                    if table in self.tables:
                        print(f"  ⭐ {table:30} {size:10} {rows or 0:8,} rows  {description}")
                    else:
                        print(f"     {table:30} {size:10} {rows or 0:8,} rows")

    def query_table(self, table_name, limit=20, where=None, order_by=None):
        """Query a specific table"""
        print(f"\n📋 Querying table: {table_name}")
        print("=" * 60)

        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                # Build query
                query = f"SELECT * FROM {table_name}"

                if where:
                    query += f" WHERE {where}"

                if order_by:
                    query += f" ORDER BY {order_by}"
                else:
                    # Default ordering for common tables
                    if table_name == 'qa_photo_reviews':
                        query += " ORDER BY upload_time DESC"
                    elif table_name in ['drops', 'fibre', 'poles']:
                        query += " ORDER BY created_at DESC"
                    elif table_name == 'contractors':
                        query += " ORDER BY name"

                query += f" LIMIT {limit}"

                try:
                    cur.execute(query)
                    results = cur.fetchall()

                    if results:
                        # Convert to list of dicts for tabulate
                        headers = results[0].keys()
                        rows = [list(row.values()) for row in results]

                        # Truncate long values for display
                        rows = [[str(val)[:50] + '...' if isinstance(val, str) and len(str(val)) > 50 else val
                                for val in row] for row in rows]

                        print(tabulate(rows, headers=headers, tablefmt='grid'))
                        print(f"\n✅ Showing {len(results)} of {limit} requested rows")
                    else:
                        print("No results found")

                except Exception as e:
                    print(f"❌ Query failed: {e}")

    def custom_query(self, sql_query):
        """Execute custom SQL query"""
        print("\n🔍 Executing custom query")
        print("=" * 60)

        # Safety check - only allow SELECT queries
        if not sql_query.strip().upper().startswith('SELECT'):
            print("❌ Only SELECT queries are allowed")
            return

        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                try:
                    cur.execute(sql_query)
                    results = cur.fetchall()

                    if results:
                        headers = results[0].keys()
                        rows = [list(row.values()) for row in results]

                        # Truncate long values
                        rows = [[str(val)[:100] + '...' if isinstance(val, str) and len(str(val)) > 100 else val
                                for val in row] for row in rows]

                        print(tabulate(rows, headers=headers, tablefmt='grid'))
                        print(f"\n✅ Query returned {len(results)} rows")
                    else:
                        print("No results found")

                except Exception as e:
                    print(f"❌ Query failed: {e}")

    def get_stats(self, table_name):
        """Get statistics for a table"""
        print(f"\n📊 Statistics for table: {table_name}")
        print("=" * 60)

        with self.get_connection() as conn:
            with conn.cursor() as cur:
                # Row count
                cur.execute(f"SELECT COUNT(*) FROM {table_name}")
                count = cur.fetchone()[0]
                print(f"Total rows: {count:,}")

                # Table size
                cur.execute(f"""
                    SELECT pg_size_pretty(pg_total_relation_size('{table_name}'))
                """)
                size = cur.fetchone()[0]
                print(f"Table size: {size}")

                # Get column info
                cur.execute(f"""
                    SELECT column_name, data_type, is_nullable
                    FROM information_schema.columns
                    WHERE table_name = '{table_name}'
                    ORDER BY ordinal_position
                """)
                columns = cur.fetchall()

                print(f"\nColumns ({len(columns)}):")
                for col_name, data_type, nullable in columns:
                    null_str = "NULL" if nullable == 'YES' else "NOT NULL"
                    print(f"  • {col_name:30} {data_type:20} {null_str}")

    def recent_activity(self, hours=24):
        """Show recent activity across key tables"""
        print(f"\n🕐 Recent Activity (last {hours} hours)")
        print("=" * 60)

        with self.get_connection() as conn:
            with conn.cursor() as cur:
                # Check qa_photo_reviews
                cur.execute(f"""
                    SELECT COUNT(*), project
                    FROM qa_photo_reviews
                    WHERE upload_time > NOW() - INTERVAL '{hours} hours'
                    GROUP BY project
                    ORDER BY COUNT(*) DESC
                """)
                qa_results = cur.fetchall()

                if qa_results:
                    print("\n📸 QA Photo Reviews:")
                    for count, project in qa_results:
                        print(f"  • {project}: {count} photos")

                # Check recent drops
                cur.execute(f"""
                    SELECT COUNT(*), project_id
                    FROM drops
                    WHERE created_at > NOW() - INTERVAL '{hours} hours'
                    GROUP BY project_id
                    LIMIT 5
                """)
                drop_results = cur.fetchall()

                if drop_results:
                    print("\n📍 Drop Points Added:")
                    for count, project_id in drop_results:
                        print(f"  • Project {project_id[:8]}...: {count} drops")

                # Check action items
                cur.execute(f"""
                    SELECT COUNT(*), status
                    FROM action_items
                    WHERE created_at > NOW() - INTERVAL '{hours} hours'
                    GROUP BY status
                """)
                action_results = cur.fetchall()

                if action_results:
                    print("\n📝 Action Items:")
                    for count, status in action_results:
                        print(f"  • {status}: {count} items")

def main():
    parser = argparse.ArgumentParser(description='Query FF_React database')
    parser.add_argument('--list-tables', action='store_true', help='List all tables')
    parser.add_argument('--table', help='Table name to query')
    parser.add_argument('--limit', type=int, default=20, help='Number of rows to return')
    parser.add_argument('--where', help='WHERE clause for filtering')
    parser.add_argument('--order-by', help='ORDER BY clause')
    parser.add_argument('--query', help='Custom SQL query (SELECT only)')
    parser.add_argument('--stats', help='Get statistics for a table')
    parser.add_argument('--recent', action='store_true', help='Show recent activity')
    parser.add_argument('--hours', type=int, default=24, help='Hours for recent activity')

    args = parser.parse_args()

    db = FFReactDatabase()

    if args.list_tables:
        db.list_tables()
    elif args.table:
        db.query_table(args.table, args.limit, args.where, args.order_by)
    elif args.query:
        db.custom_query(args.query)
    elif args.stats:
        db.get_stats(args.stats)
    elif args.recent:
        db.recent_activity(args.hours)
    else:
        # Default action - show summary
        print("\n🎯 FF_React Database Query Tool")
        print("\nQuick examples:")
        print("  ./query.py --list-tables")
        print("  ./query.py --table contractors --limit 10")
        print("  ./query.py --table qa_photo_reviews --where \"project='Lawley'\"")
        print("  ./query.py --stats drops")
        print("  ./query.py --recent --hours 48")
        print("\nUse --help for all options")

if __name__ == '__main__':
    main()