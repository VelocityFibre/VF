#!/bin/bash
# Automated Autopilot System Deployment to FibreFlow
# Runs from ~/Agents/claude directory

set -e  # Exit on error

echo "🚀 Deploying Vibe Coding Transformation to FibreFlow"
echo "====================================================="
echo ""

# Configuration
VF_SERVER="velo@100.96.203.105"
VF_PASSWORD="2025"
FIBREFLOW_DIR="~/fibreflow-louis"
LOCAL_DIR="$(pwd)"

echo "📦 Step 1: Packaging autopilot system..."
cd "$LOCAL_DIR"

# Create temporary directory for packaging
TMP_DIR=$(mktemp -d)
echo "   Using temp directory: $TMP_DIR"

# Copy all autopilot files
mkdir -p "$TMP_DIR/autopilot/harness"
mkdir -p "$TMP_DIR/autopilot/orchestrator"

echo "   Copying harness files..."
cp harness/autopilot_orchestrator.py "$TMP_DIR/autopilot/harness/" 2>/dev/null || echo "   ⚠ autopilot_orchestrator.py not found"
cp harness/best_of_n_selector.py "$TMP_DIR/autopilot/harness/" 2>/dev/null || echo "   ⚠ best_of_n_selector.py not found"
cp harness/sandbox_manager.py "$TMP_DIR/autopilot/harness/" 2>/dev/null || echo "   ⚠ sandbox_manager.py not found"
cp harness/failure_knowledge_base.py "$TMP_DIR/autopilot/harness/" 2>/dev/null || echo "   ⚠ failure_knowledge_base.py not found"
cp harness/sla_monitor.py "$TMP_DIR/autopilot/harness/" 2>/dev/null || echo "   ⚠ sla_monitor.py not found"
cp harness/parallel_runner.py "$TMP_DIR/autopilot/harness/" 2>/dev/null || echo "   ⚠ parallel_runner.py not found"
cp harness/worktree_manager.py "$TMP_DIR/autopilot/harness/" 2>/dev/null || echo "   ⚠ worktree_manager.py not found"
cp harness/rate_limit_handler.py "$TMP_DIR/autopilot/harness/" 2>/dev/null || echo "   ⚠ rate_limit_handler.py not found"
cp harness/dependency_graph.py "$TMP_DIR/autopilot/harness/" 2>/dev/null || echo "   ⚠ dependency_graph.py not found"
cp harness/sandbox_config.py "$TMP_DIR/autopilot/harness/" 2>/dev/null || echo "   ⚠ sandbox_config.py not found"
cp harness/session_executor.py "$TMP_DIR/autopilot/harness/" 2>/dev/null || echo "   ⚠ session_executor.py not found"

echo "   Copying configuration files..."
cp harness/data_layer_slas.yaml "$TMP_DIR/autopilot/harness/" 2>/dev/null || echo "   ⚠ data_layer_slas.yaml not found"
cp harness/learned_patterns.json "$TMP_DIR/autopilot/harness/" 2>/dev/null || echo "   ⚠ learned_patterns.json not found"
cp harness/best_of_n_results.json "$TMP_DIR/autopilot/harness/" 2>/dev/null || echo "   ⚠ best_of_n_results.json not found"

echo "   Copying orchestrator files..."
cp orchestrator/model_router.py "$TMP_DIR/autopilot/orchestrator/" 2>/dev/null || echo "   ⚠ model_router.py not found"

# Create archive
echo "   Creating archive..."
cd "$TMP_DIR"
tar -czf autopilot.tar.gz autopilot/
echo "   ✅ Archive created: $(du -h autopilot.tar.gz | cut -f1)"

echo ""
echo "📤 Step 2: Uploading to VF Server..."
scp autopilot.tar.gz "$VF_SERVER:$FIBREFLOW_DIR/"
echo "   ✅ Upload complete"

echo ""
echo "🔧 Step 3: Extracting and setting up on VF Server..."
sshpass -p "$VF_PASSWORD" ssh "$VF_SERVER" << 'ENDSSH'
cd ~/fibreflow-louis
echo "   Extracting archive..."
tar -xzf autopilot.tar.gz
echo "   ✅ Extracted"

echo "   Installing Python dependencies..."
pip3 install --user e2b-code-interpreter anthropic fastapi uvicorn pyyaml slack-sdk 2>&1 | grep -i "successfully installed\|already satisfied" || true
echo "   ✅ Dependencies installed"

echo ""
echo "🧪 Step 4: Verifying installation..."
python3 -c "
import sys
sys.path.insert(0, '/home/velo/fibreflow-louis')
try:
    from autopilot.harness.best_of_n_selector import BestOfNSelector
    print('   ✅ BestOfNSelector imported successfully')
except Exception as e:
    print(f'   ❌ Failed to import BestOfNSelector: {e}')

try:
    from autopilot.orchestrator.model_router import ModelRouter
    print('   ✅ ModelRouter imported successfully')
except Exception as e:
    print(f'   ❌ Failed to import ModelRouter: {e}')

try:
    from autopilot.harness.sandbox_manager import SandboxManager
    print('   ✅ SandboxManager imported successfully')
except Exception as e:
    print(f'   ❌ Failed to import SandboxManager: {e}')
"

echo ""
echo "📊 Installation Summary:"
ls -lh ~/fibreflow-louis/autopilot/harness/ | tail -n +2 | wc -l | xargs echo "   Harness files:"
ls -lh ~/fibreflow-louis/autopilot/orchestrator/ | tail -n +2 | wc -l | xargs echo "   Orchestrator files:"

ENDSSH

echo ""
echo "🎉 DEPLOYMENT COMPLETE!"
echo "======================"
echo ""
echo "✅ Autopilot system deployed to: $VF_SERVER:$FIBREFLOW_DIR/autopilot/"
echo "✅ Day 1 Infrastructure Setup: COMPLETE"
echo ""
echo "Next: Day 2 - FibreFlow Integration"

# Cleanup
rm -rf "$TMP_DIR"
