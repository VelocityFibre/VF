#!/bin/bash

# Deploy Storage Server to VF Server
# Run this locally: bash deploy-storage-server.sh

echo "🚀 Deploying Storage Server to VF Server..."

# Configuration
VF_SERVER="velo@100.96.203.105"
VF_PASSWORD="2025"

# Copy setup script to server
echo "📤 Copying setup script..."
sshpass -p "$VF_PASSWORD" scp -o PreferredAuthentications=password -o PubkeyAuthentication=no setup-storage-server.sh $VF_SERVER:/tmp/

# Copy adapter files
echo "📤 Copying adapter files..."
sshpass -p "$VF_PASSWORD" scp -o PreferredAuthentications=password -o PubkeyAuthentication=no storage-adapter.ts $VF_SERVER:/tmp/
sshpass -p "$VF_PASSWORD" scp -o PreferredAuthentications=password -o PubkeyAuthentication=no storage-migration.env $VF_SERVER:/tmp/

# Execute setup on server
echo "🔧 Running setup on VF Server..."
sshpass -p "$VF_PASSWORD" ssh -o PreferredAuthentications=password -o PubkeyAuthentication=no $VF_SERVER << 'EOF'
# Run setup script with sudo
echo "2025" | sudo -S bash /tmp/setup-storage-server.sh

# Copy adapter to app directories
cp /tmp/storage-adapter.ts /srv/data/apps/fibreflow/lib/
cp /tmp/storage-adapter.ts /home/louis/fibreflow-louis/lib/
cp /tmp/storage-migration.env /home/louis/

# Test the service
sleep 5
curl -s http://localhost:8090/health && echo "✅ Nginx serving files"
curl -s http://localhost:8091/health && echo "✅ Storage API running"
systemctl status fibreflow-storage --no-pager | head -10

echo ""
echo "📊 Deployment Summary:"
echo "  Storage API: http://100.96.203.105:8091"
echo "  File Server: http://100.96.203.105:8090"
echo "  Public URL: https://vf.fibreflow.app/storage/"
echo ""
EOF

echo ""
echo "✅ Deployment complete!"
echo ""
echo "📝 Next Steps:"
echo "1. Test upload:"
echo "   curl -X POST -F 'file=@test.jpg' https://vf.fibreflow.app/api/storage/upload/test/images"
echo ""
echo "2. Update your app's .env:"
echo "   NEXT_PUBLIC_USE_VF_STORAGE=true"
echo "   NEXT_PUBLIC_VF_STORAGE_URL=https://vf.fibreflow.app/api/storage"
echo ""
echo "3. Import storage adapter in your code:"
echo "   import { storage } from '@/lib/storage-adapter'"
echo ""
echo "4. Monitor logs:"
echo "   ssh $VF_SERVER 'tail -f /srv/data/fibreflow-storage/logs/storage-api.log'"