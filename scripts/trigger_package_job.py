#!/usr/bin/env python3
"""
Trigger a package job for Mohadin's project
"""
import psycopg2
import uuid
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

    # Get project details
    cur.execute("""
        SELECT name, owner_id
        FROM core_project
        WHERE id = %s
    """, (PROJECT_ID,))

    result = cur.fetchone()
    if not result:
        print("Project not found!")
        return

    project_name, owner_id = result
    print(f"Project: {project_name}")
    print(f"Owner ID: {owner_id}")

    # Get project file (QGIS file)
    cur.execute("""
        SELECT name
        FROM filestorage_file
        WHERE project_id = %s
        AND (name LIKE '%.qgs' OR name LIKE '%.qgz')
        ORDER BY name
        LIMIT 1
    """, (PROJECT_ID,))

    qgis_file = cur.fetchone()
    if not qgis_file:
        print("No QGIS project file found!")
        return

    qgis_filename = qgis_file[0]
    print(f"QGIS file: {qgis_filename}")

    # Create package job
    job_id = str(uuid.uuid4())
    now = datetime.utcnow()

    print(f"\nCreating package job: {job_id}")

    cur.execute("""
        INSERT INTO core_job (
            id,
            type,
            status,
            project_id,
            created_by_id,
            created_at,
            updated_at
        ) VALUES (
            %s,
            'package',
            'pending',
            %s,
            %s,
            %s,
            %s
        )
    """, (job_id, PROJECT_ID, owner_id, now, now))

    conn.commit()
    print("✅ Package job created!")
    print("\nMonitor status with:")
    print(f"  SELECT status FROM core_job WHERE id = '{job_id}'")

    cur.close()
    conn.close()

if __name__ == '__main__':
    main()
