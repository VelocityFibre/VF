#!/usr/bin/env python3
"""
Convex Database Agent - Claude Agent SDK Integration
Connects Claude AI with your Convex database for intelligent data operations.
"""

import os
import json
import sys
import requests
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add project root to path for shared imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from shared.base_agent import BaseAgent


class ConvexClient:
    """
    Client for interacting with Convex database.
    Handles all HTTP requests to Convex API.
    """

    def __init__(self, convex_url: str, auth_key: Optional[str] = None):
        """
        Initialize Convex client.

        Args:
            convex_url: The Convex deployment URL
            auth_key: Optional authentication key for sync operations
        """
        self.convex_url = convex_url.rstrip('/')
        self.auth_key = auth_key
        self.headers = {
            "Content-Type": "application/json"
        }
        # Note: Convex auth will be handled per-request if needed
        # Many Convex deployments allow unauthenticated queries

    def call_function(self, function_path: str, args: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Call a Convex function.

        Args:
            function_path: The function path (e.g., "tasks:listTasks")
            args: Function arguments

        Returns:
            The function result
        """
        # Convex uses different endpoint formats
        # Try multiple formats to find the right one
        endpoints_to_try = [
            f"{self.convex_url}/api/query",  # Query endpoint
            f"{self.convex_url}/api/mutation",  # Mutation endpoint
        ]

        # Convert path format: "tasks/listTasks" -> "tasks:listTasks"
        function_name = function_path.replace("/", ":")

        payload = {
            "path": function_name,
            "args": args or {}
        }

        # Try query endpoint first (without auth - many Convex queries are public)
        try:
            # Try without authentication first for queries
            response = requests.post(
                f"{self.convex_url}/api/query",
                json=payload,
                headers=self.headers,
                timeout=10
            )

            if response.status_code == 200:
                result = response.json()
                return result.get("value", result)

            # If query fails with auth error and we have an auth key, try with it
            if response.status_code == 401 and self.auth_key:
                headers_with_auth = self.headers.copy()
                headers_with_auth["Convex-Client"] = self.auth_key
                response = requests.post(
                    f"{self.convex_url}/api/query",
                    json=payload,
                    headers=headers_with_auth,
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

            # If mutation needs auth, try with auth key
            if response.status_code == 401 and self.auth_key:
                headers_with_auth = self.headers.copy()
                headers_with_auth["Convex-Client"] = self.auth_key
                response = requests.post(
                    f"{self.convex_url}/api/mutation",
                    json=payload,
                    headers=headers_with_auth,
                    timeout=10
                )
                if response.status_code == 200:
                    result = response.json()
                    return result.get("value", result)

            return {
                "error": f"Convex API error: {response.status_code} - {response.text}",
                "status": "failed",
                "note": "Function might not exist or requires different authentication"
            }

        except requests.exceptions.RequestException as e:
            return {
                "error": str(e),
                "status": "failed",
                "note": "Check if your Convex deployment is accessible and the function exists"
            }

    def query(self, function_path: str, args: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Execute a Convex query.

        Args:
            function_path: The query function path
            args: Query arguments

        Returns:
            The query result
        """
        return self.call_function(function_path, args)

    def mutation(self, function_path: str, args: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Execute a Convex mutation.

        Args:
            function_path: The mutation function path
            args: Mutation arguments

        Returns:
            The mutation result
        """
        return self.call_function(function_path, args)


class ConvexAgent(BaseAgent):
    """
    AI Agent connected to Convex database.
    Combines Claude's intelligence with your company data.
    Inherits common agent functionality from BaseAgent.
    """

    def __init__(
        self,
        model: str = "claude-3-haiku-20240307",
        convex_url: Optional[str] = None,
        auth_key: Optional[str] = None
    ):
        """
        Initialize the Convex Agent.

        Args:
            model: Claude model to use
            convex_url: Convex deployment URL (from env if not provided)
            auth_key: Sync auth key (from env if not provided)
        """
        # Load API key
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable not set")

        # Initialize base agent
        super().__init__(
            anthropic_api_key=api_key,
            model=model,
            max_tokens=4096
        )

        # Load Convex configuration
        self.convex_url = convex_url or os.environ.get("CONVEX_URL")
        self.auth_key = auth_key or os.environ.get("SYNC_AUTH_KEY")

        if not self.convex_url:
            raise ValueError("CONVEX_URL not provided and not in environment")

        # Initialize Convex client
        self.convex = ConvexClient(self.convex_url, self.auth_key)

    def define_tools(self) -> List[Dict[str, Any]]:
        """
        Define Convex database tools for the agent.
        These tools allow Claude to interact with your database.
        """
        return [
            # Task Management Tools
            {
                "name": "list_tasks",
                "description": "List all tasks from the database. Returns all tasks with their details.",
                "input_schema": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            },
            {
                "name": "add_task",
                "description": "Add a new task to the database. Creates a task with title, description, and status.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "title": {
                            "type": "string",
                            "description": "The task title"
                        },
                        "description": {
                            "type": "string",
                            "description": "Detailed task description"
                        },
                        "status": {
                            "type": "string",
                            "enum": ["pending", "in_progress", "completed"],
                            "description": "Task status"
                        },
                        "priority": {
                            "type": "string",
                            "enum": ["low", "medium", "high"],
                            "description": "Task priority"
                        }
                    },
                    "required": ["title"]
                }
            },
            {
                "name": "get_task",
                "description": "Get details of a specific task by ID.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "taskId": {
                            "type": "string",
                            "description": "The task ID to retrieve"
                        }
                    },
                    "required": ["taskId"]
                }
            },
            {
                "name": "update_task",
                "description": "Update an existing task. Can modify title, description, status, or priority.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "taskId": {
                            "type": "string",
                            "description": "The task ID to update"
                        },
                        "title": {
                            "type": "string",
                            "description": "New task title"
                        },
                        "description": {
                            "type": "string",
                            "description": "New task description"
                        },
                        "status": {
                            "type": "string",
                            "enum": ["pending", "in_progress", "completed"],
                            "description": "New task status"
                        },
                        "priority": {
                            "type": "string",
                            "enum": ["low", "medium", "high"],
                            "description": "New task priority"
                        }
                    },
                    "required": ["taskId"]
                }
            },
            {
                "name": "delete_task",
                "description": "Delete a task from the database by ID.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "taskId": {
                            "type": "string",
                            "description": "The task ID to delete"
                        }
                    },
                    "required": ["taskId"]
                }
            },
            {
                "name": "search_tasks",
                "description": "Search tasks by keyword in title or description.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query keyword"
                        }
                    },
                    "required": ["query"]
                }
            },
            {
                "name": "get_task_stats",
                "description": "Get statistics about tasks (counts by status, priority, etc.).",
                "input_schema": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            },
            # Sync Tools
            {
                "name": "get_sync_stats",
                "description": "Get synchronization statistics and status.",
                "input_schema": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            },
            {
                "name": "get_last_sync_time",
                "description": "Get the timestamp of the last synchronization.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "syncType": {
                            "type": "string",
                            "description": "The type of sync to check"
                        }
                    },
                    "required": []
                }
            }
        ]

    def execute_tool(self, tool_name: str, tool_input: Dict[str, Any]) -> str:
        """
        Execute a Convex tool by calling the appropriate database function.

        Args:
            tool_name: The tool to execute
            tool_input: Tool arguments

        Returns:
            JSON-serialized result
        """
        try:
            # Map tool names to Convex function paths
            function_map = {
                "list_tasks": "tasks/listTasks",
                "add_task": "tasks/addTask",
                "get_task": "tasks/getTask",
                "update_task": "tasks/updateTask",
                "delete_task": "tasks/deleteTask",
                "search_tasks": "tasks/searchTasks",
                "get_task_stats": "tasks/getTaskStats",
                "get_sync_stats": "sync/getSyncStats",
                "get_last_sync_time": "sync/getLastSyncTime"
            }

            if tool_name not in function_map:
                return json.dumps({"error": f"Unknown tool: {tool_name}"})

            function_path = function_map[tool_name]

            # Call Convex function
            result = self.convex.call_function(function_path, tool_input)

            return json.dumps(result, indent=2)

        except Exception as e:
            return json.dumps({
                "error": str(e),
                "tool": tool_name
            })

    def get_system_prompt(self) -> str:
        """
        Get Convex database agent system prompt.

        Returns:
            System prompt for Convex operations
        """
        return """You are a helpful assistant with access to a Convex database.

You can:
- List all available tables in the database
- Query data from tables
- Add new tasks or records
- Update existing records
- Check sync status

Always:
- Explain what you're doing before executing operations
- Format results in a clear, readable way
- Be careful with mutations (add, update operations)
- Provide helpful summaries of the data

When the user asks about data, explore what tables are available first if needed."""


def load_env():
    """Load environment variables from .env file."""
    env_path = os.path.join(os.path.dirname(__file__), '.env')
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key] = value


def main():
    """Demo of Convex Agent capabilities."""
    print("\n" + "="*60)
    print("Convex Database Agent - Demo")
    print("="*60 + "\n")

    # Load environment
    load_env()

    # Initialize agent
    agent = ConvexAgent()

    print("\n" + "="*60)
    print("Example 1: List and Analyze Tasks")
    print("="*60 + "\n")

    response = agent.chat("Show me all tasks and give me a summary of what needs to be done.")
    print(f"Agent: {response}\n")

    print("\n" + "="*60)
    print("Example 2: Get Task Statistics")
    print("="*60 + "\n")

    response = agent.chat("What's the status of our tasks? How many are pending, in progress, and completed?")
    print(f"Agent: {response}\n")

    print("\n" + "="*60)
    print("✅ Demo completed!")
    print("="*60)


if __name__ == "__main__":
    main()
