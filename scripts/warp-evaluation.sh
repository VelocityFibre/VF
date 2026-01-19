#!/bin/bash
# Warp 30-Minute Evaluation Script
# Run this in Warp to test key features before full implementation

echo "=== Warp Evaluation Checklist ==="
echo ""

# Test 1: Basic functionality
echo "✓ Test 1: Basic Commands"
echo "  Run: ls -la, git status, cd ~/Agents/claude"
echo "  Expected: Commands work, blocks are intuitive"
read -p "  Pass? (y/n): " test1
echo ""

# Test 2: Warp Agent with MCP
echo "✓ Test 2: Warp Agent + MCP"
echo "  1. Settings → MCP Servers → Add Server (File-based)"
echo "     - Name: local-docs"
echo "     - Type: File"
echo "     - Path: ~/Agents/claude/docs/"
echo "  2. Cmd+K → 'warp agent run'"
echo "     - Prompt: 'What's in the operations log?'"
echo "  3. Verify agent reads from docs/OPERATIONS_LOG.md"
read -p "  Pass? (y/n): " test2
echo ""

# Test 3: Shared session
echo "✓ Test 3: Session Sharing"
echo "  1. Settings → Collaboration → Share Session"
echo "  2. Open link in browser (or send to other dev)"
echo "  3. Verify real-time sync"
read -p "  Pass? (y/n): " test3
echo ""

# Test 4: Workflow creation
echo "✓ Test 4: Create Workflow"
echo "  1. Cmd+K → 'Create Workflow'"
echo "  2. Name: 'Test Workflow'"
echo "  3. Command: echo 'Hello from Warp'"
echo "  4. Save and run"
read -p "  Pass? (y/n): " test4
echo ""

# Test 5: Performance
echo "✓ Test 5: Performance Check"
echo "  Run: pytest tests/ -v"
echo "  Expected: No lag, blocks render fast"
read -p "  Pass? (y/n): " test5
echo ""

# Results
echo "=== Evaluation Results ==="
results=($test1 $test2 $test3 $test4 $test5)
pass_count=0
for result in "${results[@]}"; do
  if [ "$result" == "y" ]; then
    ((pass_count++))
  fi
done

echo "Passed: $pass_count/5 tests"
echo ""

if [ $pass_count -ge 4 ]; then
  echo "✅ RECOMMENDATION: Proceed with Warp implementation"
  echo "   Start with revised Phase 1 (Warp + MCP in 1 day)"
elif [ $pass_count -ge 3 ]; then
  echo "⚠️  RECOMMENDATION: Warp shows promise but has issues"
  echo "   Identify blockers before full commitment"
else
  echo "❌ RECOMMENDATION: Warp not suitable for your workflow"
  echo "   Consider alternatives (iTerm2 + tmux improvements)"
fi

echo ""
echo "Next steps saved to: /tmp/warp-next-steps.md"
cat > /tmp/warp-next-steps.md << 'EOF'
# Warp Evaluation Next Steps

## If Passed (4-5 tests)
1. Install on both dev machines
2. Configure MCP servers (see revised plan)
3. Create essential workflows
4. Weekly sync to assess value

## If Marginal (3 tests)
1. Document specific issues
2. Check Warp roadmap for fixes
3. Re-evaluate in 1 month
4. Use selectively for collaboration only

## If Failed (0-2 tests)
1. Uninstall Warp
2. Improve tmux config (see plan alternatives)
3. Focus on gh + MCP without Warp
4. Revisit when Warp Linux support matures
EOF

cat /tmp/warp-next-steps.md
