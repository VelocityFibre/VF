#!/bin/bash

# Port Manager Setup Script
# Creates convenient aliases and symlinks

echo "Setting up Port Manager..."

# Create symlink to main directory
SKILL_DIR="$(cd "$(dirname "$0")" && pwd)"
LINK_DIR="/usr/local/bin"

# Check if we need sudo
if [ -w "$LINK_DIR" ]; then
    SUDO=""
else
    SUDO="sudo"
fi

# Create convenience wrapper script
cat > /tmp/portman << 'SCRIPT'
#!/bin/bash
# Port Manager CLI

SCRIPT_DIR="/home/louisdup/Agents/claude/.claude/skills/port-manager/scripts"

case "$1" in
    list)
        shift
        python3 "$SCRIPT_DIR/list_ports.py" "$@"
        ;;
    check)
        shift
        python3 "$SCRIPT_DIR/check_port.py" "$@"
        ;;
    scan)
        shift
        python3 "$SCRIPT_DIR/scan_ports.py" "$@"
        ;;
    allocate)
        shift
        python3 "$SCRIPT_DIR/allocate_port.py" allocate "$@"
        ;;
    release)
        shift
        python3 "$SCRIPT_DIR/allocate_port.py" release "$@"
        ;;
    suggest)
        shift
        python3 "$SCRIPT_DIR/allocate_port.py" suggest "$@"
        ;;
    sync)
        shift
        python3 "$SCRIPT_DIR/sync_dokploy.py" "$@"
        ;;
    *)
        echo "Port Manager - VF Server Port Management Tool"
        echo ""
        echo "Usage: portman [command] [options]"
        echo ""
        echo "Commands:"
        echo "  list        List all allocated ports"
        echo "  check PORT  Check status of a specific port"
        echo "  scan        Scan for active ports and conflicts"
        echo "  allocate    Allocate a new port"
        echo "  release     Release an allocated port"
        echo "  suggest     Suggest available ports"
        echo "  sync        Sync with Dokploy deployments"
        echo ""
        echo "Examples:"
        echo "  portman list                    # Show all ports"
        echo "  portman list -d                 # Detailed view"
        echo "  portman check 3000              # Check port 3000"
        echo "  portman scan                    # Scan for conflicts"
        echo "  portman allocate myapp -t web  # Allocate web port"
        echo "  portman sync --dry-run         # Preview Dokploy sync"
        ;;
esac
SCRIPT

# Make it executable and install
chmod +x /tmp/portman
$SUDO mv /tmp/portman $LINK_DIR/portman

echo "✓ Port Manager installed successfully!"
echo ""
echo "You can now use 'portman' from anywhere:"
echo "  portman list     - List all ports"
echo "  portman check 3000 - Check specific port"
echo "  portman scan     - Scan for conflicts"
echo "  portman -h       - Show help"
echo ""
echo "Registry file: $SKILL_DIR/config/port_registry.json"
