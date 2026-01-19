#!/bin/bash
# Setup Auto-Approval System for Claude Code Agents

set -e

echo "🚀 Setting up Claude Code Auto-Approval System"
echo "============================================="
echo ""

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p /home/louisdup/Agents/claude/logs
mkdir -p /home/louisdup/Agents/claude/.claude/hooks

# Set correct permissions
echo "🔐 Setting permissions..."
chmod +x /home/louisdup/Agents/claude/scripts/monitor-agents.py 2>/dev/null || true
chmod +x /home/louisdup/Agents/claude/.claude/hooks/auto-approve-hook.sh 2>/dev/null || true

# Install Python dependencies if needed
echo "📦 Checking Python dependencies..."
if ! python3 -c "import rich" 2>/dev/null; then
    echo "Installing rich library for monitoring dashboard..."
    pip3 install rich --user
fi

# Create initial log files
touch /home/louisdup/Agents/claude/logs/auto-approved-commands.log
touch /home/louisdup/Agents/claude/logs/agent-commands.jsonl
touch /home/louisdup/Agents/claude/logs/important-operations.log

echo ""
echo "✅ Setup Complete!"
echo ""
echo "📋 Quick Start Guide:"
echo "===================="
echo ""
echo "1. IMMEDIATE SOLUTION (For current session):"
echo "   When you see the approval prompt, select option 2:"
echo "   'Yes, and don't ask again for similar commands in /home/louisdup/Agents/claude'"
echo ""
echo "2. MONITOR COMMANDS (In separate terminal):"
echo "   ./scripts/monitor-agents.py watch    # Interactive dashboard"
echo "   ./scripts/monitor-agents.py tail     # Real-time log tail"
echo ""
echo "3. VIEW STATISTICS:"
echo "   ./scripts/monitor-agents.py stats"
echo ""
echo "4. CHECK LOGS:"
echo "   tail -f logs/auto-approved-commands.log      # All commands"
echo "   tail -f logs/important-operations.log        # Important operations only"
echo ""
echo "5. CUSTOMIZE AUTO-APPROVAL:"
echo "   Edit: .claude/approved-commands.yaml"
echo "   Add patterns for commands you trust"
echo ""
echo "💡 Pro Tips:"
echo "- Use option 2 in Claude Code for immediate relief"
echo "- Keep monitor running in a tmux/screen session"
echo "- Review logs daily for security"
echo "- Dangerous commands are always blocked"
echo ""
echo "🎯 Your specific Cloudflare DNS commands are pre-configured for auto-approval!"
echo ""