#!/usr/bin/env python3
"""
Execute a task through a specific agent.
"""

import json
import argparse
import sys
import os
from pathlib import Path

# Add parent directory to path for agent imports
sys.path.append(str(Path(__file__).parent.parent.parent.parent.parent))

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

def execute_agent_task(agent_id, query):
    """Execute a query through a specific agent."""
    registry = load_registry()

    # Find agent in registry
    agent_info = None
    for agent in registry.get("agents", []):
        if agent["id"] == agent_id:
            agent_info = agent
            break

    if not agent_info:
        return {
            "error": f"Agent '{agent_id}' not found",
            "available_agents": [a["id"] for a in registry.get("agents", [])]
        }

    if agent_info.get("status") != "active":
        return {
            "error": f"Agent '{agent_id}' is not active",
            "status": agent_info.get("status", "unknown")
        }

    try:
        # Import and execute based on agent type
        if agent_id == "neon-database":
            from neon_agent import NeonDatabaseAgent

            # Check for required environment variable
            if not os.getenv("NEON_DATABASE_URL"):
                return {"error": "NEON_DATABASE_URL environment variable not set"}

            if not os.getenv("ANTHROPIC_API_KEY"):
                return {"error": "ANTHROPIC_API_KEY environment variable not set"}

            agent = NeonDatabaseAgent(
                database_url=os.getenv("NEON_DATABASE_URL"),
                anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
                model=agent_info.get("model", "claude-3-haiku-20240307")
            )

            response = agent.chat(query)

            return {
                "agent": agent_id,
                "query": query,
                "response": response,
                "model": agent_info.get("model"),
                "success": True
            }

        elif agent_id == "convex-database":
            from convex_agent import ConvexDatabaseAgent

            if not os.getenv("CONVEX_URL"):
                return {"error": "CONVEX_URL environment variable not set"}

            if not os.getenv("ANTHROPIC_API_KEY"):
                return {"error": "ANTHROPIC_API_KEY environment variable not set"}

            agent = ConvexDatabaseAgent(
                convex_url=os.getenv("CONVEX_URL"),
                anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
                model=agent_info.get("model", "claude-3-haiku-20240307")
            )

            response = agent.chat(query)

            return {
                "agent": agent_id,
                "query": query,
                "response": response,
                "model": agent_info.get("model"),
                "success": True
            }

        elif agent_id == "vps-monitor":
            # VPS monitor requires SSH setup
            return {
                "agent": agent_id,
                "query": query,
                "response": "VPS Monitor agent requires SSH configuration. Please use the agent directly.",
                "note": "Run: ./venv/bin/python3 agents/vps-monitor/demo.py",
                "success": False
            }

        else:
            # For other agents, provide guidance
            return {
                "agent": agent_id,
                "query": query,
                "response": f"Agent '{agent_id}' execution not implemented in this script",
                "path": agent_info.get("path"),
                "note": f"Run directly: ./venv/bin/python3 {agent_info.get('path')}/agent.py",
                "success": False
            }

    except ImportError as e:
        return {
            "error": f"Failed to import agent: {str(e)}",
            "agent": agent_id,
            "note": "Make sure the agent module is installed"
        }
    except Exception as e:
        return {
            "error": f"Agent execution failed: {str(e)}",
            "agent": agent_id,
            "query": query
        }

def main():
    parser = argparse.ArgumentParser(description='Execute task through specific agent')
    parser.add_argument('--agent', required=True, help='Agent ID to execute through')
    parser.add_argument('--query', required=True, help='Query to send to agent')

    args = parser.parse_args()

    result = execute_agent_task(args.agent, args.query)
    print(json.dumps(result, indent=2))

    # Exit with error if execution failed
    if "error" in result or not result.get("success", False):
        sys.exit(1)

if __name__ == "__main__":
    main()