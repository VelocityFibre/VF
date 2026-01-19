#!/bin/bash
# Quick test of database-operations skill scripts
# Run this to verify all scripts work correctly

echo "=== Testing Database Operations Skill ==="
echo ""

# Check environment
if [ -z "$NEON_DATABASE_URL" ]; then
    echo "❌ Error: NEON_DATABASE_URL not set"
    echo "Run: export NEON_DATABASE_URL='postgresql://...'"
    exit 1
fi

echo "✓ NEON_DATABASE_URL is set"
echo ""

# Test 1: List tables
echo "Test 1: List tables"
./list_tables.py | head -20
echo ""

# Test 2: Describe contractors table
echo "Test 2: Describe contractors table"
./describe_table.py --table contractors | head -30
echo ""

# Test 3: Get table stats
echo "Test 3: Get contractors table stats"
./table_stats.py --table contractors
echo ""

# Test 4: Execute query
echo "Test 4: Count contractors"
./execute_query.py --query "SELECT COUNT(*) as count FROM contractors"
echo ""

echo "=== All Tests Complete ==="
