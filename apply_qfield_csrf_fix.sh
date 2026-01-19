#!/bin/bash

# QFieldCloud CSRF Fix Application Script
# This script applies the fix to restore both CSRF and Storage configurations

echo "==========================================="
echo "QFieldCloud CSRF Fix Application"
echo "==========================================="
echo ""
echo "This script will fix the CSRF error for Juan on https://qfield.fibreflow.app"
echo ""

# Configuration
SERVER="100.96.203.105"
USER="velo"
CONFIG_FILE="/tmp/fixed_docker_compose_override.yml"

# Check if fixed config exists locally
if [ ! -f "$CONFIG_FILE" ]; then
    echo "Creating fixed configuration file..."
    cat > $CONFIG_FILE << 'EOF'
version: '3.9'
services:
  nginx:
    ports:
      - "8082:80"
    environment:
      WEB_HTTP_PORT: 80

  app:
    environment:
      CSRF_TRUSTED_ORIGINS: ${CSRF_TRUSTED_ORIGINS}
      STORAGE_ENDPOINT_URL: http://minio:9000
      STORAGE_ACCESS_KEY_ID: minioadmin
      STORAGE_SECRET_ACCESS_KEY: minioadmin
      STORAGE_BUCKET_NAME: qfieldcloud-prod
      STORAGE_REGION_NAME: us-east-1

  db:
    image: postgis/postgis:13-3.1-alpine
    restart: unless-stopped
    environment:
      POSTGRES_DB: qfieldcloud_db
      POSTGRES_USER: qfieldcloud_db_admin
      POSTGRES_PASSWORD: c6ce1f02f798c5776fee9e6857f628ff775c75e5eb3b7753
    volumes:
      - postgres_data:/var/lib/postgresql/data/
    ports:
      - "5433:5432"
    command: ["postgres", "-c", "log_statement=all", "-c", "log_destination=stderr"]

  minio:
    image: minio/minio:RELEASE.2025-02-18T16-25-55Z
    restart: unless-stopped
    volumes:
      - minio_data1:/data1
      - minio_data2:/data2
      - minio_data3:/data3
      - minio_data4:/data4
    environment:
      MINIO_ROOT_USER: minioadmin
      MINIO_ROOT_PASSWORD: minioadmin
      MINIO_BROWSER_REDIRECT_URL: http://qfield.fibreflow.app:8010
    command: server /data{1...4} --console-address :9001
    healthcheck:
      test: ["CMD", "curl", "-A", "Mozilla/5.0 (X11; Linux x86_64; rv:30.0) Gecko/20100101 Firefox/30.0", "-f", "http://localhost:9001/minio/index.html"]
      interval: 5s
      timeout: 20s
      retries: 5
    ports:
      - "8010:9001"
      - "8009:9000"

volumes:
  postgres_data:
  minio_data1:
  minio_data2:
  minio_data3:
  minio_data4:
EOF
fi

echo ""
echo "Ready to apply fix to $USER@$SERVER"
echo ""
echo "Steps that will be performed:"
echo "1. Copy fixed configuration to server"
echo "2. Backup existing configuration"
echo "3. Apply the fix"
echo "4. Restart app container"
echo "5. Verify the fix"
echo ""
echo "You will be prompted for the password (2025)"
echo ""
read -p "Press Enter to continue..."

# Copy the fixed configuration
echo ""
echo "Step 1: Copying fixed configuration to server..."
scp $CONFIG_FILE $USER@$SERVER:/tmp/fixed_docker_compose.yml

if [ $? -ne 0 ]; then
    echo "Failed to copy file. Please check SSH access."
    exit 1
fi

# Apply the fix on the server
echo ""
echo "Step 2-5: Applying fix on server..."
ssh $USER@$SERVER << 'REMOTE'
cd /opt/qfieldcloud

# Backup
echo "Backing up current configuration..."
sudo cp docker-compose.override.yml docker-compose.override.yml.backup-csrf-$(date +%Y%m%d-%H%M%S)

# Apply fix
echo "Applying fixed configuration..."
sudo cp /tmp/fixed_docker_compose.yml docker-compose.override.yml

# Verify CSRF line is present
echo ""
echo "Verifying CSRF configuration..."
if grep -q "CSRF_TRUSTED_ORIGINS" docker-compose.override.yml; then
    echo "✓ CSRF configuration found"
else
    echo "✗ WARNING: CSRF configuration missing!"
fi

# Check .env file
echo ""
echo "Checking .env file..."
if grep -q "CSRF_TRUSTED_ORIGINS" .env; then
    echo "✓ CSRF_TRUSTED_ORIGINS found in .env:"
    grep CSRF_TRUSTED_ORIGINS .env
else
    echo "Adding CSRF_TRUSTED_ORIGINS to .env..."
    echo 'CSRF_TRUSTED_ORIGINS="https://srv1083126.hstgr.cloud https://qfield.fibreflow.app"' | sudo tee -a .env
fi

# Restart app
echo ""
echo "Restarting app container..."
sudo docker-compose up -d app

# Wait for restart
echo "Waiting 30 seconds for container to restart..."
sleep 30

# Verify
echo ""
echo "Verifying fix in container..."
sudo docker-compose exec -T app env | grep CSRF || echo "No CSRF variable found"

echo ""
echo "Checking logs for CSRF loading..."
sudo docker-compose logs app --tail 30 | grep -i "csrf\|loading" || echo "No CSRF messages in recent logs"

echo ""
echo "==========================================="
echo "CSRF Fix Applied Successfully!"
echo "==========================================="
echo ""
echo "Next steps for Juan:"
echo "1. Clear browser cache (Ctrl+Shift+Delete)"
echo "2. Visit https://qfield.fibreflow.app"
echo "3. Try logging in or creating a project"
echo "4. Should work without CSRF errors now!"
echo ""
REMOTE

echo "Script completed!"
