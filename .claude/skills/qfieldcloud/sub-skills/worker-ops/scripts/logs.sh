#!/bin/bash
# QFieldCloud Worker Logs Viewer

# Default to 50 lines if not specified
LINES=${1:-50}

echo "================================================"
echo "QFieldCloud Worker Logs (Last $LINES lines)"
echo "================================================"

cd /opt/qfieldcloud

# Show logs with color coding
docker-compose logs --tail=$LINES worker_wrapper 2>&1 | \
    sed -e 's/ERROR/\x1b[31mERROR\x1b[0m/g' \
        -e 's/WARNING/\x1b[33mWARNING\x1b[0m/g' \
        -e 's/INFO/\x1b[32mINFO\x1b[0m/g' \
        -e 's/CRITICAL/\x1b[35mCRITICAL\x1b[0m/g' \
        -e 's/Finished execution with code 0/\x1b[32m✅ SUCCESS\x1b[0m/g' \
        -e 's/ImageNotFound/\x1b[31m❌ IMAGE MISSING\x1b[0m/g'

echo ""
echo "================================================"
echo "Log Summary"
echo "================================================"

# Count different log levels
ERROR_COUNT=$(docker-compose logs --tail=1000 worker_wrapper 2>&1 | grep -c "ERROR")
WARNING_COUNT=$(docker-compose logs --tail=1000 worker_wrapper 2>&1 | grep -c "WARNING")
SUCCESS_COUNT=$(docker-compose logs --tail=1000 worker_wrapper 2>&1 | grep -c "Finished execution with code 0")

echo "Last 1000 lines contain:"
echo "  Errors: $ERROR_COUNT"
echo "  Warnings: $WARNING_COUNT"
echo "  Successful jobs: $SUCCESS_COUNT"

if [ "$ERROR_COUNT" -gt 0 ]; then
    echo ""
    echo "⚠️  Errors detected! Run ./check_errors.sh for details"
fi