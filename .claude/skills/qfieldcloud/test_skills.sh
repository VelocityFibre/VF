#!/bin/bash
# QFieldCloud Sub-Skills Test Suite
# This script tests all sub-skills by running them on the VF Server

SSH_KEY="$HOME/.ssh/vf_server_key"
VF_SERVER="velo@100.96.203.105"

echo "================================================"
echo "QFieldCloud Sub-Skills Test Suite"
echo "================================================"
echo ""

# Function to run remote script
run_remote() {
    local skill=$1
    local script=$2
    local description=$3

    echo "Testing: $description"
    echo "----------------------------------------"

    # Copy the script to the server
    scp -i "$SSH_KEY" -q ".claude/skills/qfieldcloud/sub-skills/$skill/scripts/$script" "$VF_SERVER:/tmp/$script" 2>/dev/null

    # Run it
    ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no "$VF_SERVER" "chmod +x /tmp/$script && /tmp/$script"

    local exit_code=$?

    if [ $exit_code -eq 0 ]; then
        echo "✅ PASSED"
    else
        echo "❌ FAILED (exit code: $exit_code)"
    fi

    echo ""
    return $exit_code
}

# Test 1: Monitoring - Quick Status
echo "1. MONITORING SUB-SKILL"
echo "========================================"
run_remote "monitoring" "quick_status.sh" "Quick Status Check"

# Test 2: QGIS Image - Check
echo "2. QGIS IMAGE SUB-SKILL"
echo "========================================"
run_remote "qgis-image" "check.sh" "QGIS Image Check"

# Test 3: CSRF Fix - Diagnose
echo "3. CSRF FIX SUB-SKILL"
echo "========================================"
run_remote "csrf-fix" "diagnose.sh" "CSRF Diagnosis"

# Test 4: Worker Ops - Status
echo "4. WORKER OPS SUB-SKILL"
echo "========================================"
run_remote "worker-ops" "status.sh" "Worker Status"

# Test 5: Monitoring - Critical Check
echo "5. CRITICAL CHECK"
echo "========================================"
run_remote "monitoring" "critical_check.sh" "Critical Issues Check"

echo "================================================"
echo "Test Suite Complete"
echo "================================================"