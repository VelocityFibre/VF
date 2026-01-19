#!/bin/bash

# Automated SSH Setup for Hein
# This script sets up SSH access to VF Server

echo "🔧 Setting up SSH access to VF Server..."

# Check if key already exists
if [ -f ~/.ssh/vf_server_key ]; then
    echo "⚠️  Key already exists at ~/.ssh/vf_server_key"
    read -p "Overwrite? (y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Skipping key setup"
        exit 1
    fi
fi

# Create SSH directory if it doesn't exist
mkdir -p ~/.ssh

# Create the key file
cat > ~/.ssh/vf_server_key << 'EOF'
-----BEGIN OPENSSH PRIVATE KEY-----
b3BlbnNzaC1rZXktdjEAAAAABG5vbmUAAAAEbm9uZQAAAAAAAAABAAAAMwAAAAtzc2gtZW
QyNTUxOQAAACDpGD+QRbI2p3H3BZQITPZAKQdO23awbh57iYrhcCuJpgAAAJgCKVMcAilT
HAAAAAtzc2gtZWQyNTUxOQAAACDpGD+QRbI2p3H3BZQITPZAKQdO23awbh57iYrhcCuJpg
AAAEBsAui/l71IaG9oDFOI7SztM4UAFghiA7vRiiQDU9yVxOkYP5BFsjancfcFlAhM9kAp
B07bdrBuHnuJiuFwK4mmAAAAEnZmLXNlcnZlci0yMDI2MDEwNQECAw==
-----END OPENSSH PRIVATE KEY-----
EOF

# Set correct permissions
chmod 600 ~/.ssh/vf_server_key
echo "✅ SSH key created at ~/.ssh/vf_server_key"

# Add SSH config entry
if ! grep -q "Host vf-server" ~/.ssh/config 2>/dev/null; then
    echo "" >> ~/.ssh/config
    echo "Host vf-server" >> ~/.ssh/config
    echo "  HostName 100.96.203.105" >> ~/.ssh/config
    echo "  User velo" >> ~/.ssh/config
    echo "  IdentityFile ~/.ssh/vf_server_key" >> ~/.ssh/config
    echo "  StrictHostKeyChecking no" >> ~/.ssh/config
    echo "✅ SSH config updated"
fi

# Test connection
echo ""
echo "🧪 Testing connection..."
ssh -i ~/.ssh/vf_server_key -o ConnectTimeout=5 velo@100.96.203.105 'echo "✅ Connection successful!"; hostname'

echo ""
echo "🎉 Setup complete!"
echo ""
echo "You can now connect with:"
echo "  ssh vf-server"
echo "  OR"
echo "  ssh -i ~/.ssh/vf_server_key velo@100.96.203.105"
echo ""
echo "To manage VLLM:"
echo "  ssh vf-server 'ps aux | grep vllm'  # Check status"
echo "  ssh vf-server 'pkill -f vllm'       # Stop VLLM"