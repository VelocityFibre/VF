#!/bin/bash
# Deploy Autopilot System to FibreFlow
# Run this from ~/Agents/claude directory

set -e  # Exit on error

echo "🚀 Deploying Vibe Coding Transformation to FibreFlow"
echo "====================================================="
echo ""

# Configuration
VF_SERVER="velo@100.96.203.105"
FIBREFLOW_PATH="~/fibreflow-louis"
LOCAL_BASE="$HOME/Agents/claude"

echo "📋 Configuration:"
echo "  VF Server: $VF_SERVER"
echo "  FibreFlow: $FIBREFLOW_PATH"
echo "  Source: $LOCAL_BASE"
echo ""

# Create remote directories
echo "📁 Creating remote directories..."
ssh $VF_SERVER "mkdir -p $FIBREFLOW_PATH/autopilot/{harness,orchestrator,dashboard}"

# Copy Phase 1: E2B Sandboxes
echo "📦 Copying Phase 1: Sandbox Manager..."
scp $LOCAL_BASE/harness/sandbox_manager.py $VF_SERVER:$FIBREFLOW_PATH/autopilot/harness/
scp $LOCAL_BASE/harness/sandbox_config.py $VF_SERVER:$FIBREFLOW_PATH/autopilot/harness/

# Copy Phase 1.5: Reflection
echo "📦 Copying Phase 1.5: Failure Knowledge Base..."
scp $LOCAL_BASE/harness/failure_knowledge_base.py $VF_SERVER:$FIBREFLOW_PATH/autopilot/harness/
scp $LOCAL_BASE/harness/learned_patterns.json $VF_SERVER:$FIBREFLOW_PATH/autopilot/harness/ 2>/dev/null || echo "  (No learned patterns yet - will be created)"

# Copy Phase 2: Tiered Routing
echo "📦 Copying Phase 2: Model Router..."
scp $LOCAL_BASE/orchestrator/model_router.py $VF_SERVER:$FIBREFLOW_PATH/autopilot/orchestrator/

# Copy Phase 2.5: SLA Monitoring
echo "📦 Copying Phase 2.5: SLA Monitor..."
scp $LOCAL_BASE/harness/sla_monitor.py $VF_SERVER:$FIBREFLOW_PATH/autopilot/harness/
scp $LOCAL_BASE/harness/data_layer_slas.yaml $VF_SERVER:$FIBREFLOW_PATH/autopilot/harness/

# Copy Phase 3: Autopilot
echo "📦 Copying Phase 3: Autopilot System..."
scp $LOCAL_BASE/harness/best_of_n_selector.py $VF_SERVER:$FIBREFLOW_PATH/autopilot/harness/
scp $LOCAL_BASE/harness/autopilot_orchestrator.py $VF_SERVER:$FIBREFLOW_PATH/autopilot/harness/

# Copy Phase 4: Dashboard
echo "📦 Copying Phase 4: Digital Twin Dashboard..."
scp $LOCAL_BASE/dashboard/digital_twin_api.py $VF_SERVER:$FIBREFLOW_PATH/autopilot/dashboard/
scp $LOCAL_BASE/dashboard/dashboard.html $VF_SERVER:$FIBREFLOW_PATH/autopilot/dashboard/

# Copy demo contractor dashboard
echo "📦 Copying demo contractor dashboard..."
scp $LOCAL_BASE/demo_contractor_dashboard.tsx $VF_SERVER:$FIBREFLOW_PATH/autopilot/

# Copy documentation
echo "📦 Copying documentation..."
scp $LOCAL_BASE/FIBREFLOW_EVALUATION.md $VF_SERVER:$FIBREFLOW_PATH/autopilot/
scp $LOCAL_BASE/WEEK_1_IMPLEMENTATION_PLAN.md $VF_SERVER:$FIBREFLOW_PATH/autopilot/
scp $LOCAL_BASE/DEMONSTRATION_SUMMARY.md $VF_SERVER:$FIBREFLOW_PATH/autopilot/

echo ""
echo "✅ All files copied to VF Server!"
echo ""

# Install dependencies
echo "📚 Installing Python dependencies on VF Server..."
ssh $VF_SERVER "pip3 install --user e2b-code-interpreter anthropic fastapi uvicorn pyyaml python-multipart aiofiles"

echo ""
echo "🔧 Setting up environment..."
ssh $VF_SERVER "cd $FIBREFLOW_PATH && touch .env.local"
ssh $VF_SERVER "cd $FIBREFLOW_PATH && grep -q E2B_API_KEY .env.local || echo 'E2B_API_KEY=e2b_98a87c7aac72e2377a06f505efd53720a7da1e46' >> .env.local"

echo ""
echo "✅ Testing installation..."
ssh $VF_SERVER "cd $FIBREFLOW_PATH && python3 -c 'import sys; sys.path.insert(0, \"autopilot\"); from harness.best_of_n_selector import BestOfNSelector; print(\"✅ Autopilot system operational!\")'"

echo ""
echo "🎉 DEPLOYMENT COMPLETE!"
echo ""
echo "Next steps:"
echo "1. SSH to VF Server: ssh $VF_SERVER"
echo "2. Navigate to FibreFlow: cd $FIBREFLOW_PATH"
echo "3. Check installation: ls -la autopilot/"
echo "4. Add your ANTHROPIC_API_KEY to .env.local"
echo "5. Ready for Day 2!"
echo ""
