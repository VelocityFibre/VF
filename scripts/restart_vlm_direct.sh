#!/bin/bash
# Direct approach: Create a script on the server and execute it

echo "Creating restart script on VF server..."

# Create the restart script on the remote server
sshpass -p "VeloAdmin2025!" ssh -o StrictHostKeyChecking=no louis@100.96.203.105 'cat > /tmp/restart_vlm.sh << '\''SCRIPT_END'\''
#!/bin/bash
# Restart VLM server with increased context

echo "Stopping VLM server..."
pkill -f "vllm.entrypoints.openai.api_server"
sleep 5

# Force kill if still running
pkill -9 -f "vllm.entrypoints.openai.api_server" 2>/dev/null
sleep 2

echo "Starting VLM server with max-model-len 16384..."

# Start the server in the background
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
    --allowed-origins '\''["*"]'\'' \
    > /tmp/vllm.log 2>&1 &

echo "VLM server starting in background..."
sleep 5

echo "Current VLM processes:"
ps aux | grep "[v]llm.entrypoints.openai.api_server"

echo ""
echo "Last 10 lines of log:"
tail -10 /tmp/vllm.log
SCRIPT_END

chmod +x /tmp/restart_vlm.sh
'

echo ""
echo "Executing restart script as velo user..."

# Execute the script as the velo user (who owns the vllm environment)
sshpass -p "VeloAdmin2025!" ssh -o StrictHostKeyChecking=no louis@100.96.203.105 \
    'sudo -u velo bash /tmp/restart_vlm.sh'

echo ""
echo "Waiting for VLM server to initialize (30 seconds)..."
sleep 30

echo ""
echo "Checking server status..."
sshpass -p "VeloAdmin2025!" ssh -o StrictHostKeyChecking=no louis@100.96.203.105 '
ps aux | grep "[v]llm.entrypoints.openai.api_server"
echo ""
echo "Checking API health..."
curl -s http://localhost:8100/v1/models | python3 -c "import sys, json; data = json.load(sys.stdin); print(\"Model loaded:\", data['\''data'\''][0]['\''id'\'']) if '\''data'\'' in data else print(\"Still loading...\")"
'

echo ""
echo "VLM restart complete!"
