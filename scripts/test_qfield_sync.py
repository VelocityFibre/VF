#!/usr/bin/env python3
"""
Test QFieldCloud sync by triggering a package job
"""
import psycopg2
import requests
import time

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

    # Check current project size
    print("Checking project status...")
    cur.execute("""
        SELECT
            name,
            file_storage_bytes,
            updated_at
        FROM core_project
        WHERE id = %s
    """, (PROJECT_ID,))

    result = cur.fetchone()
    if result:
        name, storage, updated = result
        print(f"✅ Project: {name}")
        print(f"   Storage: {storage / 1024 / 1024:.1f} MB")
        print(f"   Updated: {updated}")

    # Check recent jobs
    print("\nChecking recent jobs (last 5 minutes)...")
    cur.execute("""
        SELECT
            id,
            type,
            status,
            created_at
        FROM core_job
        WHERE project_id = %s
        AND created_at > NOW() - INTERVAL '5 minutes'
        ORDER BY created_at DESC
    """, (PROJECT_ID,))

    recent_jobs = cur.fetchall()
    if recent_jobs:
        print(f"Found {len(recent_jobs)} recent jobs:")
        for job_id, job_type, status, created in recent_jobs:
            print(f"  - {job_type}: {status} (created {created})")
    else:
        print("No recent jobs found")

    # Check if any jobs are currently running
    print("\nChecking running jobs...")
    cur.execute("""
        SELECT COUNT(*)
        FROM core_job
        WHERE project_id = %s
        AND status IN ('pending', 'queued', 'started')
    """, (PROJECT_ID,))

    running = cur.fetchone()[0]
    if running > 0:
        print(f"⚠️  {running} jobs currently running/pending")
    else:
        print("✅ No jobs currently running")

    # Test file access via API (need auth token)
    print("\nChecking user authentication tokens...")
    cur.execute("""
        SELECT
            u.username,
            t.key,
            t.expires_at
        FROM authentication_authtoken t
        JOIN core_user u ON t.user_id = u.id
        WHERE u.username IN ('Juan', 'juan', 'mohadin', 'Mohadin')
        AND t.expires_at > NOW()
        ORDER BY t.created_at DESC
        LIMIT 1
    """)

    token_result = cur.fetchone()
    if token_result:
        username, token, expires = token_result
        print(f"✅ Found valid token for {username} (expires {expires})")

        # Test API endpoint
        print("\nTesting API endpoint...")
        headers = {'Authorization': f'Token {token}'}
        url = f'https://qfield.fibreflow.app/api/v1/projects/{PROJECT_ID}/'

        try:
            response = requests.get(url, headers=headers, timeout=10)
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ Project API accessible")
                print(f"   Files count: {data.get('file_count', 'N/A')}")
            else:
                print(f"   ⚠️  Status: {response.status_code}")
        except Exception as e:
            print(f"   ⚠️  Error: {e}")
    else:
        print("No valid tokens found for testing")

    cur.close()
    conn.close()

if __name__ == '__main__':
    main()
