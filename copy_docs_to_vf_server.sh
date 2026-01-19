#!/bin/bash

# Script to copy essential documentation to VF Server
# Run this from your local machine: ./copy_docs_to_vf_server.sh

VF_SERVER="100.96.203.105"
VF_USER="velo"
VF_PASS="2025"

echo "📚 Copying documentation to VF Server..."

# Create documentation structure on VF Server
sshpass -p "$VF_PASS" ssh $VF_USER@$VF_SERVER << 'EOF'
# Create documentation directories
mkdir -p /opt/docs/{architecture,setup,guides}
mkdir -p /home/velo/server-docs

# Create a README in home directory for easy access
cat > /home/velo/README_SERVER.md << 'READMEEOF'
# VF Server Documentation

## Quick Access to Documentation
- Setup Guide: /opt/docs/setup/VF_SERVER_PRODUCTION_SETUP.md
- Architecture: /opt/docs/architecture/INFRASTRUCTURE_STRATEGY.md
- Master Reference: /opt/docs/CLAUDE.md

## Port Allocation
- 3000: Production (app.fibreflow.app)
- 3005: Development (Hein)
- 3006: Staging (Louis)
- 8080: QFieldCloud
- 8081: WhatsApp Sender
- 8100: VLM Processing

## Quick Commands
- View setup guide: cat /opt/docs/setup/VF_SERVER_PRODUCTION_SETUP.md
- Check services: pm2 list
- View logs: pm2 logs
READMEEOF
EOF

echo "📂 Uploading documentation files..."

# Copy main setup guide
sshpass -p "$VF_PASS" scp docs/deployment/VF_SERVER_PRODUCTION_SETUP.md \
    $VF_USER@$VF_SERVER:/home/velo/production-docs/

# Copy Hein's prompt
sshpass -p "$VF_PASS" scp docs/deployment/HEIN_CLAUDE_PROMPT_UPDATED.md \
    $VF_USER@$VF_SERVER:/home/velo/production-docs/

# Copy architecture documentation
sshpass -p "$VF_PASS" scp docs/INFRASTRUCTURE_RESILIENCE_STRATEGY.md \
    $VF_USER@$VF_SERVER:/home/velo/production-docs/

# Copy master reference
sshpass -p "$VF_PASS" scp CLAUDE.md \
    $VF_USER@$VF_SERVER:/home/velo/production-docs/

# Create quick setup script on server
sshpass -p "$VF_PASS" ssh $VF_USER@$VF_SERVER << 'EOF'
cat > /home/velo/setup_production.sh << 'SETUPEOF'
#!/bin/bash
# Quick setup script for production services on VF Server

echo "🚀 VF Server Production Setup"
echo "=============================="
echo ""
echo "This script will help you set up production services."
echo "Current services on this server:"
echo ""
echo "EXISTING (keep running):"
echo "  - Port 3005: Development (Hein)"
echo "  - Port 3006: Staging (Louis)"
echo ""
echo "TO BE ADDED:"
echo "  - Port 3000: Production FibreFlow"
echo "  - Port 8080: QFieldCloud"
echo "  - Port 8081: WhatsApp Sender"
echo ""
echo "Documentation available at:"
echo "  /opt/docs/setup/VF_SERVER_PRODUCTION_SETUP.md"
echo ""
echo "Run 'cat /opt/docs/setup/VF_SERVER_PRODUCTION_SETUP.md' for full guide"

# Create production directories
echo ""
echo "Creating production directories..."
sudo mkdir -p /opt/{fibreflow-prod,qfieldcloud,whatsapp-sender,monitoring}
sudo mkdir -p /var/log/{fibreflow-prod,qfieldcloud,whatsapp}
sudo chown -R velo:velo /opt/fibreflow-prod /opt/qfieldcloud /opt/whatsapp-sender
echo "✅ Directories created"

echo ""
echo "Next steps:"
echo "1. Deploy production app to /opt/fibreflow-prod"
echo "2. Configure nginx for production domains"
echo "3. Set up QFieldCloud service"
echo "4. Migrate WhatsApp sender (preserve session!)"
echo ""
echo "See full guide: /opt/docs/setup/VF_SERVER_PRODUCTION_SETUP.md"
SETUPEOF

chmod +x /home/velo/setup_production.sh
EOF

echo "✅ Documentation copied to VF Server!"
echo ""
echo "📍 Documentation locations on VF Server:"
echo "   - Main guide: /opt/docs/setup/VF_SERVER_PRODUCTION_SETUP.md"
echo "   - Architecture: /opt/docs/architecture/INFRASTRUCTURE_STRATEGY.md"
echo "   - Master reference: /opt/docs/CLAUDE.md"
echo "   - Quick README: /home/velo/README_SERVER.md"
echo "   - Setup script: /home/velo/setup_production.sh"
echo ""
echo "Tell Hein to SSH to VF Server and run:"
echo "   ./setup_production.sh"