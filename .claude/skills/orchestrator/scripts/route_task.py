#!/usr/bin/env python3
"""
Route tasks to appropriate agents based on keyword matching.
"""

import json
import argparse
import sys
from pathlib import Path

# Load registry
REGISTRY_PATH = Path(__file__).parent.parent.parent.parent.parent / "orchestrator" / "registry.json"

def load_registry():
    """Load agent registry from JSON file."""
    try:
        with open(REGISTRY_PATH, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(json.dumps({"error": f"Failed to load registry: {str(e)}"}))
        sys.exit(1)

def find_agent_for_task(task_description, registry):
    """Find best agent(s) for a given task based on keywords."""
    task_lower = task_description.lower()
    matches = []

    for agent in registry.get("agents", []):
        if agent.get("status") != "active":
            continue

        score = 0
        matched_triggers = []

        # Check trigger keywords
        for trigger in agent.get("triggers", []):
            if trigger.lower() in task_lower:
                score += 1
                matched_triggers.append(trigger)

        if score > 0:
            matches.append({
                "agent_id": agent["id"],
                "agent_name": agent["name"],
                "confidence": score,
                "matched_keywords": matched_triggers,
                "description": agent["description"],
                "path": agent.get("path", ""),
                "model": agent.get("model", "unknown"),
                "cost_per_query": agent.get("cost_per_query", "unknown")
            })

    # Sort by confidence (highest first)
    matches.sort(key=lambda x: x["confidence"], reverse=True)
    return matches

def route_task(task_description, auto_select=False):
    """Route a task to the appropriate agent."""
    registry = load_registry()
    matches = find_agent_for_task(task_description, registry)

    if not matches:
        return {
            "status": "no_match",
            "message": "No specialized agent found for this task",
            "suggestion": "Try rephrasing with specific keywords or list available agents",
            "task": task_description
        }

    if auto_select or (len(matches) == 1):
        result = {
            "status": "routed",
            "agent": matches[0],
            "alternatives": matches[1:] if len(matches) > 1 else [],
            "task": task_description
        }
    elif matches[0]["confidence"] >= 3:
        # High confidence, suggest primary agent
        result = {
            "status": "high_confidence",
            "agent": matches[0],
            "alternatives": matches[1:],
            "task": task_description
        }
    else:
        # Multiple options, let user choose
        result = {
            "status": "multiple_matches",
            "message": f"Found {len(matches)} agents that can handle this task",
            "options": matches,
            "task": task_description
        }

    return result

def main():
    parser = argparse.ArgumentParser(description='Route tasks to appropriate agents')
    parser.add_argument('--task', required=True, help='Task description to route')
    parser.add_argument('--auto-select', action='store_true',
                       help='Automatically select best match')

    args = parser.parse_args()

    result = route_task(args.task, args.auto_select)
    print(json.dumps(result, indent=2))

    # Exit with appropriate code
    if result["status"] in ["routed", "high_confidence"]:
        sys.exit(0)
    elif result["status"] == "multiple_matches":
        sys.exit(0)  # Success, but multiple options
    else:
        sys.exit(1)  # No match found

if __name__ == "__main__":
    main()