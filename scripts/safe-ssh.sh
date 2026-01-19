#!/bin/bash
# Safe SSH Command Wrapper
# Usage: ./safe-ssh.sh <server> <command>
# Automatically logs destructive commands and requires approval

set -e

SERVER="$1"
COMMAND="$2"
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
AUDIT_LOG=".server-audit.log"

# Destructive command patterns
DESTRUCTIVE_PATTERNS=(
    "sudo.*kill"
    "sudo.*pkill"
    "sudo.*systemctl.*(restart|stop)"
    "sudo.*rm"
    "sudo.*passwd"
    "sudo.*apt"
    "sudo.*nano"
    "sudo.*vim"
    "sudo.*chmod"
    "sudo.*chown"
    "rm -rf"
)

# Check if command is destructive
is_destructive() {
    local cmd="$1"
    for pattern in "${DESTRUCTIVE_PATTERNS[@]}"; do
        if echo "$cmd" | grep -qE "$pattern"; then
            return 0  # True - is destructive
        fi
    done
    return 1  # False - is safe
}

# Log to audit trail
log_command() {
    local result="$1"
    echo "[$TIMESTAMP] [claude-code] [$SERVER] [$COMMAND] [$result]" >> "$AUDIT_LOG"
}

# Execute command
if is_destructive "$COMMAND"; then
    echo "⚠️  DESTRUCTIVE COMMAND DETECTED"
    echo "Server: $SERVER"
    echo "Command: $COMMAND"
    echo ""
    echo "This command could impact production services."
    echo "Has user explicitly approved this? (yes/no)"

    # In automation context, this should fail
    echo "❌ BLOCKED: Destructive command requires explicit user approval in Claude Code chat"
    log_command "❌ BLOCKED - No approval"
    exit 1
else
    # Safe command - execute
    ssh -i ~/.ssh/vf_server_key "$SERVER" "$COMMAND"
    log_command "✅ SAFE - Auto-executed"
fi
