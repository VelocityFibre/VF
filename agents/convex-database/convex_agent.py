#!/usr/bin/env python3
"""
Convex Database Agent - Claude Agent SDK Integration
Connects Claude AI with your Convex database for intelligent data operations.
"""

import os
import json
import requests
from typing import List, Dict, Any, Optional
from anthropic import Anthropic


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


class ConvexAgent:
    """
    AI Agent connected to Convex database.
    Combines Claude's intelligence with your company data.
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

        self.client = Anthropic(api_key=api_key)
        self.model = model
        self.conversation_history: List[Dict[str, Any]] = []
        self.max_tokens = 4096

        # Load Convex configuration
        self.convex_url = convex_url or os.environ.get("CONVEX_URL")
        self.auth_key = auth_key or os.environ.get("SYNC_AUTH_KEY")

        if not self.convex_url:
            raise ValueError("CONVEX_URL not provided and not in environment")

        # Initialize Convex client
        self.convex = ConvexClient(self.convex_url, self.auth_key)

        print(f"✅ Convex Agent initialized")
        print(f"   Model: {model}")
        print(f"   Convex: {self.convex_url}")

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
            # Contractor Management Tools
            {
                "name": "list_contractors",
                "description": "List all contractors from the database. Can filter by active status.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "activeOnly": {
                            "type": "boolean",
                            "description": "If true, only return active contractors"
                        }
                    },
                    "required": []
                }
            },
            {
                "name": "search_contractors",
                "description": "Search contractors by company name.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query for company name"
                        }
                    },
                    "required": ["query"]
                }
            },
            {
                "name": "get_contractor_stats",
                "description": "Get statistics about contractors (active, inactive counts).",
                "input_schema": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            },
            {
                "name": "add_contractor",
                "description": "Add a new contractor to the database.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "companyName": {
                            "type": "string",
                            "description": "Contractor company name"
                        },
                        "email": {
                            "type": "string",
                            "description": "Contact email"
                        },
                        "phone": {
                            "type": "string",
                            "description": "Contact phone"
                        },
                        "isActive": {
                            "type": "boolean",
                            "description": "Whether contractor is active"
                        }
                    },
                    "required": ["companyName"]
                }
            },
            # Project Management Tools
            {
                "name": "list_projects",
                "description": "List all projects from the database. Can filter by status.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "status": {
                            "type": "string",
                            "description": "Filter by project status (active, planning, completed, on_hold, cancelled)"
                        }
                    },
                    "required": []
                }
            },
            {
                "name": "search_projects",
                "description": "Search projects by name or description.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query for project name"
                        }
                    },
                    "required": ["query"]
                }
            },
            {
                "name": "get_project_stats",
                "description": "Get statistics about projects by status.",
                "input_schema": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            },
            {
                "name": "add_project",
                "description": "Add a new project to the database.",
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
                            "description": "Project status (active, planning, completed)"
                        },
                        "location": {
                            "type": "string",
                            "description": "Project location"
                        }
                    },
                    "required": ["name"]
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
                # Task functions
                "list_tasks": "tasks/listTasks",
                "add_task": "tasks/addTask",
                "get_task": "tasks/getTask",
                "update_task": "tasks/updateTask",
                "delete_task": "tasks/deleteTask",
                "search_tasks": "tasks/searchTasks",
                "get_task_stats": "tasks/getTaskStats",
                # Contractor functions
                "list_contractors": "contractors/list",
                "search_contractors": "contractors/search",
                "get_contractor_stats": "contractors/getStats",
                "add_contractor": "contractors/create",
                # Project functions
                "list_projects": "projects/list",
                "search_projects": "projects/search",
                "get_project_stats": "projects/getStats",
                "add_project": "projects/create",
                # Sync functions
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

    def chat(self, user_message: str) -> str:
        """
        Send a message to the agent and get a response.
        The agent can query and modify your Convex database as needed.

        Args:
            user_message: The user's message

        Returns:
            The agent's response
        """
        # Add user message to history
        self.conversation_history.append({
            "role": "user",
            "content": user_message
        })

        tools = self.define_tools()

        # Continue conversation with tool use
        while True:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                messages=self.conversation_history,
                tools=tools
            )

            # Add assistant's response to history
            self.conversation_history.append({
                "role": "assistant",
                "content": response.content
            })

            # Check if Claude wants to use a tool
            if response.stop_reason == "tool_use":
                # Find tool use blocks
                tool_uses = [block for block in response.content if block.type == "tool_use"]

                if not tool_uses:
                    break

                # Execute each tool
                tool_results = []
                for tool_use in tool_uses:
                    print(f"🔧 Tool: {tool_use.name}")
                    print(f"   Args: {json.dumps(tool_use.input, indent=2)}")

                    result = self.execute_tool(tool_use.name, tool_use.input)
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": tool_use.id,
                        "content": result
                    })
                    print(f"   ✓ Done\n")

                # Add tool results to history
                self.conversation_history.append({
                    "role": "user",
                    "content": tool_results
                })

                # Continue conversation with tool results
                continue

            # Extract text response
            text_blocks = [block.text for block in response.content if hasattr(block, 'text')]
            return "\n".join(text_blocks)

    def reset_conversation(self):
        """Clear the conversation history."""
        self.conversation_history = []


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
