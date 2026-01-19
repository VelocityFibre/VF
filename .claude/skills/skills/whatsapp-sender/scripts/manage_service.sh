#!/bin/bash

# WhatsApp Sender Service Management Script
# Usage: ./manage_service.sh [start|stop|restart|status|logs|test]

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

# Function to execute SSH commands
exec_ssh() {
    ssh -i "$SSH_KEY" "$USER@$SERVER" "$1"
}

# Function to print header
print_header() {
    echo ""
    echo -e "${BLUE}$1${NC}"
    echo "======================================"
}

# Function to check service status
check_status() {
    print_header "WhatsApp Sender Service Status"

    # Check if process is running
    PID=$(exec_ssh "if [ -f $WA_DIR/whatsapp-sender.pid ]; then cat $WA_DIR/whatsapp-sender.pid; else echo ''; fi")

    if [ -n "$PID" ]; then
        RUNNING=$(exec_ssh "ps -p $PID > /dev/null 2>&1 && echo 'true' || echo 'false'")
        if [ "$RUNNING" = "true" ]; then
            echo -e "${GREEN}✓ Service is running (PID: $PID)${NC}"
        else
            echo -e "${RED}✗ Service is not running (stale PID: $PID)${NC}"
        fi
    else
        echo -e "${RED}✗ Service is not running (no PID file)${NC}"
    fi

    # Check session database
    SESSION=$(exec_ssh "[ -f $WA_DIR/store/whatsapp.db ] && echo 'exists' || echo 'missing'")
    if [ "$SESSION" = "exists" ]; then
        SESSION_SIZE=$(exec_ssh "ls -lh $WA_DIR/store/whatsapp.db | awk '{print \$5}'")
        SESSION_DATE=$(exec_ssh "stat -c %y $WA_DIR/store/whatsapp.db | cut -d' ' -f1")
        echo -e "${GREEN}✓ Session database exists (${SESSION_SIZE}, created: ${SESSION_DATE})${NC}"
    else
        echo -e "${RED}✗ Session database missing (pairing required)${NC}"
    fi

    # Check API health
    echo ""
    echo "Checking API health..."
    HEALTH=$(exec_ssh "curl -s http://localhost:8081/health 2>/dev/null || echo '{\"status\":\"offline\"}'")

    if echo "$HEALTH" | grep -q "healthy"; then
        echo -e "${GREEN}✓ API is healthy${NC}"

        # Parse and display connection info
        CONNECTED=$(echo "$HEALTH" | grep -o '"connected":[^,}]*' | cut -d: -f2)
        PHONE=$(echo "$HEALTH" | grep -o '"phone":"[^"]*"' | cut -d'"' -f4)

        if [ "$CONNECTED" = "true" ]; then
            echo -e "${GREEN}✓ WhatsApp connected${NC}"
            [ -n "$PHONE" ] && echo "  Phone: $PHONE"
        else
            echo -e "${YELLOW}⚠️  WhatsApp not connected${NC}"
        fi
    else
        echo -e "${RED}✗ API is offline or unhealthy${NC}"
    fi

    # Check recent activity
    echo ""
    echo "Recent activity:"
    exec_ssh "grep -E '(message sent|ERROR)' $WA_DIR/whatsapp-sender.log 2>/dev/null | tail -3 || echo '  No recent activity'"
}

# Function to start service
start_service() {
    print_header "Starting WhatsApp Sender Service"

    # Check if already running
    PID=$(exec_ssh "if [ -f $WA_DIR/whatsapp-sender.pid ]; then cat $WA_DIR/whatsapp-sender.pid; else echo ''; fi")
    if [ -n "$PID" ]; then
        RUNNING=$(exec_ssh "ps -p $PID > /dev/null 2>&1 && echo 'true' || echo 'false'")
        if [ "$RUNNING" = "true" ]; then
            echo -e "${YELLOW}Service is already running (PID: $PID)${NC}"
            return
        fi
    fi

    # Check session exists
    SESSION=$(exec_ssh "[ -f $WA_DIR/store/whatsapp.db ] && echo 'exists' || echo 'missing'")
    if [ "$SESSION" = "missing" ]; then
        echo -e "${RED}Error: No WhatsApp session found!${NC}"
        echo "Please run pairing first: ./pair_phone.sh"
        exit 1
    fi

    # Start the service
    echo "Starting service..."
    exec_ssh "cd $WA_DIR && nohup ./whatsapp-sender > whatsapp-sender.log 2>&1 & echo \$! > whatsapp-sender.pid"

    sleep 3

    # Verify it started
    NEW_PID=$(exec_ssh "cat $WA_DIR/whatsapp-sender.pid")
    RUNNING=$(exec_ssh "ps -p $NEW_PID > /dev/null 2>&1 && echo 'true' || echo 'false'")

    if [ "$RUNNING" = "true" ]; then
        echo -e "${GREEN}✓ Service started successfully (PID: $NEW_PID)${NC}"

        # Wait for API to be ready
        echo "Waiting for API to be ready..."
        sleep 2

        HEALTH=$(exec_ssh "curl -s http://localhost:8081/health 2>/dev/null || echo '{\"status\":\"offline\"}'")
        if echo "$HEALTH" | grep -q "healthy"; then
            echo -e "${GREEN}✓ API is healthy and ready${NC}"
        else
            echo -e "${YELLOW}⚠️  API may not be ready yet. Check logs for details.${NC}"
        fi
    else
        echo -e "${RED}✗ Failed to start service${NC}"
        echo "Check logs: ssh -i $SSH_KEY $USER@$SERVER 'tail -50 $WA_DIR/whatsapp-sender.log'"
        exit 1
    fi
}

# Function to stop service
stop_service() {
    print_header "Stopping WhatsApp Sender Service"

    PID=$(exec_ssh "if [ -f $WA_DIR/whatsapp-sender.pid ]; then cat $WA_DIR/whatsapp-sender.pid; else echo ''; fi")

    if [ -z "$PID" ]; then
        echo -e "${YELLOW}No PID file found${NC}"
    else
        RUNNING=$(exec_ssh "ps -p $PID > /dev/null 2>&1 && echo 'true' || echo 'false'")
        if [ "$RUNNING" = "true" ]; then
            echo "Stopping service (PID: $PID)..."
            exec_ssh "kill $PID 2>/dev/null || true"
            sleep 2

            # Verify stopped
            STILL_RUNNING=$(exec_ssh "ps -p $PID > /dev/null 2>&1 && echo 'true' || echo 'false'")
            if [ "$STILL_RUNNING" = "false" ]; then
                echo -e "${GREEN}✓ Service stopped successfully${NC}"
            else
                echo -e "${YELLOW}⚠️  Service may still be stopping...${NC}"
                echo "Force stop with: kill -9 $PID"
            fi
        else
            echo -e "${YELLOW}Service was not running (stale PID: $PID)${NC}"
        fi
    fi

    # Clean up any remaining processes
    exec_ssh "pkill -f whatsapp-sender 2>/dev/null || true"
    exec_ssh "rm -f $WA_DIR/whatsapp-sender.pid"
    echo -e "${GREEN}✓ Cleanup completed${NC}"
}

# Function to restart service
restart_service() {
    print_header "Restarting WhatsApp Sender Service"
    stop_service
    echo ""
    sleep 2
    start_service
}

# Function to show logs
show_logs() {
    print_header "WhatsApp Sender Logs"

    LINES="${1:-50}"
    echo "Showing last $LINES lines..."
    echo ""
    exec_ssh "tail -${LINES} $WA_DIR/whatsapp-sender.log 2>/dev/null || echo 'No logs found'"
}

# Function to test service
test_service() {
    print_header "Testing WhatsApp Sender Service"

    # Check health
    echo "1. Testing health endpoint..."
    HEALTH=$(exec_ssh "curl -s http://localhost:8081/health 2>/dev/null")
    if [ -n "$HEALTH" ]; then
        echo -e "${GREEN}✓ Health endpoint responding${NC}"
        echo "$HEALTH" | python3 -m json.tool 2>/dev/null || echo "$HEALTH"
    else
        echo -e "${RED}✗ Health endpoint not responding${NC}"
        exit 1
    fi

    echo ""
    echo "2. Testing status endpoint..."
    STATUS=$(exec_ssh "curl -s http://localhost:8081/status 2>/dev/null")
    if [ -n "$STATUS" ]; then
        echo -e "${GREEN}✓ Status endpoint responding${NC}"
        echo "$STATUS" | python3 -m json.tool 2>/dev/null || echo "$STATUS"
    else
        echo -e "${YELLOW}⚠️  Status endpoint not responding${NC}"
    fi

    echo ""
    read -p "3. Send test message? (yes/no): " send_test
    if [ "$send_test" = "yes" ]; then
        read -p "Enter phone number (with +27 prefix): " phone
        read -p "Enter test message: " message

        echo ""
        echo "Sending test message..."
        RESPONSE=$(exec_ssh "curl -s -X POST http://localhost:8081/send \
            -H 'Content-Type: application/json' \
            -d '{\"phone\": \"$phone\", \"message\": \"$message\"}'")

        if echo "$RESPONSE" | grep -q "success.*true"; then
            echo -e "${GREEN}✓ Message sent successfully${NC}"
            echo "$RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$RESPONSE"
        else
            echo -e "${RED}✗ Failed to send message${NC}"
            echo "$RESPONSE"
        fi
    fi
}

# Function to show usage
show_usage() {
    echo "WhatsApp Sender Service Manager"
    echo ""
    echo "Usage: $0 [command] [options]"
    echo ""
    echo "Commands:"
    echo "  start       Start the WhatsApp sender service"
    echo "  stop        Stop the WhatsApp sender service"
    echo "  restart     Restart the WhatsApp sender service"
    echo "  status      Show service status"
    echo "  logs [n]    Show last n lines of logs (default: 50)"
    echo "  test        Test service endpoints"
    echo "  help        Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 status"
    echo "  $0 start"
    echo "  $0 logs 100"
    echo "  $0 restart"
}

# Main script
case "${1:-}" in
    start)
        start_service
        ;;
    stop)
        stop_service
        ;;
    restart)
        restart_service
        ;;
    status)
        check_status
        ;;
    logs)
        show_logs "${2:-50}"
        ;;
    test)
        test_service
        ;;
    help|--help|-h)
        show_usage
        ;;
    *)
        if [ -n "${1:-}" ]; then
            echo -e "${RED}Unknown command: $1${NC}"
            echo ""
        fi
        show_usage
        exit 1
        ;;
esac

echo ""