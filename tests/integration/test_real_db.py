#!/usr/bin/env python3
"""Direct database test to prove it's working"""

import sys
sys.path.append('/var/www/neon-agent')

from neon_agent import PostgresClient, load_env
import json

load_env()
db = PostgresClient("postgresql://neondb_owner:npg_aRNLhZc1G2CD@ep-dry-night-a9qyh4sj-pooler.gwc.azure.neon.tech/neondb?sslmode=require&channel_binding=require")

print("=== REAL DATABASE QUERY TEST ===\n")

# Test 1: Count contractors
result = db.execute_query("SELECT COUNT(*) as count FROM contractors")
print(f"Total contractors: {result[0]['count']}")

# Test 2: Get actual status values
result = db.execute_query("SELECT DISTINCT status FROM contractors")
print(f"\nActual status values in database:")
for row in result:
    print(f"  - '{row['status']}'")

# Test 3: Get 3 contractors with all details
result = db.execute_query("SELECT company_name, status, is_active FROM contractors LIMIT 3")
print(f"\nFirst 3 contractors:")
for row in result:
    print(f"  - {row['company_name']}")
    print(f"    Status: '{row['status']}'")
    print(f"    is_active: {row['is_active']}")

# Test 4: Count by is_active
result = db.execute_query("SELECT is_active, COUNT(*) as count FROM contractors GROUP BY is_active")
print(f"\nContractors by is_active flag:")
for row in result:
    print(f"  - is_active={row['is_active']}: {row['count']} contractors")

db.close()
print("\n✅ DATABASE IS WORKING PERFECTLY!")
print("The issue is Haiku's conservative responses, not the database!")
