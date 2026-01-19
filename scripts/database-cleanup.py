#!/usr/bin/env python3
"""
Database Data Retention Cleanup Job
Removes old records from audit/log tables to prevent unbounded growth

Based on recommendations from DATABASE_AUDIT.md

Usage:
  ./scripts/database-cleanup.py --dry-run  # Preview what would be deleted
  ./scripts/database-cleanup.py            # Actually delete old records

Cron setup:
  0 2 * * 0  cd /home/louisdup/Agents/claude && ./venv/bin/python3 scripts/database-cleanup.py >> logs/database-cleanup.log 2>&1
  (Runs every Sunday at 2 AM)
"""

import os
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
import argparse

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import psycopg2
from urllib.parse import urlparse


def load_env():
    """Load environment variables from .env file"""
    env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    if key not in os.environ:  # Don't override existing env vars
                        os.environ[key] = value


def get_connection():
    """Get database connection using psycopg2"""
    # Try to load from .env if not already set
    if 'NEON_DATABASE_URL' not in os.environ:
        load_env()

    db_url = os.getenv('NEON_DATABASE_URL')
    if not db_url:
        raise ValueError("NEON_DATABASE_URL not set in environment or .env file")

    result = urlparse(db_url)
    return psycopg2.connect(
        database=result.path[1:],
        user=result.username,
        password=result.password,
        host=result.hostname,
        port=result.port or 5432,
        sslmode='require'
    )

# Retention policies (days)
RETENTION_POLICIES = {
    'qcontact_sync_log': {
        'days': 90,
        'date_column': 'synced_at',
        'description': 'QContact sync audit log',
        'priority': 'HIGH'
    },
    'qfield_sync_jobs': {
        'days': 30,
        'date_column': 'completed_at',
        'description': 'QField sync job history',
        'priority': 'HIGH',
        'where_clause': "status = 'completed'"  # Only delete completed jobs
    },
    'whatsapp_notifications': {
        'days': 30,
        'date_column': 'sent_at',
        'description': 'WhatsApp delivery confirmations',
        'priority': 'MEDIUM'
    },
    'ticket_attachments': {
        'days': 180,  # 6 months
        'date_column': 'uploaded_at',
        'description': 'Ticket attachment metadata (files stay on storage)',
        'priority': 'LOW',
        'where_clause': "ticket_id NOT IN (SELECT id FROM tickets WHERE status != 'closed')"
    }
}

# Tables to NEVER clean up (permanent audit trail)
PROTECTED_TABLES = [
    'handover_snapshots',  # Immutable audit trail
    'tickets',             # Core business data
    'projects',            # Core business data
    'contractors',         # Core business data
]


def get_cleanup_stats(conn, dry_run: bool = True) -> List[Dict]:
    """
    Analyze tables and return cleanup statistics

    Args:
        conn: Database connection
        dry_run: If True, only count records, don't delete

    Returns:
        List of dicts with cleanup stats per table
    """
    stats = []
    cursor = conn.cursor()

    for table_name, policy in RETENTION_POLICIES.items():
        cutoff_date = datetime.now() - timedelta(days=policy['days'])
        date_column = policy['date_column']
        where_clause = policy.get('where_clause', '1=1')

        # Check if table exists
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_name = %s
            )
        """, (table_name,))

        if not cursor.fetchone()[0]:
            stats.append({
                'table': table_name,
                'status': 'SKIP',
                'reason': 'Table does not exist',
                'count': 0
            })
            continue

        # Check if date column exists
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.columns
                WHERE table_name = %s AND column_name = %s
            )
        """, (table_name, date_column))

        if not cursor.fetchone()[0]:
            stats.append({
                'table': table_name,
                'status': 'SKIP',
                'reason': f'Column {date_column} does not exist',
                'count': 0
            })
            continue

        # Count records to be deleted
        query = f"""
            SELECT COUNT(*) FROM {table_name}
            WHERE {date_column} < %s AND ({where_clause})
        """

        try:
            cursor.execute(query, (cutoff_date,))
            count = cursor.fetchone()[0]

            stats.append({
                'table': table_name,
                'status': 'READY' if count > 0 else 'CLEAN',
                'count': count,
                'cutoff_date': cutoff_date,
                'retention_days': policy['days'],
                'description': policy['description'],
                'priority': policy['priority']
            })
        except Exception as e:
            stats.append({
                'table': table_name,
                'status': 'ERROR',
                'reason': str(e),
                'count': 0
            })

    cursor.close()
    return stats


def cleanup_table(conn, table_name: str, policy: Dict, dry_run: bool = False) -> Tuple[int, str]:
    """
    Clean up old records from a single table

    Returns:
        (rows_deleted, status_message)
    """
    cutoff_date = datetime.now() - timedelta(days=policy['days'])
    date_column = policy['date_column']
    where_clause = policy.get('where_clause', '1=1')

    cursor = conn.cursor()

    # Build DELETE query
    query = f"""
        DELETE FROM {table_name}
        WHERE {date_column} < %s AND ({where_clause})
    """

    try:
        if dry_run:
            # Just count
            count_query = f"""
                SELECT COUNT(*) FROM {table_name}
                WHERE {date_column} < %s AND ({where_clause})
            """
            cursor.execute(count_query, (cutoff_date,))
            count = cursor.fetchone()[0]
            message = f"Would delete {count} records"
        else:
            # Actually delete
            cursor.execute(query, (cutoff_date,))
            count = cursor.rowcount
            conn.commit()
            message = f"Deleted {count} records"

        cursor.close()
        return count, message

    except Exception as e:
        conn.rollback()
        cursor.close()
        return 0, f"ERROR: {str(e)}"


def main():
    parser = argparse.ArgumentParser(description='Clean up old database records')
    parser.add_argument('--dry-run', action='store_true',
                       help='Preview changes without deleting')
    parser.add_argument('--table', type=str,
                       help='Only clean specific table')
    parser.add_argument('--force', action='store_true',
                       help='Skip confirmation prompt')
    args = parser.parse_args()

    print(f"\n{'='*80}")
    print(f"🗑️  DATABASE CLEANUP JOB - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*80}\n")

    if args.dry_run:
        print("🔍 DRY RUN MODE - No data will be deleted\n")

    # Get database connection
    try:
        conn = get_connection()
        print("✅ Connected to database\n")
    except Exception as e:
        print(f"❌ Failed to connect to database: {e}")
        return 1

    # Get cleanup statistics
    stats = get_cleanup_stats(conn, dry_run=args.dry_run)

    # Print summary table
    print(f"{'Table':<30} {'Status':<10} {'Count':<10} {'Retention':<15} {'Priority':<10}")
    print(f"{'-'*80}")

    total_to_delete = 0
    tables_to_clean = []

    for stat in stats:
        table = stat['table']
        status = stat['status']
        count = stat.get('count', 0)
        retention = f"{stat.get('retention_days', 0)} days" if 'retention_days' in stat else 'N/A'
        priority = stat.get('priority', 'N/A')

        # Filter by table if specified
        if args.table and table != args.table:
            continue

        status_icon = {
            'READY': '🔴',
            'CLEAN': '✅',
            'SKIP': '⚠️',
            'ERROR': '❌'
        }.get(status, '❓')

        print(f"{table:<30} {status_icon} {status:<8} {count:<10} {retention:<15} {priority:<10}")

        if status == 'READY':
            total_to_delete += count
            tables_to_clean.append(table)

        if status in ['SKIP', 'ERROR'] and 'reason' in stat:
            print(f"  └─ {stat['reason']}")

    print(f"\n{'='*80}")
    print(f"Total records to delete: {total_to_delete:,}")
    print(f"Tables to clean: {len(tables_to_clean)}")
    print(f"{'='*80}\n")

    # Confirm before deleting
    if not args.dry_run and total_to_delete > 0:
        if not args.force:
            response = input(f"⚠️  Delete {total_to_delete:,} records? (yes/no): ")
            if response.lower() != 'yes':
                print("❌ Cleanup cancelled")
                conn.close()
                return 0

        # Perform cleanup
        print("\n🗑️  Cleaning up...\n")
        for table_name in tables_to_clean:
            policy = RETENTION_POLICIES[table_name]
            count, message = cleanup_table(conn, table_name, policy, dry_run=False)
            print(f"  {table_name}: {message}")

        print("\n✅ Cleanup complete!\n")

    conn.close()
    return 0


if __name__ == '__main__':
    sys.exit(main())
