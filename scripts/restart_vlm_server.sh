#!/bin/bash
# Script to restart VLM server with increased context length

echo "Restarting VLM Server with Increased Context"
echo "============================================="
echo ""

# Step 1: Stop current VLM server
echo "Stopping current VLM server..."
sshpass -p "VeloAdmin2025!" ssh -o StrictHostKeyChecking=no louis@100.96.203.105 '
# Find and kill the VLM process
VLLM_PID=$(ps aux | grep "vllm.entrypoints.openai.api_server" | grep -v grep | awk "{print \$2}" | head -1)

if [ ! -z "$VLLM_PID" ]; then
    echo "Found VLM process: PID $VLLM_PID"
    kill $VLLM_PID
    echo "Sent kill signal to VLM server"
    sleep 5

    # Force kill if still running
    if ps -p $VLLM_PID > /dev/null 2>&1; then
        echo "Force killing VLM process..."
        kill -9 $VLLM_PID
        sleep 2
    fi

    echo "VLM server stopped"
else
    echo "VLM server not running"
fi
'

echo ""
echo "Starting VLM server with increased context (max-model-len: 16384)..."
echo ""

# Step 2: Start VLM server with new configuration
sshpass -p "VeloAdmin2025!" ssh -o StrictHostKeyChecking=no louis@100.96.203.105 '
# Start as velo user (who has access to the vllm environment)
sudo -u velo bash -c "
    source /home/velo/ml/vllm_env/bin/activate

    nohup python -m vllm.entrypoints.openai.api_server \
        --model Qwen/Qwen3-VL-8B-Instruct \
        --dtype bfloat16 \
        --max-model-len 16384 \
        --gpu-memory-utilization 0.85 \
        --max-num-seqs 16 \
        --trust-remote-code \
        --port 8100 \
        --host 0.0.0.0 \
        --allowed-origins '[\"*\"]' \
        > /tmp/vllm.log 2>&1 &

    echo \"VLM server starting...\"
    sleep 3

    # Check if process started
    if ps aux | grep -q \"[v]llm.entrypoints.openai.api_server\"; then
        echo \"VLM server started successfully!\"
        ps aux | grep \"[v]llm.entrypoints.openai.api_server\" | head -1
    else
        echo \"Failed to start VLM server. Check /tmp/vllm.log for errors\"
        tail -20 /tmp/vllm.log
    fi
"
'

echo ""
echo "Waiting for VLM server to initialize (this may take 30-60 seconds)..."
sleep 10

# Step 3: Check server status
echo ""
echo "Checking VLM server health..."
sshpass -p "VeloAdmin2025!" ssh -o StrictHostKeyChecking=no louis@100.96.203.105 '
# Check if server is responding
for i in {1..6}; do
    if curl -s http://localhost:8100/v1/models > /dev/null 2>&1; then
        echo "VLM server is responding!"
        curl -s http://localhost:8100/v1/models | python3 -c "import sys, json; data = json.load(sys.stdin); print(f\"Model: {data['\''data'\''][0]['\''id'\'']}\") if '\''data'\'' in data else print('\''API responding but no models loaded yet'\'')"
        break
    else
        echo "Attempt $i/6: VLM server not ready yet, waiting..."
        sleep 10
    fi
done
'

echo ""
echo "============================================="
echo "VLM Server Configuration Updated!"
echo ""
echo "Configuration:"
echo "  Model: Qwen/Qwen3-VL-8B-Instruct"
echo "  Max Context Length: 16384 tokens (was 8192)"
echo "  Port: 8100"
echo ""
echo "You can now test with:"
echo "  curl -X POST http://100.96.203.105:3005/api/foto/evaluate -H 'Content-Type: application/json' -d '{\"dr_number\": \"DR1734014\"}'"
