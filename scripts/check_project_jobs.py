#!/usr/bin/env python3
"""
Check QFieldCloud jobs for project to see if packaging is needed
"""
import psycopg2
from datetime import datetime

DB_CONFIG = {
    'host': '100.96.203.105',
    'port': 5433,
    'database': 'qfieldcloud_db',
    'user': 'qfieldcloud_db_admin',
    'password': 'c6ce1f02f798c5776fee9e6857f628ff775c75e5eb3b7753'
}

PROJECT_ID = '137eb5ec-4c0b-4eab-8a5c-de046eb06349'

def main():
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    # Check recent jobs
    print("Recent jobs for project:")
    print("=" * 100)
    cur.execute("""
        SELECT
            id,
            type,
            status,
            created_at,
            updated_at,
            output
        FROM core_job
        WHERE project_id = %s
        ORDER BY created_at DESC
        LIMIT 10
    """, (PROJECT_ID,))

    jobs = cur.fetchall()

    if not jobs:
        print("No jobs found")
    else:
        for job_id, job_type, status, created, updated, output in jobs:
            print(f"\nJob ID: {job_id}")
            print(f"  Type: {job_type}")
            print(f"  Status: {status}")
            print(f"  Created: {created}")
            print(f"  Updated: {updated}")
            if output:
                print(f"  Output: {output[:200]}")

    # Check if any jobs are pending/running
    print("\n" + "=" * 100)
    print("Pending/Running jobs:")
    cur.execute("""
        SELECT COUNT(*), status
        FROM core_job
        WHERE project_id = %s
        AND status IN ('pending', 'queued', 'started')
        GROUP BY status
    """, (PROJECT_ID,))

    pending = cur.fetchall()
    if pending:
        for count, status in pending:
            print(f"  {status}: {count} jobs")
    else:
        print("  None")

    # Check project data last updated
    print("\n" + "=" * 100)
    print("Project info:")
    cur.execute("""
        SELECT
            name,
            updated_at,
            file_storage_bytes
        FROM core_project
        WHERE id = %s
    """, (PROJECT_ID,))

    result = cur.fetchone()
    if result:
        name, updated, storage = result
        print(f"  Name: {name}")
        print(f"  Updated: {updated}")
        print(f"  Storage: {storage / 1024 / 1024:.1f} MB")

    cur.close()
    conn.close()

if __name__ == '__main__':
    main()
