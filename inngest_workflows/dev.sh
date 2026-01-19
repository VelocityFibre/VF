#!/bin/bash
# Development script for Inngest + FibreFlow

echo "🚀 Starting FibreFlow Inngest Development Environment"
echo "=================================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if virtual environment is activated
if [ -z "$VIRTUAL_ENV" ]; then
    echo -e "${YELLOW}Activating virtual environment...${NC}"
    source ../venv/bin/activate
fi

# Function to cleanup on exit
cleanup() {
    echo -e "\n${YELLOW}Shutting down services...${NC}"
    kill $FASTAPI_PID 2>/dev/null
    kill $INNGEST_PID 2>/dev/null
    exit
}

# Register cleanup function
trap cleanup INT TERM

# Start FastAPI server in background
echo -e "${GREEN}Starting FastAPI server on port 3000...${NC}"
python app.py &
FASTAPI_PID=$!

# Wait for FastAPI to start
sleep 3

# Check if FastAPI is running
if ! kill -0 $FASTAPI_PID 2>/dev/null; then
    echo -e "${RED}Failed to start FastAPI server${NC}"
    exit 1
fi

echo -e "${GREEN}✅ FastAPI server running at http://localhost:3000${NC}"

# Start Inngest dev server
echo -e "${GREEN}Starting Inngest dev server...${NC}"
echo -e "${YELLOW}Note: This will open at http://localhost:8288${NC}"

# Run Inngest dev server with our endpoint
npx inngest-cli@latest dev \
    --no-discovery \
    -u http://localhost:3000/api/inngest &
INNGEST_PID=$!

echo ""
echo "=================================================="
echo -e "${GREEN}🎉 Development environment ready!${NC}"
echo ""
echo "Services running:"
echo "  • FastAPI: http://localhost:3000"
echo "  • Inngest Dev UI: http://localhost:8288"
echo "  • API Endpoint: http://localhost:3000/api/inngest"
echo ""
echo "Quick test commands:"
echo "  # Trigger database sync"
echo "  curl -X POST http://localhost:8288/e/fibreflow-agents/database.sync.scheduled"
echo ""
echo "  # Queue WhatsApp message"
echo '  curl -X POST http://localhost:8288/e/fibreflow-agents/whatsapp.message.queued \\'
echo '    -H "Content-Type: application/json" \\'
echo '    -d '"'"'{"data":{"phone":"+27123456789","message":"Test message"}}'"'"
echo ""
echo "  # Request VLM evaluation"
echo '  curl -X POST http://localhost:8288/e/fibreflow-agents/vlm.evaluation.requested \\'
echo '    -H "Content-Type: application/json" \\'
echo '    -d '"'"'{"data":{"dr_number":"DR123","image_url":"test.jpg"}}'"'"
echo ""
echo -e "${YELLOW}Press Ctrl+C to stop all services${NC}"
echo "=================================================="

# Wait for processes
wait $FASTAPI_PID
wait $INNGEST_PID