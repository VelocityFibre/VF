#!/bin/bash

# Simple VLLM Manager for Hein - No sudo required
# This can be run by any team member

echo "🚀 Simple VLLM Manager (No sudo needed)"
echo "======================================="

# SSH connection details
SERVER="100.96.203.105"
KEY="$HOME/.ssh/vf_server_key"

# Function to execute commands on server
run_remote() {
    ssh -i "$KEY" velo@$SERVER "$1"
}

case "$1" in
    status)
        echo "📊 Checking VLLM status..."
        run_remote "ps aux | grep 'vllm.*8100' | grep -v grep || echo 'VLLM is not running'"
        echo ""
        echo "🔍 Testing API..."
        curl -s http://$SERVER:8100/v1/models 2>/dev/null | python3 -m json.tool 2>/dev/null || echo "API not responding"
        ;;

    start)
        echo "🚀 Starting VLLM..."
        run_remote "cd /home/velo/ml && source vllm_env/bin/activate && nohup python3 -m vllm.entrypoints.openai.api_server --model Qwen/Qwen3-VL-8B-Instruct --trust-remote-code --port 8100 --max-model-len 4096 --gpu-memory-utilization 0.80 --host 0.0.0.0 > vllm_service.log 2>&1 & echo 'VLLM starting...'"
        sleep 5
        echo "Checking if started..."
        $0 status
        ;;

    stop)
        echo "🛑 Stopping VLLM..."
        run_remote "pkill -f 'vllm.entrypoints.openai.api_server' && echo 'VLLM stopped' || echo 'No VLLM process found'"
        ;;

    restart)
        echo "🔄 Restarting VLLM..."
        $0 stop
        sleep 2
        $0 start
        ;;

    logs)
        echo "📜 Showing recent logs..."
        run_remote "tail -50 /home/velo/ml/vllm_service.log 2>/dev/null || tail -50 /home/velo/ml/vllm_qwen3.log 2>/dev/null || echo 'No log files found'"
        ;;

    test)
        echo "🧪 Testing VLLM API..."
        echo "1. Model list:"
        curl -s http://$SERVER:8100/v1/models | python3 -m json.tool
        echo ""
        echo "2. Health check:"
        curl -s -w "\nHTTP Status: %{http_code}\n" http://$SERVER:8100/health
        ;;

    kill-all)
        echo "☠️  Force killing ALL VLLM processes..."
        run_remote "pkill -9 -f vllm && echo 'All VLLM processes killed'"
        ;;

    *)
        echo "Usage: $0 {status|start|stop|restart|logs|test|kill-all}"
        echo ""
        echo "Commands:"
        echo "  status    - Check if VLLM is running"
        echo "  start     - Start VLLM service"
        echo "  stop      - Stop VLLM service"
        echo "  restart   - Restart VLLM service"
        echo "  logs      - Show recent logs"
        echo "  test      - Test VLLM API"
        echo "  kill-all  - Force kill all VLLM processes"
        echo ""
        echo "Example: $0 restart"
        exit 1
        ;;
esac