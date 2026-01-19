#!/usr/bin/env python3
"""
Project Agent - Specialized Agent for VF Project Management

Part of the VF Agent Workforce system.
Handles all project-related queries and operations.
"""

import os
import sys
import json
import requests
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add project root to path for shared imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from shared.base_agent import BaseAgent

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from anthropic import Anthropic


class ConvexClient:
    """Client for Convex database operations."""

    def __init__(self, convex_url: str):
        self.convex_url = convex_url.rstrip('/')
        self.headers = {"Content-Type": "application/json"}

    def call_function(self, function_path: str, args: Dict[str, Any] = None) -> Dict[str, Any]:
        """Call a Convex function."""
        function_name = function_path.replace("/", ":")
        payload = {"path": function_name, "args": args or {}}

        try:
            response = requests.post(
                f"{self.convex_url}/api/query",
                json=payload,
                headers=self.headers,
                timeout=10
            )

            if response.status_code == 200:
                result = response.json()
                return result.get("value", result)

            # Try mutation endpoint
            response = requests.post(
                f"{self.convex_url}/api/mutation",
                json=payload,
                headers=self.headers,
                timeout=10
            )

            if response.status_code == 200:
                result = response.json()
                return result.get("value", result)

            return {
                "error": f"API error: {response.status_code}",
                "status": "failed"
            }
        except Exception as e:
            return {"error": str(e), "status": "failed"}


class ProjectAgent(BaseAgent):
    """
    Specialized AI Agent for Project Management.
    Inherits common agent functionality from BaseAgent.

    Capabilities:
    - List and search projects
    - Get project statistics
    - Add new projects
    - Analyze project data
    - Track project status
    """

    def __init__(
        self,
        model: str = "claude-3-haiku-20240307",
        convex_url: Optional[str] = None
    ):
        """Initialize the Project Agent."""
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable not set")

        # Initialize base agent
        super().__init__(
            anthropic_api_key=api_key,
            model=model,
            max_tokens=4096
        )

        self.convex_url = convex_url or os.environ.get("CONVEX_URL")
        if not self.convex_url:
            raise ValueError("CONVEX_URL not provided")

        self.convex = ConvexClient(self.convex_url)

    def define_tools(self) -> List[Dict[str, Any]]:
        """Define project management tools."""
        return [
            {
                "name": "list_projects",
                "description": "List all projects. Can filter by status (active, planning, completed, on_hold, cancelled). Returns project details including name, status, location.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "status": {
                            "type": "string",
                            "description": "Filter by project status"
                        },
                        "limit": {
                            "type": "number",
                            "description": "Maximum number of projects to return"
                        }
                    },
                    "required": []
                }
            },
            {
                "name": "search_projects",
                "description": "Search for projects by name or description. Returns matching projects.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query for project name (partial match supported)"
                        }
                    },
                    "required": ["query"]
                }
            },
            {
                "name": "get_project_stats",
                "description": "Get statistics about projects including counts by status (active, planning, completed, on_hold, cancelled).",
                "input_schema": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            },
            {
                "name": "add_project",
                "description": "Add a new project to the database. Requires project name at minimum.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "Project name"
                        },
                        "description": {
                            "type": "string",
                            "description": "Project description"
                        },
                        "status": {
                            "type": "string",
                            "description": "Project status (active, planning, completed, on_hold, cancelled)"
                        },
                        "location": {
                            "type": "string",
                            "description": "Project location/site"
                        },
                        "budget": {
                            "type": "number",
                            "description": "Project budget amount"
                        }
                    },
                    "required": ["name"]
                }
            }
        ]

    def execute_tool(self, tool_name: str, tool_input: Dict[str, Any]) -> str:
        """Execute a project management tool."""
        try:
            function_map = {
                "list_projects": "projects/list",
                "search_projects": "projects/search",
                "get_project_stats": "projects/getStats",
                "add_project": "projects/create"
            }

            if tool_name not in function_map:
                return json.dumps({"error": f"Unknown tool: {tool_name}"})

            function_path = function_map[tool_name]
            result = self.convex.call_function(function_path, tool_input)

            return json.dumps(result, indent=2)

        except Exception as e:
            return json.dumps({"error": str(e), "tool": tool_name})

    def get_system_prompt(self) -> str:
        """
        Get Project agent system prompt.

        Returns:
            System prompt for project management
        """
        return """You are a specialized project management assistant.

You can:
- List and search projects
- View project details (name, description, status, contractors)
- Analyze project statistics
- Add new projects to the system
- Track project status and progress

Always:
- Provide clear, formatted project information
- Highlight project status (active, completed, pending)
- Show associated contractor information when relevant
- Format dates and status clearly
- Provide actionable insights

When searching, use partial matching and be case-insensitive to help users find projects easily."""


def load_env():
    """Load environment variables from .env file."""
    env_path = os.path.join(os.path.dirname(__file__), '../../.env')
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key] = value


def main():
    """Demo of Project Agent."""
    print("\n" + "="*60)
    print("Project Agent - Demo")
    print("="*60 + "\n")

    load_env()
    agent = ProjectAgent()

    # Test queries
    queries = [
        "How many projects do we have?",
        "List all active projects",
        "Show me project statistics"
    ]

    for i, query in enumerate(queries, 1):
        print(f"\n{'='*60}")
        print(f"Query {i}: {query}")
        print("="*60 + "\n")

        response = agent.chat(query)
        print(f"Agent: {response}\n")

        agent.reset_conversation()

    print("\n" + "="*60)
    print("✅ Demo completed!")
    print("="*60)


if __name__ == "__main__":
    main()
