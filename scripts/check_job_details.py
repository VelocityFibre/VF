#!/usr/bin/env python3
"""
Check detailed output of failed packaging job
"""
import psycopg2

DB_CONFIG = {
    'host': '100.96.203.105',
    'port': 5433,
    'database': 'qfieldcloud_db',
    'user': 'qfieldcloud_db_admin',
    'password': 'c6ce1f02f798c5776fee9e6857f628ff775c75e5eb3b7753'
}

JOB_ID = '6bf843f4-31c1-46aa-97f7-3ff99371aa53'  # Most recent failed package job

def main():
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    cur.execute("""
        SELECT
            id,
            type,
            status,
            created_at,
            updated_at,
            started_at,
            finished_at,
            output,
            feedback
        FROM core_job
        WHERE id = %s
    """, (JOB_ID,))

    result = cur.fetchone()
    if result:
        job_id, job_type, status, created, updated, started, finished, output, feedback = result
        print(f"Job: {job_id}")
        print(f"Type: {job_type}")
        print(f"Status: {status}")
        print(f"Created: {created}")
        print(f"Updated: {updated}")
        print(f"\nOutput:")
        print(output if output else "None")

    cur.close()
    conn.close()

if __name__ == '__main__':
    main()
