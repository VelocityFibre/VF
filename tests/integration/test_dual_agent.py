#!/usr/bin/env python3
"""Quick test of dual database agent"""

import sys
sys.path.append('ui-module')

from dual_agent import DualDatabaseAgent, load_env

load_env()

print("\n" + "="*60)
print("DUAL DATABASE AGENT TEST")
print("="*60)

agent = DualDatabaseAgent()

print("\n📊 Testing NEON PostgreSQL...")
print("-"*60)
try:
    response = agent.chat("How many contractors are in the database?", database="neon")
    print(response)
    print("\n✅ Neon query successful!")
except Exception as e:
    print(f"\n❌ Neon error: {e}")

print("\n" + "="*60)
print("📊 Testing CONVEX...")
print("-"*60)
try:
    response = agent.chat("List all contractors", database="convex")
    print(response)
    print("\n✅ Convex query successful!")
except Exception as e:
    print(f"\n❌ Convex error: {e}")

print("\n" + "="*60)
print("✅ DUAL AGENT TEST COMPLETE")
print("="*60)

agent.close()
