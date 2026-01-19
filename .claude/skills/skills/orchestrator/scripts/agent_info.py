#!/usr/bin/env python3
"""
Get detailed information about a specific agent.
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

def get_agent_info(agent_id):
    """Get detailed information about a specific agent."""
    registry = load_registry()

    for agent in registry.get("agents", []):
        if agent["id"] == agent_id:
            return {
                "id": agent["id"],
                "name": agent["name"],
                "status": agent.get("status", "unknown"),
                "type": agent.get("type", "unknown"),
                "description": agent["description"],
                "path": agent.get("path", "unknown"),
                "triggers": agent.get("triggers", []),
                "capabilities": agent.get("capabilities", {}),
                "model": agent.get("model", "unknown"),
                "avg_response_time": agent.get("avg_response_time", "unknown"),
                "cost_per_query": agent.get("cost_per_query", "unknown")
            }

    return {
        "error": f"Agent '{agent_id}' not found",
        "available_agents": [a["id"] for a in registry.get("agents", [])]
    }

def main():
    parser = argparse.ArgumentParser(description='Get detailed agent information')
    parser.add_argument('--agent', required=True, help='Agent ID (e.g., vps-monitor)')

    args = parser.parse_args()

    result = get_agent_info(args.agent)
    print(json.dumps(result, indent=2))

    # Exit with error if agent not found
    if "error" in result:
        sys.exit(1)

if __name__ == "__main__":
    main()