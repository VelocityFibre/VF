#!/bin/bash
# Search for the unique message across all WhatsApp services

MESSAGE="FFBRIDGE-150015-2fd5b2"
echo "🔍 Searching for: $MESSAGE"
echo "========================================"

# Check Hostinger VPS logs
echo -e "\n📂 Checking Hostinger VPS (72.60.17.245)..."
sshpass -p "VeloF@2025@@" ssh -o StrictHostKeyChecking=no root@72.60.17.245 "
    echo 'Checking WhatsApp sender logs...'
    grep -r '$MESSAGE' /opt/whatsapp-sender/*.log 2>/dev/null | tail -5

    echo 'Checking monitor logs...'
    grep -r '$MESSAGE' /opt/velo-test-monitor/ 2>/dev/null | head -5

    echo 'Checking systemd logs...'
    journalctl -u whatsapp-sender --since '5 minutes ago' 2>/dev/null | grep -i '$MESSAGE'
"

# Check VF Server logs
echo -e "\n📂 Checking VF Server (100.96.203.105)..."
sshpass -p "2025" ssh -o StrictHostKeyChecking=no velo@100.96.203.105 "
    echo 'Checking WhatsApp service...'
    grep -r '$MESSAGE' ~/whatsapp-sender/ 2>/dev/null | head -5

    echo 'Checking application logs...'
    grep -r '$MESSAGE' ~/apps/fibreflow*/logs/ 2>/dev/null | head -5
"

echo -e "\n========================================"
echo "📝 If the message was found, look for a group ID pattern like:"
echo "   120363XXXXXXXXXX@g.us"
echo "   or XXXXXXXXXX-XXXXXXXXXX@g.us"