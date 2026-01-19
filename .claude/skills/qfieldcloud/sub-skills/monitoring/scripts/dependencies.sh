#!/bin/bash
# QFieldCloud Service Dependencies Check

echo "================================================"
echo "QFieldCloud Service Dependencies"
echo "================================================"
echo ""

cd /opt/qfieldcloud 2>/dev/null || exit 1

# Function to check dependency
check_dep() {
    local service=$1
    local status="❌ DOWN"

    # Handle both naming conventions (with and without -1 suffix)
    if docker ps | grep -qE "${service}(-1)?.*Up"; then
        status="✅ Running"
    fi
    echo "$status"
}

echo "Service Dependency Tree:"
echo ""
echo "┌─ nginx (Web Server)"
echo "│  └─ Depends on: app"
echo "│     Status: $(check_dep 'qfieldcloud-nginx')"
echo "│"
echo "├─ app (Django Application)"
echo "│  ├─ Depends on: db, redis, minio"
echo "│  └─ Status: $(check_dep 'qfieldcloud-app')"
echo "│"
echo "├─ worker_wrapper (Processing)"
echo "│  ├─ Depends on: app, db, redis, qgis-image"
echo "│  ├─ Status: $(docker ps | grep -c 'worker_wrapper.*Up')/8 running"
echo "│  └─ QGIS Image: $(docker images | grep -q 'qfieldcloud-qgis.*latest' && echo '✅ Present' || echo '❌ MISSING')"
echo "│"
echo "├─ db (PostgreSQL Database)"
echo "│  ├─ No dependencies"
echo "│  └─ Status: $(check_dep 'qfieldcloud-db')"
echo "│"
echo "├─ redis (Cache/Queue)"
echo "│  ├─ No dependencies"
echo "│  └─ Status: $(check_dep 'qfieldcloud-redis')"
echo "│"
echo "└─ minio (S3 Storage)"
echo "   ├─ No dependencies"
echo "   └─ Status: $(check_dep 'qfieldcloud-minio')"
echo ""

echo "Critical Dependencies:"
echo "----------------------------------------"

# Check critical paths
ISSUES=()

# Workers need QGIS image
if ! docker images | grep -q "qfieldcloud-qgis.*latest"; then
    ISSUES+=("❌ Workers cannot process without QGIS image")
fi

# App needs database
if ! docker ps | grep -q "qfieldcloud-db.*Up"; then
    ISSUES+=("❌ App cannot function without database")
fi

# Workers need app
if ! docker ps | grep -q "qfieldcloud-app.*Up"; then
    ISSUES+=("❌ Workers cannot function without app service")
fi

# Nginx needs app
if docker ps | grep -q "qfieldcloud-nginx.*Up" && ! docker ps | grep -q "qfieldcloud-app.*Up"; then
    ISSUES+=("⚠️  Nginx running but app is down - web interface broken")
fi

if [ ${#ISSUES[@]} -eq 0 ]; then
    echo "✅ All critical dependencies satisfied"
else
    for issue in "${ISSUES[@]}"; do
        echo "$issue"
    done
fi

echo ""
echo "Service Start Order:"
echo "----------------------------------------"
echo "1. db, redis, minio (can start in parallel)"
echo "2. app (after db and redis are ready)"
echo "3. worker_wrapper (after app is ready)"
echo "4. nginx (after app is ready)"

echo ""
echo "Restart Commands:"
echo "----------------------------------------"
echo "Full restart (correct order):"
echo "  docker-compose down && docker-compose up -d"
echo ""
echo "Individual service restart:"
echo "  docker-compose restart [service_name]"
echo ""
echo "Workers only:"
echo "  docker-compose restart worker_wrapper"

# Exit code based on critical dependencies
if [ ${#ISSUES[@]} -eq 0 ]; then
    exit 0
else
    exit 1
fi