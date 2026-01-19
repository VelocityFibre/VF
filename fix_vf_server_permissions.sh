#!/bin/bash

# Fix VF Server Service Permissions for Team Access
# This script sets up proper group permissions so all team members can manage services

echo "🔧 Fixing VF Server service permissions for team access..."

# Connect to VF Server
ssh -i ~/.ssh/vf_server_key velo@100.96.203.105 << 'ENDSSH'

# Create management scripts in /opt/team-scripts
sudo mkdir -p /opt/team-scripts
sudo chown root:velocity-team /opt/team-scripts
sudo chmod 775 /opt/team-scripts

# Create VLLM management script
sudo tee /opt/team-scripts/manage-vllm.sh > /dev/null << 'EOF'
#!/bin/bash
# VLLM Management Script - Can be run by any velocity-team member

ACTION=$1

case $ACTION in
    start)
        echo "Starting VLLM service..."
        pkill -f "vllm.entrypoints.openai.api_server" 2>/dev/null
        cd /srv/ml/vllm
        source vllm_env/bin/activate
        nohup python3 -m vllm.entrypoints.openai.api_server \
            --model Qwen/Qwen3-VL-8B-Instruct \
            --trust-remote-code \
            --port 8100 \
            --max-model-len 4096 \
            --gpu-memory-utilization 0.80 \
            --host 0.0.0.0 > /srv/ml/vllm/vllm_service.log 2>&1 &
        echo "VLLM started. Check logs at /srv/ml/vllm/vllm_service.log"
        ;;
    stop)
        echo "Stopping VLLM service..."
        pkill -f "vllm.entrypoints.openai.api_server"
        echo "VLLM stopped"
        ;;
    restart)
        $0 stop
        sleep 2
        $0 start
        ;;
    status)
        if pgrep -f "vllm.entrypoints.openai.api_server" > /dev/null; then
            echo "✅ VLLM is running"
            ps aux | grep "vllm.entrypoints.openai.api_server" | grep -v grep
        else
            echo "❌ VLLM is not running"
        fi
        ;;
    logs)
        tail -f /srv/ml/vllm/vllm_service.log
        ;;
    test)
        echo "Testing VLLM API..."
        curl -s http://localhost:8100/v1/models | python3 -m json.tool
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status|logs|test}"
        exit 1
        ;;
esac
EOF

# Create OCR service management script
sudo tee /opt/team-scripts/manage-ocr.sh > /dev/null << 'EOF'
#!/bin/bash
# OCR Service Management Script - Can be run by any velocity-team member

ACTION=$1

case $ACTION in
    start)
        echo "Starting OCR service..."
        pkill -f "uvicorn main:app" 2>/dev/null
        cd /opt/ocr-service
        source venv/bin/activate
        nohup python -m uvicorn main:app --host 0.0.0.0 --port 8095 --log-level info > ocr_service.log 2>&1 &
        echo "OCR service started. Check logs at /opt/ocr-service/ocr_service.log"
        ;;
    stop)
        echo "Stopping OCR service..."
        pkill -f "uvicorn main:app"
        echo "OCR service stopped"
        ;;
    restart)
        $0 stop
        sleep 2
        $0 start
        ;;
    status)
        if pgrep -f "uvicorn main:app" > /dev/null; then
            echo "✅ OCR service is running"
            ps aux | grep "uvicorn main:app" | grep -v grep
        else
            echo "❌ OCR service is not running"
        fi
        ;;
    logs)
        tail -f /opt/ocr-service/ocr_service.log
        ;;
    test)
        echo "Testing OCR API..."
        curl -s http://localhost:8095/health | python3 -m json.tool
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status|logs|test}"
        exit 1
        ;;
esac
EOF

# Make scripts executable
sudo chmod 755 /opt/team-scripts/manage-vllm.sh
sudo chmod 755 /opt/team-scripts/manage-ocr.sh

# Set proper ownership
sudo chown root:velocity-team /opt/team-scripts/*.sh

# Fix permissions on key directories
sudo chgrp -R velocity-team /srv/ml/vllm
sudo chmod -R g+rw /srv/ml/vllm
sudo chmod g+s /srv/ml/vllm  # Set group sticky bit

# Create sudoers entries for team management (optional, for more control)
echo "# Velocity team service management" | sudo tee /etc/sudoers.d/velocity-team > /dev/null
echo "%velocity-team ALL=(ALL) NOPASSWD: /opt/team-scripts/manage-vllm.sh" | sudo tee -a /etc/sudoers.d/velocity-team
echo "%velocity-team ALL=(ALL) NOPASSWD: /opt/team-scripts/manage-ocr.sh" | sudo tee -a /etc/sudoers.d/velocity-team
echo "%velocity-team ALL=(ALL) NOPASSWD: /usr/bin/pkill -f vllm.entrypoints.openai.api_server" | sudo tee -a /etc/sudoers.d/velocity-team
echo "%velocity-team ALL=(ALL) NOPASSWD: /usr/bin/pkill -f uvicorn main:app" | sudo tee -a /etc/sudoers.d/velocity-team

echo "✅ Permissions fixed! Team scripts created at /opt/team-scripts/"
echo ""
echo "Available commands for all team members:"
echo "  /opt/team-scripts/manage-vllm.sh {start|stop|restart|status|logs|test}"
echo "  /opt/team-scripts/manage-ocr.sh {start|stop|restart|status|logs|test}"

ENDSSH

echo "✅ Script execution complete!"