#!/bin/bash
# Command Validation Hook for Claude Code
# Prevents accidental destructive commands

COMMAND="$1"
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
AUDIT_LOG=".command-audit.log"

# Dangerous patterns that require explicit approval
DANGEROUS_PATTERNS=(
  "sudo\s+(rm|kill|pkill)"
  "sudo\s+systemctl\s+(stop|restart)"
  "rm\s+-rf\s+/"
  "chmod\s+777"
  "sudo\s+passwd"
  ">\s*/etc/"
  "dd\s+if=.*of=/dev/"
)

# Check if command is dangerous
for pattern in "${DANGEROUS_PATTERNS[@]}"; do
  if echo "$COMMAND" | grep -qE "$pattern"; then
    echo "[$TIMESTAMP] BLOCKED: $COMMAND" >> "$AUDIT_LOG"
    echo "🚨 SECURITY: This command requires explicit user approval in the chat."
    echo "Command: $COMMAND"
    echo "Ask user: 'Do you approve executing this command? Type yes to confirm.'"
    exit 1
  fi
done

# Log allowed commands
echo "[$TIMESTAMP] ALLOWED: $COMMAND" >> "$AUDIT_LOG"
exit 0