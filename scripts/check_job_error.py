#!/usr/bin/env python3
"""
Check the END of failed packaging job output for errors
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
        SELECT output
        FROM core_job
        WHERE id = %s
    """, (JOB_ID,))

    result = cur.fetchone()
    if result and result[0]:
        output = result[0]
        lines = output.split('\n')

        # Show last 50 lines
        print("LAST 50 LINES OF JOB OUTPUT:")
        print("=" * 100)
        for line in lines[-50:]:
            print(line)

    cur.close()
    conn.close()

if __name__ == '__main__':
    main()
