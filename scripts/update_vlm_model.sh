#!/bin/bash
# Script to update VLM model configuration on VF server

echo "Updating VLM Model Configuration"
echo "================================="
echo "Changing from: openbmb/MiniCPM-V-2_6"
echo "Changing to:   Qwen/Qwen3-VL-8B-Instruct"
echo ""

# Check current configuration
echo "Checking current .env configuration..."
sshpass -p "VeloAdmin2025!" ssh -o StrictHostKeyChecking=no louis@100.96.203.105 \
  'grep -E "VLM_MODEL|VLM_API_URL" /home/louis/apps/fibreflow/.env 2>/dev/null || echo "No VLM config in .env"'

echo ""
echo "Adding/Updating VLM_MODEL in .env..."

# Update or add VLM_MODEL in .env
sshpass -p "VeloAdmin2025!" ssh -o StrictHostKeyChecking=no louis@100.96.203.105 '
cd /home/louis/apps/fibreflow

# Backup current .env
cp .env .env.backup.$(date +%Y%m%d_%H%M%S)

# Check if VLM_MODEL exists and update it, or add it
if grep -q "^VLM_MODEL=" .env 2>/dev/null; then
    # Update existing
    sed -i "s|^VLM_MODEL=.*|VLM_MODEL=Qwen/Qwen3-VL-8B-Instruct|" .env
    echo "Updated existing VLM_MODEL"
else
    # Add new
    echo "" >> .env
    echo "# Vision Language Model Configuration" >> .env
    echo "VLM_MODEL=Qwen/Qwen3-VL-8B-Instruct" >> .env
    echo "Added VLM_MODEL to .env"
fi

# Also ensure VLM_API_URL is set if not already
if ! grep -q "^VLM_API_URL=" .env 2>/dev/null; then
    echo "VLM_API_URL=http://100.96.203.105:8100" >> .env
    echo "Added VLM_API_URL to .env"
fi

# Show updated config
echo ""
echo "Updated configuration:"
grep -E "VLM_MODEL|VLM_API_URL" .env
'

echo ""
echo "Restarting Next.js application..."

# Find and restart the Next.js process
sshpass -p "VeloAdmin2025!" ssh -o StrictHostKeyChecking=no louis@100.96.203.105 '
# Get the PID of the Next.js server
PID=$(ps aux | grep "next-server" | grep -v grep | awk "{print \$2}")

if [ ! -z "$PID" ]; then
    echo "Found Next.js process: PID $PID"
    kill -HUP $PID 2>/dev/null || kill $PID
    echo "Sent restart signal to Next.js"

    # Wait a moment
    sleep 3

    # Start it again if needed
    cd /home/louis/apps/fibreflow
    if ! ps aux | grep -q "[n]ext-server"; then
        echo "Starting Next.js server..."
        npm run start > /dev/null 2>&1 &
    fi
else
    echo "Next.js process not found. Starting it..."
    cd /home/louis/apps/fibreflow
    npm run start > /dev/null 2>&1 &
fi

sleep 5
echo ""
echo "Server status:"
ps aux | grep "[n]ext-server" | head -1
'

echo ""
echo "================================="
echo "VLM Model Update Complete!"
echo ""
echo "The system is now configured to use: Qwen/Qwen3-VL-8B-Instruct"
echo ""
echo "Note: Make sure the Qwen model is available on the VLM server at port 8100"
echo "You can test with: ./venv/bin/python3 evaluate_dr.py DR1733758"