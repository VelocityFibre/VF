#!/bin/bash
# Super simple trigger script

echo "🚀 Triggering server check..."
echo ""

# Send the event to trigger our function
curl -X POST http://localhost:8288/e/fibreflow-agents/test.check.server \
  -H "Content-Type: application/json" \
  -d '{"data": {"requested_at": "'$(date)'"}}' \
  2>/dev/null

echo ""
echo "✅ Check triggered!"
echo ""
echo "👀 Now open http://localhost:8288 in your browser"
echo "   Click on 'Runs' to see your function execute!"
echo ""