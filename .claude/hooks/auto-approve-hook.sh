#!/bin/bash
# Smart Auto-Approval Hook for Claude Code
# Auto-approves safe patterns while maintaining full audit trail

# Configuration
LOG_FILE="/home/louisdup/Agents/claude/logs/auto-approved-commands.log"
NOTIFY_FILE="/home/louisdup/Agents/claude/logs/important-operations.log"
SLACK_WEBHOOK=""  # Add your Slack webhook URL here if you want notifications

# Ensure log directory exists
mkdir -p "$(dirname "$LOG_FILE")"

# Function to log commands
log_command() {
    local command="$1"
    local status="$2"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo "[$timestamp] [$status] $command" >> "$LOG_FILE"

    # Also log as JSON for structured processing
    echo "{\"timestamp\":\"$timestamp\",\"status\":\"$status\",\"command\":\"$command\"}" >> "${LOG_FILE}.jsonl"
}

# Function to send notification for important operations
notify_important() {
    local command="$1"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')

    echo "[$timestamp] IMPORTANT: $command" >> "$NOTIFY_FILE"

    # Send to Slack if configured
    if [ -n "$SLACK_WEBHOOK" ]; then
        curl -X POST -H 'Content-type: application/json' \
             --data "{\"text\":\"🚨 Important Operation: \`$command\`\"}" \
             "$SLACK_WEBHOOK" 2>/dev/null
    fi

    # Desktop notification (if available)
    if command -v notify-send &> /dev/null; then
        notify-send "Claude Agent Operation" "$command" -u normal -i dialog-information
    fi
}

# Get the command being executed
COMMAND="$1"

# Define safe patterns that can be auto-approved
SAFE_PATTERNS=(
    # Read-only operations
    "ps aux"
    "tail -"
    "ls -"
    "cat "
    "grep "
    "find "
    "ss -tlnp"
    "netstat"
    "df -h"
    "free -h"
    "SELECT"  # SQL read queries

    # Cloudflare tunnel operations (your specific case)
    "cloudflared tunnel route dns"
    "cloudflared tunnel list"
)

# Define patterns that need notification but can proceed
NOTIFY_PATTERNS=(
    "systemctl restart"
    "npm run build"
    "git push"
    "DATABASE_URL"
    "cloudflared tunnel route"
)

# Define dangerous patterns that should always prompt
DANGER_PATTERNS=(
    "rm -rf"
    "DROP TABLE"
    "DELETE FROM"
    "pkill -9"
    "kill -9"
    "> /dev/null 2>&1"  # Hiding output
)

# Check if command matches dangerous patterns
for pattern in "${DANGER_PATTERNS[@]}"; do
    if [[ "$COMMAND" == *"$pattern"* ]]; then
        log_command "$COMMAND" "BLOCKED_DANGEROUS"
        echo "REJECT"  # This would block the command
        exit 0
    fi
done

# Check if command matches notify patterns
for pattern in "${NOTIFY_PATTERNS[@]}"; do
    if [[ "$COMMAND" == *"$pattern"* ]]; then
        log_command "$COMMAND" "AUTO_APPROVED_WITH_NOTIFICATION"
        notify_important "$COMMAND"
        echo "APPROVE"  # Auto-approve but notify
        exit 0
    fi
done

# Check if command matches safe patterns
for pattern in "${SAFE_PATTERNS[@]}"; do
    if [[ "$COMMAND" == *"$pattern"* ]]; then
        log_command "$COMMAND" "AUTO_APPROVED_SAFE"
        echo "APPROVE"  # Silently auto-approve
        exit 0
    fi
done

# Default: Log and let Claude Code handle it normally
log_command "$COMMAND" "MANUAL_REVIEW_REQUIRED"
echo "PROMPT"  # Show the normal approval prompt