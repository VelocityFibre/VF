#!/bin/bash
# QFieldCloud QGIS Image Restore from Backup
# Time: 30 seconds

echo "================================================"
echo "QGIS Image Quick Restore"
echo "================================================"

BACKUP_FILE="/home/velo/qfield-backups/qfieldcloud-qgis-20260113-1034.tar.gz"

# Check if backup exists
if [ ! -f "$BACKUP_FILE" ]; then
    echo "❌ Backup not found at $BACKUP_FILE"
    echo "Use rebuild.sh instead (takes 5 minutes)"
    exit 1
fi

echo "Loading QGIS image from backup..."
docker load < "$BACKUP_FILE"

if [ $? -eq 0 ]; then
    echo "✅ Image restored successfully!"

    # Tag for protection
    docker tag qfieldcloud-qgis:latest qfieldcloud-qgis:production
    docker tag qfieldcloud-qgis:latest qfieldcloud-qgis:do-not-delete

    # Restart workers
    echo "Restarting workers..."
    cd /opt/qfieldcloud
    docker-compose restart worker_wrapper

    echo ""
    echo "✅ COMPLETE! Projects should sync now."
else
    echo "❌ Restore failed! Use rebuild.sh"
    exit 1
fi