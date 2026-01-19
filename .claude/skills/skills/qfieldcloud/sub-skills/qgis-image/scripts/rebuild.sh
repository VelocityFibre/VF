#!/bin/bash
# QFieldCloud QGIS Image Rebuild from Source
# Time: 5-10 minutes

echo "================================================"
echo "QGIS Image Rebuild (5-10 minutes)"
echo "================================================"

cd /opt/qfieldcloud/docker-qgis

if [ ! -f "Dockerfile" ]; then
    echo "❌ Dockerfile not found!"
    echo "Check /opt/qfieldcloud/docker-qgis/"
    exit 1
fi

echo "Building QGIS image from source..."
echo "This will take 5-10 minutes and download ~2.6GB..."

sudo docker build -t qfieldcloud-qgis:latest .

if [ $? -eq 0 ]; then
    echo "✅ Build successful!"

    # Tag for protection
    docker tag qfieldcloud-qgis:latest qfieldcloud-qgis:production
    docker tag qfieldcloud-qgis:latest qfieldcloud-qgis:do-not-delete
    docker tag qfieldcloud-qgis:latest qfieldcloud-qgis:$(date +%Y%m%d)

    # Create backup
    echo "Creating backup for future quick restore..."
    mkdir -p ~/qfield-backups
    docker save qfieldcloud-qgis:latest | gzip > ~/qfield-backups/qfieldcloud-qgis-$(date +%Y%m%d-%H%M).tar.gz

    # Restart workers
    echo "Restarting workers..."
    cd /opt/qfieldcloud
    sudo docker-compose restart worker_wrapper

    echo ""
    echo "✅ COMPLETE! Image rebuilt and backed up."
else
    echo "❌ Build failed! Check Docker logs."
    exit 1
fi