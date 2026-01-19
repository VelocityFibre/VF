#!/bin/bash

# WhatsApp Phone Pairing Script
# Usage: ./pair_phone.sh [phone_number]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SERVER="100.96.203.105"
USER="louis"
SSH_KEY="$HOME/.ssh/vf_server_key"
WA_DIR="~/whatsapp-sender"

echo -e "${BLUE}WhatsApp Sender Phone Pairing Utility${NC}"
echo "======================================"

# Check SSH key exists
if [ ! -f "$SSH_KEY" ]; then
    echo -e "${RED}Error: SSH key not found at $SSH_KEY${NC}"
    exit 1
fi

# Get phone number if provided
PHONE_NUMBER="${1:-}"
if [ -n "$PHONE_NUMBER" ]; then
    echo -e "${GREEN}Phone number to pair: $PHONE_NUMBER${NC}"
else
    echo -e "${YELLOW}No phone number provided. Will display pairing code for manual entry.${NC}"
fi

echo ""
echo -e "${YELLOW}⚠️  IMPORTANT WARNINGS:${NC}"
echo "1. This will DELETE the existing WhatsApp session"
echo "2. The previous phone will be disconnected"
echo "3. You need the phone ready with WhatsApp installed"
echo "4. If you see 'rate-overlimit' error, wait 1-24 hours"
echo ""
read -p "Continue with pairing? (yes/no): " confirm

if [ "$confirm" != "yes" ]; then
    echo -e "${RED}Pairing cancelled${NC}"
    exit 0
fi

echo ""
echo -e "${BLUE}Step 1: Backing up existing session (if any)...${NC}"
ssh -i "$SSH_KEY" "$USER@$SERVER" "
    cd $WA_DIR
    if [ -f store/whatsapp.db ]; then
        backup_dir=\"store.backup.\$(date +%Y%m%d_%H%M%S)\"
        cp -r store \$backup_dir
        echo \"✓ Session backed up to \$backup_dir\"
    else
        echo \"✓ No existing session to backup\"
    fi
"

echo ""
echo -e "${BLUE}Step 2: Stopping any running WhatsApp sender...${NC}"
ssh -i "$SSH_KEY" "$USER@$SERVER" "
    if [ -f $WA_DIR/whatsapp-sender.pid ]; then
        pid=\$(cat $WA_DIR/whatsapp-sender.pid)
        if ps -p \$pid > /dev/null 2>&1; then
            kill \$pid 2>/dev/null || true
            echo \"✓ Stopped existing service (PID: \$pid)\"
            sleep 2
        fi
    fi
    pkill -f whatsapp-sender 2>/dev/null || true
"

echo ""
echo -e "${BLUE}Step 3: Clearing old session...${NC}"
ssh -i "$SSH_KEY" "$USER@$SERVER" "
    cd $WA_DIR
    rm -rf store/*
    echo \"✓ Session cleared\"
"

echo ""
echo -e "${BLUE}Step 4: Starting pairing process...${NC}"
echo -e "${YELLOW}Watch for the pairing code below!${NC}"
echo ""

# Start the pairing process and capture output
ssh -i "$SSH_KEY" "$USER@$SERVER" "
    cd $WA_DIR
    timeout 60 ./whatsapp-sender 2>&1 | while IFS= read -r line; do
        echo \"\$line\"

        # Check for pairing code
        if echo \"\$line\" | grep -q 'Pairing code:'; then
            code=\$(echo \"\$line\" | grep -oP 'Pairing code: \K[A-Z0-9-]+')
            echo \"\"
            echo \"========================================\"
            echo \"📱 PAIRING CODE: \$code\"
            echo \"========================================\"
            echo \"\"
            echo \"On your phone:\"
            echo \"1. Open WhatsApp\"
            echo \"2. Go to Settings > Linked Devices\"
            echo \"3. Tap 'Link a Device'\"
            echo \"4. Enter the code: \$code\"
            echo \"\"
            echo \"Waiting for pairing...\"
        fi

        # Check for rate limit
        if echo \"\$line\" | grep -q 'rate-overlimit'; then
            echo \"\"
            echo \"❌ ERROR: WhatsApp rate limit detected!\"
            echo \"You must wait 1-24 hours before trying again.\"
            echo \"The rate limit was triggered by too many pairing attempts.\"
            exit 1
        fi

        # Check for successful login
        if echo \"\$line\" | grep -q 'Successfully logged in'; then
            echo \"\"
            echo \"✅ SUCCESS: Phone paired successfully!\"
            echo \"The service will now be started in background.\"
            sleep 2
            break
        fi
    done
"

# Check if pairing was successful
echo ""
echo -e "${BLUE}Step 5: Verifying pairing...${NC}"
PAIRED=$(ssh -i "$SSH_KEY" "$USER@$SERVER" "
    if [ -f $WA_DIR/store/whatsapp.db ]; then
        echo 'true'
    else
        echo 'false'
    fi
")

if [ "$PAIRED" = "true" ]; then
    echo -e "${GREEN}✓ Session database created successfully${NC}"

    echo ""
    echo -e "${BLUE}Step 6: Starting service in background...${NC}"
    ssh -i "$SSH_KEY" "$USER@$SERVER" "
        cd $WA_DIR
        nohup ./whatsapp-sender > whatsapp-sender.log 2>&1 &
        echo \$! > whatsapp-sender.pid
        sleep 3

        # Verify it's running
        if ps -p \$(cat whatsapp-sender.pid) > /dev/null 2>&1; then
            echo \"✓ Service started (PID: \$(cat whatsapp-sender.pid))\"
        else
            echo \"⚠️  Service may not have started properly\"
        fi
    "

    echo ""
    echo -e "${BLUE}Step 7: Testing service health...${NC}"
    sleep 2
    HEALTH=$(ssh -i "$SSH_KEY" "$USER@$SERVER" "curl -s http://localhost:8081/health 2>/dev/null || echo '{\"status\":\"error\"}'")

    if echo "$HEALTH" | grep -q "healthy"; then
        echo -e "${GREEN}✓ Service is healthy and ready!${NC}"
        echo ""
        echo -e "${GREEN}✅ PAIRING COMPLETE!${NC}"
        echo ""
        echo "Service details:"
        echo "- Server: $SERVER"
        echo "- Port: 8081"
        echo "- Logs: $WA_DIR/whatsapp-sender.log"
        echo ""
        echo "Test with:"
        echo "  curl http://$SERVER:8081/health"
    else
        echo -e "${YELLOW}⚠️  Service health check failed${NC}"
        echo "Check logs with:"
        echo "  ssh -i $SSH_KEY $USER@$SERVER 'tail -50 $WA_DIR/whatsapp-sender.log'"
    fi
else
    echo -e "${RED}❌ PAIRING FAILED${NC}"
    echo ""
    echo "Possible reasons:"
    echo "1. Rate limit active (wait 1-24 hours)"
    echo "2. Pairing was cancelled or timed out"
    echo "3. Network connectivity issues"
    echo ""
    echo "Check logs with:"
    echo "  ssh -i $SSH_KEY $USER@$SERVER 'tail -50 $WA_DIR/whatsapp-sender.log'"
fi