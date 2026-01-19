#!/usr/bin/env python3
"""
Contractor Agent - Specialized Agent for VF Contractor Management

Part of the VF Agent Workforce system.
Handles all contractor-related queries and operations.
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

# Add parent directory to path to import ConvexClient
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


class ContractorAgent(BaseAgent):
    """
    Specialized AI Agent for Contractor Management.
    Inherits common agent functionality from BaseAgent.

    Capabilities:
    - List and search contractors
    - Get contractor statistics
    - Add new contractors
    - Analyze contractor data
    """

    def __init__(
        self,
        model: str = "claude-3-haiku-20240307",
        convex_url: Optional[str] = None
    ):
        """Initialize the Contractor Agent."""
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
        """Define contractor management tools."""
        return [
            {
                "name": "list_contractors",
                "description": "List all contractors. Can filter to show only active contractors. Returns company name, contact info, and status.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "activeOnly": {
                            "type": "boolean",
                            "description": "If true, only return active contractors"
                        },
                        "limit": {
                            "type": "number",
                            "description": "Maximum number of contractors to return"
                        }
                    },
                    "required": []
                }
            },
            {
                "name": "search_contractors",
                "description": "Search for contractors by company name. Returns matching contractors.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query for company name (partial match supported)"
                        }
                    },
                    "required": ["query"]
                }
            },
            {
                "name": "get_contractor_stats",
                "description": "Get statistics about contractors including total count, active count, and inactive count.",
                "input_schema": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            },
            {
                "name": "add_contractor",
                "description": "Add a new contractor to the database. Requires company name at minimum.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "company_name": {
                            "type": "string",
                            "description": "Contractor company name"
                        },
                        "email": {
                            "type": "string",
                            "description": "Contact email address"
                        },
                        "phone": {
                            "type": "string",
                            "description": "Contact phone number"
                        },
                        "contact_person": {
                            "type": "string",
                            "description": "Primary contact person name"
                        },
                        "address": {
                            "type": "string",
                            "description": "Business address"
                        },
                        "is_active": {
                            "type": "boolean",
                            "description": "Whether the contractor is active (default: true)"
                        }
                    },
                    "required": ["company_name"]
                }
            }
        ]

    def execute_tool(self, tool_name: str, tool_input: Dict[str, Any]) -> str:
        """Execute a contractor management tool."""
        try:
            function_map = {
                "list_contractors": "contractors/list",
                "search_contractors": "contractors/search",
                "get_contractor_stats": "contractors/getStats",
                "add_contractor": "contractors/create"
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
        Get Contractor agent system prompt.

        Returns:
            System prompt for contractor management
        """
        return """You are a specialized contractor management assistant.

You can:
- List and search contractors
- View contractor details (name, phone, email, specialty)
- Analyze contractor statistics
- Add new contractors to the system

Always:
- Provide clear, formatted contractor information
- Include relevant contact details
- Highlight contractor specialties
- Format phone numbers and emails clearly

When searching, use partial matching and be case-insensitive to help users find contractors easily."""


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
    """Demo of Contractor Agent."""
    print("\n" + "="*60)
    print("Contractor Agent - Demo")
    print("="*60 + "\n")

    load_env()
    agent = ContractorAgent()

    # Test queries
    queries = [
        "How many contractors do we have in total?",
        "List all active contractors",
        "Search for contractors with 'Fiber' in their name"
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
