#!/usr/bin/env python3
"""
Automatic Command Logger for Claude Code
Monitors bash command execution and logs to dashboard automatically
"""

import json
import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

LOG_FILE = Path("/home/louisdup/Agents/claude/logs/agent-commands.jsonl")
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
    elif any(x in cmd_lower for x in ["npm", "pip", "yarn", "npx"]):
        return "Build"
    elif any(x in cmd_lower for x in ["systemctl", "service"]):
        return "System"
    elif any(x in cmd_lower for x in ["curl", "wget", "http"]):
        return "Network"
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
    notify_patterns = ["git push", "systemctl restart", "npm run build", "deploy", "pkill", "kill "]
    if any(pattern in cmd_lower for pattern in notify_patterns):
        return "notified"

    # Safe patterns - auto approve
    safe_patterns = [
        "ps aux", "tail", "ls", "cat", "grep", "find", "ss", "netstat",
        "df", "free", "select", "mkdir", "pwd", "echo", "curl", "wc"
    ]
    if any(pattern in cmd_lower for pattern in safe_patterns):
        return "auto_approved"

    # Default: manual review needed
    return "manual"

def log_command(command: str, source: str = "claude"):
    """Log command to JSONL file"""
    # Skip logging the logger itself
    if "auto-logger.py" in command or "agent-commands.jsonl" in command:
        return

    entry = {
        "timestamp": datetime.now().isoformat(),
        "command": command,
        "status": determine_status(command),
        "category": categorize_command(command),
        "agent": source
    }

    try:
        with open(LOG_FILE, 'a') as f:
            f.write(json.dumps(entry) + '\n')
    except Exception as e:
        # Silent fail - don't break command execution
        pass

# If called directly, log the command from arguments
if __name__ == "__main__":
    if len(sys.argv) > 1:
        command = ' '.join(sys.argv[1:])
        log_command(command)
