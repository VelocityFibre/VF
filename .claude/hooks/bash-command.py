#!/usr/bin/env python3
"""
Bash Command Hook for Claude Code Auto-Approval Monitoring
Logs all bash commands to structured JSON for dashboard consumption
"""

import json
import sys
from datetime import datetime
from pathlib import Path

# Configuration
LOG_FILE = Path("/home/louisdup/Agents/claude/logs/agent-commands.jsonl")

# Ensure log directory exists
LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

def categorize_command(command: str) -> str:
    """Categorize command for monitoring"""
    cmd_lower = command.lower()

    if "vf_server" in cmd_lower:
        return "VF Server"
    elif "cloudflared" in cmd_lower or "tunnel" in cmd_lower:
        return "Cloudflare"
    elif any(x in cmd_lower for x in ["git", "clone", "push", "pull"]):
        return "Git"
    elif any(x in cmd_lower for x in ["ps", "tail", "grep", "ls", "ss", "netstat"]):
        return "Monitoring"
    elif any(x in cmd_lower for x in ["mkdir", "cp", "mv", "cat", "rm"]):
        return "File Ops"
    elif any(x in cmd_lower for x in ["npm", "pip", "yarn"]):
        return "Build"
    elif any(x in cmd_lower for x in ["systemctl", "service"]):
        return "System"
    else:
        return "Other"

def determine_status(command: str) -> str:
    """Determine approval status based on command patterns"""
    cmd_lower = command.lower()

    # Dangerous patterns - would be blocked
    danger_patterns = ["rm -rf", "drop table", "delete from", "truncate table"]
    if any(pattern in cmd_lower for pattern in danger_patterns):
        return "blocked"

    # Important patterns - notify but approve
    notify_patterns = ["git push", "systemctl restart", "npm run build", "deploy"]
    if any(pattern in cmd_lower for pattern in notify_patterns):
        return "notified"

    # Safe patterns - auto approve
    safe_patterns = [
        "ps aux", "tail", "ls", "cat", "grep", "find", "ss", "netstat",
        "df", "free", "select", "mkdir", "pwd", "echo", "curl"
    ]
    if any(pattern in cmd_lower for pattern in safe_patterns):
        return "auto_approved"

    # Default: manual review needed
    return "manual"

def log_command(command: str):
    """Log command to JSONL file"""
    entry = {
        "timestamp": datetime.now().isoformat(),
        "command": command,
        "status": determine_status(command),
        "category": categorize_command(command),
        "agent": "claude"
    }

    with open(LOG_FILE, 'a') as f:
        f.write(json.dumps(entry) + '\n')

if __name__ == "__main__":
    # Get command from stdin or args
    if len(sys.argv) > 1:
        command = ' '.join(sys.argv[1:])
    else:
        command = sys.stdin.read().strip()

    if command:
        log_command(command)

    # Return APPROVE to auto-approve (or PROMPT/REJECT to modify behavior)
    print("APPROVE")
    sys.exit(0)
