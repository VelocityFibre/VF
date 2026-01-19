#!/bin/bash
# Simple Sudo Monitoring Script
# Sends alerts to Slack/Discord when sudo commands are executed

# Configuration
WEBHOOK_URL="${SLACK_WEBHOOK_URL:-https://hooks.slack.com/services/YOUR/WEBHOOK/URL}"
LOG_FILE="/var/log/auth.log"
STATE_FILE="/tmp/.sudo-monitor-state"

# Get last processed line number
LAST_LINE=$(cat "$STATE_FILE" 2>/dev/null || echo 0)
CURRENT_LINE=$(wc -l < "$LOG_FILE")

# Process new lines only
tail -n +"$((LAST_LINE + 1))" "$LOG_FILE" | while read -r line; do
  if echo "$line" | grep -q "sudo.*COMMAND"; then
    # Extract details
    TIMESTAMP=$(echo "$line" | cut -d' ' -f1-3)
    USER=$(echo "$line" | grep -oP 'USER=\K\w+')
    TTY=$(echo "$line" | grep -oP 'TTY=\K[^ ]+')
    PWD=$(echo "$line" | grep -oP 'PWD=\K[^ ]+')
    COMMAND=$(echo "$line" | grep -oP 'COMMAND=\K.*')

    # Determine severity
    if echo "$COMMAND" | grep -qE "(kill|restart|stop|rm|passwd)"; then
      EMOJI="🚨"
      COLOR="danger"
    elif echo "$COMMAND" | grep -q "systemctl status"; then
      EMOJI="✅"
      COLOR="good"
    else
      EMOJI="ℹ️"
      COLOR="warning"
    fi

    # Send to Slack/Discord
    curl -X POST "$WEBHOOK_URL" \
      -H 'Content-Type: application/json' \
      -d "{
        \"text\": \"$EMOJI Sudo Command Executed\",
        \"attachments\": [{
          \"color\": \"$COLOR\",
          \"fields\": [
            {\"title\": \"User\", \"value\": \"$USER\", \"short\": true},
            {\"title\": \"Time\", \"value\": \"$TIMESTAMP\", \"short\": true},
            {\"title\": \"Command\", \"value\": \"\`$COMMAND\`\", \"short\": false},
            {\"title\": \"Directory\", \"value\": \"$PWD\", \"short\": true},
            {\"title\": \"Terminal\", \"value\": \"$TTY\", \"short\": true}
          ]
        }]
      }" 2>/dev/null

    # Log locally too
    echo "[$TIMESTAMP] $USER: $COMMAND" >> /var/log/sudo-monitor.log
  fi
done

# Update state
echo "$CURRENT_LINE" > "$STATE_FILE"