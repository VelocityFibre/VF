#!/usr/bin/env python3
"""
Find QGIS project file for Mohadin's project
"""
import psycopg2

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

    # Get all files
    cur.execute("""
        SELECT name, size
        FROM filestorage_file f
        JOIN filestorage_fileversion fv ON f.latest_version_id = fv.id
        WHERE project_id = %s
        AND name NOT LIKE '%/%'
        ORDER BY name
    """, (PROJECT_ID,))

    files = cur.fetchall()
    print(f"Found {len(files)} files in project root:")
    for name, size in files:
        print(f"  {name} ({size / 1024:.1f} KB)")

    cur.close()
    conn.close()

if __name__ == '__main__':
    main()
