#!/bin/bash

echo "
🧪 SIMPLE INNGEST TEST
======================

This will:
1. Check if GitHub is up
2. Do a calculation (that sometimes fails on purpose)
3. Show you retries in action!
"

echo "📡 Triggering the test..."
echo ""

# Trigger the GitHub check
curl -X POST http://localhost:8288/e/fibreflow-agents/test.check.github \
  -H "Content-Type: application/json" \
  -d '{"data": {"test": true}}' \
  2>/dev/null

echo ""
echo "✅ Done! Now look at the browser!"
echo ""
echo "👉 Open: http://localhost:8288"
echo ""
echo "Click on 'Runs' tab to see:"
echo "  • Your function running"
echo "  • GitHub check result"
echo "  • Calculation (might retry if it 'fails')"
echo ""
echo "🎲 The calculation has 30% chance to fail"
echo "   If it fails, watch Inngest retry it!"
echo ""