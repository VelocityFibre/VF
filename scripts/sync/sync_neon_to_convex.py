#!/usr/bin/env python3
"""
Sync Neon PostgreSQL data to Convex
Simple Python version using requests
"""

import sys
import os
import psycopg2
from psycopg2.extras import RealDictCursor
import requests
import json

# Configuration
NEON_URL = "postgresql://neondb_owner:npg_aRNLhZc1G2CD@ep-dry-night-a9qyh4sj-pooler.gwc.azure.neon.tech/neondb?sslmode=require&channel_binding=require"
CONVEX_URL = "https://quixotic-crow-802.convex.cloud"

def call_convex_mutation(function_path, args):
    """Call a Convex mutation"""
    url = f"{CONVEX_URL}/api/mutation"
    payload = {
        "path": function_path,
        "args": args
    }

    try:
        response = requests.post(url, json=payload, timeout=30)
        result = response.json()

        if result.get("status") == "error":
            return {"error": result.get("errorMessage", "Unknown error")}

        return result.get("value")
    except Exception as e:
        return {"error": str(e)}


def sync_contractors():
    """Sync contractors from Neon to Convex"""
    print("\n📋 Syncing Contractors...")

    conn = psycopg2.connect(NEON_URL)

    with conn.cursor(cursor_factory=RealDictCursor) as cursor:
        cursor.execute("""
            SELECT
                id,
                company_name,
                status,
                is_active,
                email,
                phone
            FROM contractors
            WHERE is_active = true
            ORDER BY company_name
        """)
        contractors = cursor.fetchall()

    print(f"   Found {len(contractors)} active contractors in Neon")

    synced = 0
    failed = 0

    for contractor in contractors:
        result = call_convex_mutation("contractors:create", {
            "company_name": contractor["company_name"],
            "status": contractor["status"],
            "is_active": contractor["is_active"],
            "email": contractor["email"],
            "phone": contractor["phone"],
            "neon_id": str(contractor["id"])
        })

        if isinstance(result, dict) and "error" in result:
            print(f"\n   ❌ {contractor['company_name']}: {result['error']}")
            failed += 1
        else:
            synced += 1
            print(f"\r   Synced: {synced}/{len(contractors)}", end="", flush=True)

    print(f"\n   ✅ Synced {synced} contractors ({failed} failed)")
    conn.close()
    return synced, failed


def sync_projects():
    """Sync projects from Neon to Convex"""
    print("\n📁 Syncing Projects...")

    conn = psycopg2.connect(NEON_URL)

    with conn.cursor(cursor_factory=RealDictCursor) as cursor:
        cursor.execute("""
            SELECT
                id,
                project_name,
                description,
                status
            FROM projects
            WHERE status = 'active'
            ORDER BY project_name
        """)
        projects = cursor.fetchall()

    print(f"   Found {len(projects)} active projects in Neon")

    synced = 0
    failed = 0

    for project in projects:
        result = call_convex_mutation("projects:create", {
            "name": project["project_name"],
            "description": project["description"],
            "status": project["status"],
            "neon_id": str(project["id"])
        })

        if isinstance(result, dict) and "error" in result:
            print(f"\n   ❌ {project['project_name']}: {result['error']}")
            failed += 1
        else:
            synced += 1
            print(f"\r   Synced: {synced}/{len(projects)}", end="", flush=True)

    print(f"\n   ✅ Synced {synced} projects ({failed} failed)")
    conn.close()
    return synced, failed


def main():
    print("=" * 60)
    print("🔄 Neon → Convex Sync (Python)")
    print("=" * 60)
    print(f"\n📊 Neon:   {NEON_URL.split('@')[1].split('/')[0]}")
    print(f"🌐 Convex: {CONVEX_URL}")

    try:
        c_synced, c_failed = sync_contractors()
        p_synced, p_failed = sync_projects()

        print("\n" + "=" * 60)
        print(f"✅ Sync Complete!")
        print(f"   Contractors: {c_synced} synced, {c_failed} failed")
        print(f"   Projects: {p_synced} synced, {p_failed} failed")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ Sync failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
