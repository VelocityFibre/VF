#!/usr/bin/env python3
"""
Get recent team context from FF App WhatsApp group
"""

import json
import sys
from pathlib import Path
from datetime import datetime

def get_team_context():
    """Read and display team context"""

    # Read context file
    context_file = Path("/home/louisdup/Agents/claude/TEAM_CONTEXT.md")

    if not context_file.exists():
        print("❌ No team context file found. Bridge may not be running.")
        return

    # Read and display context
    content = context_file.read_text()

    # Check how recent it is
    for line in content.split('\n'):
        if 'Last Updated:' in line:
            print(f"📅 {line.strip()}\n")
            break

    # Display the content
    print(content)

    # Also check tasks file
    tasks_file = Path("/home/louisdup/Agents/claude/TEAM_TASKS.json")
    if tasks_file.exists():
        with open(tasks_file, 'r') as f:
            tasks_data = json.load(f)

        summary = tasks_data.get('summary', {})
        if summary:
            print("\n📊 Task Summary:")
            print(f"   Total: {summary.get('total', 0)}")
            print(f"   Louis: {summary.get('louis', 0)}")
            print(f"   Hein: {summary.get('hein', 0)}")
            print(f"   Unassigned: {summary.get('unassigned', 0)}")

if __name__ == "__main__":
    get_team_context()