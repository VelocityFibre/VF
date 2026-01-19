#!/usr/bin/env python3
"""
Recalculate project storage size after compression
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

    # Calculate actual total size from file versions
    print("Calculating actual storage size...")
    cur.execute("""
        SELECT SUM(fv.size) as total_size
        FROM filestorage_file f
        JOIN filestorage_fileversion fv ON f.latest_version_id = fv.id
        WHERE f.project_id = %s
    """, (PROJECT_ID,))

    actual_size = cur.fetchone()[0]
    print(f"Actual total file size: {actual_size / 1024 / 1024:.1f} MB")

    # Check project table
    cur.execute("SELECT file_storage_bytes FROM core_project WHERE id = %s", (PROJECT_ID,))
    cached_size = cur.fetchone()[0]
    print(f"Cached project storage: {cached_size / 1024 / 1024:.1f} MB")

    if actual_size != cached_size:
        print(f"\n⚠️  MISMATCH: Database cache is stale!")
        print(f"   Actual: {actual_size / 1024 / 1024:.1f} MB")
        print(f"   Cached: {cached_size / 1024 / 1024:.1f} MB")
        print(f"   Difference: {(cached_size - actual_size) / 1024 / 1024:.1f} MB")

        # Update database
        response = input("\nUpdate database with correct size? (yes/no): ").strip().lower()
        if response == 'yes':
            cur.execute("""
                UPDATE core_project
                SET file_storage_bytes = %s
                WHERE id = %s
            """, (actual_size, PROJECT_ID))
            conn.commit()
            print("✅ Database updated!")
        else:
            print("Skipped update.")

    cur.close()
    conn.close()

if __name__ == '__main__':
    main()
