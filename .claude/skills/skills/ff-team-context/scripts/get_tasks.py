#!/usr/bin/env python3
"""
Get tasks for a specific developer
"""

import json
import sys
from pathlib import Path
from datetime import datetime

def get_my_tasks(developer=None):
    """Get tasks for a specific developer"""

    # Get developer from command line if not provided
    if not developer and len(sys.argv) > 1:
        developer = sys.argv[1].lower()

    # Read tasks file
    tasks_file = Path("/home/louisdup/Agents/claude/TEAM_TASKS.json")

    if not tasks_file.exists():
        print("❌ No tasks file found. Bridge may not be running.")
        return

    with open(tasks_file, 'r') as f:
        tasks_data = json.load(f)

    tasks = tasks_data.get('tasks', [])
    updated = tasks_data.get('updated', 'Unknown')

    print(f"📋 Team Tasks (Updated: {updated})\n")

    if not developer:
        # Show all tasks grouped by assignee
        louis_tasks = [t for t in tasks if t.get('assigned_to') == 'louis']
        hein_tasks = [t for t in tasks if t.get('assigned_to') == 'hein']
        unassigned = [t for t in tasks if t.get('assigned_to') == 'unassigned']

        if louis_tasks:
            print("### Louis")
            for task in louis_tasks:
                status_emoji = "✅" if task.get('status') == 'completed' else "⏳" if task.get('status') == 'in_progress' else "📌"
                print(f"  {status_emoji} {task.get('description', 'No description')}")
            print()

        if hein_tasks:
            print("### Hein")
            for task in hein_tasks:
                status_emoji = "✅" if task.get('status') == 'completed' else "⏳" if task.get('status') == 'in_progress' else "📌"
                print(f"  {status_emoji} {task.get('description', 'No description')}")
            print()

        if unassigned:
            print("### Unassigned")
            for task in unassigned:
                print(f"  🔴 {task.get('description', 'No description')}")
            print()

    else:
        # Show tasks for specific developer
        my_tasks = [t for t in tasks if t.get('assigned_to') == developer.lower()]

        if my_tasks:
            print(f"### Tasks for {developer.capitalize()}")
            for task in my_tasks:
                status_emoji = "✅" if task.get('status') == 'completed' else "⏳" if task.get('status') == 'in_progress' else "📌"
                print(f"  {status_emoji} {task.get('description', 'No description')}")
                print(f"      From: {task.get('sender', 'Unknown')}")
                print(f"      When: {task.get('timestamp', 'Unknown')}")
                print()
        else:
            print(f"No tasks found for {developer}")

    # Show summary
    summary = tasks_data.get('summary', {})
    if summary:
        print("\n📊 Summary:")
        print(f"   Total tasks: {summary.get('total', 0)}")
        print(f"   Louis: {summary.get('louis', 0)}")
        print(f"   Hein: {summary.get('hein', 0)}")
        print(f"   Unassigned: {summary.get('unassigned', 0)}")

if __name__ == "__main__":
    get_my_tasks()