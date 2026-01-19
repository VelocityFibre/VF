#!/bin/bash
# Setup workflow reminders - run once to install all reminders

echo "🔧 Setting up FibreFlow Workflow Reminders..."
echo ""

# 1. Add banner to bashrc
echo "1️⃣  Terminal banner..."
if ! grep -q "workflow-banner.sh" ~/.bashrc 2>/dev/null; then
    echo "" >> ~/.bashrc
    echo "# FibreFlow Workflow Reminder" >> ~/.bashrc
    echo "source ~/Agents/claude/.claude/reminders/workflow-banner.sh" >> ~/.bashrc
    echo "   ✅ Added to ~/.bashrc (shows on terminal startup)"
else
    echo "   ⚠️  Already in ~/.bashrc"
fi

# 2. Install git pre-push hook
echo ""
echo "2️⃣  Git pre-push hook..."
chmod +x .git/hooks/pre-push
echo "   ✅ Installed (runs before every git push)"

# 3. Create desktop reminder
echo ""
echo "3️⃣  Desktop checklist..."
cat .claude/reminders/DEPLOYMENT_CHECKLIST.txt
echo ""
echo "   📋 Checklist printed above - save or screenshot it!"

# 4. Add alias for quick reference
echo ""
echo "4️⃣  Quick reference alias..."
if ! grep -q "alias workflow=" ~/.bashrc 2>/dev/null; then
    echo "" >> ~/.bashrc
    echo "# Quick workflow reference" >> ~/.bashrc
    echo "alias workflow='cat ~/Agents/claude/.claude/reminders/DEPLOYMENT_CHECKLIST.txt'" >> ~/.bashrc
    echo "alias modules='cat ~/Agents/claude/.claude/modules/_index.yaml'" >> ~/.bashrc
    echo "   ✅ Added aliases:"
    echo "      • workflow - Show checklist"
    echo "      • modules  - List all modules"
else
    echo "   ⚠️  Aliases already exist"
fi

# 5. VF Server MOTD (optional)
echo ""
echo "5️⃣  VF Server reminder (optional)..."
read -p "   Add reminder to VF Server login? [y/N]: " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    cat > /tmp/vf_motd.sh << 'EOF'
cat << 'BANNER'
╔══════════════════════════════════════════════════════════════╗
║          Welcome to VF Server (FibreFlow Production)         ║
╠══════════════════════════════════════════════════════════════╣
║  ⚠️  BEFORE deploying:                                       ║
║  • Read module profile: cat .claude/modules/{module}.md     ║
║  • Run quality gates: ./sync-to-hostinger --code            ║
╚══════════════════════════════════════════════════════════════╝
BANNER
EOF
    sshpass -p "2025" scp -o StrictHostKeyChecking=no /tmp/vf_motd.sh velo@100.96.203.105:/tmp/
    sshpass -p "2025" ssh -o StrictHostKeyChecking=no velo@100.96.203.105 \
        "cat /tmp/vf_motd.sh >> ~/.bashrc"
    echo "   ✅ Added to VF Server login banner"
fi

echo ""
echo "════════════════════════════════════════════════════════════"
echo "✅ SETUP COMPLETE!"
echo "════════════════════════════════════════════════════════════"
echo ""
echo "Reminders installed:"
echo "  1. Terminal banner (every login)"
echo "  2. Git pre-push hook (blocks unsafe pushes)"
echo "  3. Desktop checklist (print or screenshot)"
echo "  4. Quick aliases (type 'workflow' or 'modules')"
echo ""
echo "To activate changes:"
echo "  source ~/.bashrc"
echo ""
echo "To test:"
echo "  workflow     # Show checklist"
echo "  modules      # List modules"
echo "  git push     # See pre-push reminder"
echo ""
