#!/bin/bash
# Source this file to enable automatic command monitoring
# Usage: source .claude/hooks/enable-monitoring.sh

LOGGER="/home/louisdup/Agents/claude/.claude/hooks/auto-logger.py"

# Create a wrapper for common dangerous commands
for cmd in systemctl git npm yarn docker docker-compose pkill; do
    if command -v "$cmd" &> /dev/null; then
        eval "
        _original_${cmd}=\$(command -v $cmd)
        ${cmd}() {
            $LOGGER \"$cmd \$@\"
            \$_original_${cmd} \"\$@\"
        }
        "
    fi
done

echo "✅ Command monitoring enabled for: systemctl, git, npm, yarn, docker, pkill"
echo "📊 Dashboard: http://localhost:8002/monitor"
