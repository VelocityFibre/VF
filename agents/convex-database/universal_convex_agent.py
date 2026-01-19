#!/usr/bin/env python3
"""
Universal Convex Agent - Dynamic Access to ALL Convex Tables

This agent can query ANY table in your Convex deployment without
needing pre-defined tools for each table. Perfect for exploring
the full FibreFlow database.
"""

import os
import json
import requests
from typing import List, Dict, Any, Optional
from anthropic import Anthropic


class UniversalConvexClient:
    """Universal client for any Convex collection."""

    def __init__(self, convex_url: str):
        self.convex_url = convex_url.rstrip('/')
        self.headers = {"Content-Type": "application/json"}
        self.available_tables = []

    def discover_tables(self) -> List[str]:
        """Discover all available tables by trying common patterns."""

        # Known tables from our scan
        known_tables = [
            "tasks", "contractors", "projects", "syncRecords",
            "boqs", "rfqs", "quotes", "materials", "equipment",
            "meetings", "clients", "installations", "activations",
            "poles", "drops", "exports", "financials",
            "lawley_activations", "mohadin_activations",
            "onemap_installations", "onemap_poles",
            "sow_poles", "sow_drops", "nokia_exports",
            "vps_servers", "vps_metrics", "vps_logs",
            "vps_services", "vps_alerts", "sync_mappings"
        ]

        working_tables = []
        for table in known_tables:
            if self.test_table_exists(table):
                working_tables.append(table)

        self.available_tables = working_tables
        return working_tables

    def test_table_exists(self, table_name: str) -> bool:
        """Test if a table exists by trying to query it."""
        try:
            payload = {"path": f"{table_name}:list", "args": {}}
            response = requests.post(
                f"{self.convex_url}/api/query",
                json=payload,
                headers=self.headers,
                timeout=5
            )
            return response.status_code == 200
        except:
            return False

    def query_table(
        self,
        table_name: str,
        limit: Optional[int] = None,
        args: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Query any table using common function patterns."""

        # Try different function naming patterns
        function_patterns = [
            f"{table_name}:list",
            f"{table_name}:listAll",
            f"{table_name}:getAll",
        ]

        query_args = args or {}
        if limit:
            query_args["limit"] = limit

        for pattern in function_patterns:
            try:
                payload = {"path": pattern, "args": query_args}
                response = requests.post(
                    f"{self.convex_url}/api/query",
                    json=payload,
                    headers=self.headers,
                    timeout=10
                )

                if response.status_code == 200:
                    result = response.json()
                    return result.get("value", result)
            except:
                continue

        return {"error": f"Could not query table: {table_name}"}

    def get_table_sample(self, table_name: str, limit: int = 5) -> Dict[str, Any]:
        """Get a sample of records from a table."""
        return self.query_table(table_name, limit=limit)


class UniversalConvexAgent:
    """
    Universal AI Agent that can query ANY table in Convex.

    No need to pre-define tools - it dynamically accesses all 35+ tables!
    """

    def __init__(
        self,
        model: str = "claude-3-haiku-20240307",
        convex_url: Optional[str] = None
    ):
        """Initialize the Universal Convex Agent."""
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable not set")

        self.client = Anthropic(api_key=api_key)
        self.model = model
        self.conversation_history: List[Dict[str, Any]] = []
        self.max_tokens = 4096

        self.convex_url = convex_url or os.environ.get("CONVEX_URL")
        if not self.convex_url:
            raise ValueError("CONVEX_URL not provided")

        self.convex = UniversalConvexClient(self.convex_url)

        # Discover available tables
        print(f"🔍 Discovering available tables...")
        self.available_tables = self.convex.discover_tables()

        print(f"✅ Universal Convex Agent initialized")
        print(f"   Model: {model}")
        print(f"   Convex: {self.convex_url}")
        print(f"   Tables: {len(self.available_tables)} available")

    def define_tools(self) -> List[Dict[str, Any]]:
        """Define universal tools for dynamic table access."""
        return [
            {
                "name": "list_available_tables",
                "description": f"List all {len(self.available_tables)} available tables/collections in the Convex database. Returns table names that can be queried.",
                "input_schema": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            },
            {
                "name": "query_table",
                "description": "Query any table in the database by name. Returns data from the specified table. Available tables include: " + ", ".join(self.available_tables[:10]) + ", and more.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "table_name": {
                            "type": "string",
                            "description": "Name of the table to query (e.g., 'boqs', 'rfqs', 'contractors', 'projects', 'materials', 'equipment')"
                        },
                        "limit": {
                            "type": "number",
                            "description": "Maximum number of records to return (default: 10)"
                        }
                    },
                    "required": ["table_name"]
                }
            },
            {
                "name": "get_table_sample",
                "description": "Get a small sample (5 records) from any table to understand its structure and data.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "table_name": {
                            "type": "string",
                            "description": "Name of the table to sample"
                        }
                    },
                    "required": ["table_name"]
                }
            },
            {
                "name": "search_multiple_tables",
                "description": "Query multiple tables at once to get a comprehensive view. Useful for getting overview data.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "table_names": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of table names to query"
                        },
                        "limit": {
                            "type": "number",
                            "description": "Limit per table"
                        }
                    },
                    "required": ["table_names"]
                }
            }
        ]

    def execute_tool(self, tool_name: str, tool_input: Dict[str, Any]) -> str:
        """Execute a universal tool."""
        try:
            if tool_name == "list_available_tables":
                return json.dumps({
                    "status": "success",
                    "tables": self.available_tables,
                    "total": len(self.available_tables)
                }, indent=2)

            elif tool_name == "query_table":
                table_name = tool_input.get("table_name")
                limit = tool_input.get("limit", 10)

                if table_name not in self.available_tables:
                    return json.dumps({
                        "error": f"Table '{table_name}' not found",
                        "available_tables": self.available_tables
                    }, indent=2)

                result = self.convex.query_table(table_name, limit=limit)
                return json.dumps(result, indent=2)

            elif tool_name == "get_table_sample":
                table_name = tool_input.get("table_name")

                if table_name not in self.available_tables:
                    return json.dumps({
                        "error": f"Table '{table_name}' not found"
                    }, indent=2)

                result = self.convex.get_table_sample(table_name, limit=5)
                return json.dumps(result, indent=2)

            elif tool_name == "search_multiple_tables":
                table_names = tool_input.get("table_names", [])
                limit = tool_input.get("limit", 10)

                results = {}
                for table_name in table_names:
                    if table_name in self.available_tables:
                        results[table_name] = self.convex.query_table(table_name, limit=limit)

                return json.dumps(results, indent=2)

            return json.dumps({"error": f"Unknown tool: {tool_name}"})

        except Exception as e:
            return json.dumps({"error": str(e), "tool": tool_name})

    def chat(self, user_message: str) -> str:
        """Chat with the universal agent."""
        self.conversation_history.append({
            "role": "user",
            "content": user_message
        })

        tools = self.define_tools()

        while True:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                messages=self.conversation_history,
                tools=tools
            )

            self.conversation_history.append({
                "role": "assistant",
                "content": response.content
            })

            if response.stop_reason == "tool_use":
                tool_uses = [block for block in response.content if block.type == "tool_use"]

                if not tool_uses:
                    break

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

                self.conversation_history.append({
                    "role": "user",
                    "content": tool_results
                })
                continue

            text_blocks = [block.text for block in response.content if hasattr(block, 'text')]
            return "\n".join(text_blocks)

    def reset_conversation(self):
        """Clear conversation history."""
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
    """Demo of Universal Convex Agent."""
    print("\n" + "="*70)
    print("UNIVERSAL CONVEX AGENT - Full FibreFlow Access")
    print("="*70 + "\n")

    load_env()
    agent = UniversalConvexAgent()

    # Demo queries
    print("\n" + "="*70)
    print("DEMO: Exploring Your FibreFlow Data")
    print("="*70)

    queries = [
        "What tables are available in the database?",
        "Show me some BOQs (Bill of Quantities)",
        "List RFQs (Request for Quotes)",
        "Show me equipment data",
        "Get a sample of materials",
    ]

    for i, query in enumerate(queries, 1):
        print(f"\n{'─'*70}")
        print(f"Query {i}: {query}")
        print("─"*70)

        try:
            response = agent.chat(query)
            print(f"\n{response}\n")
            agent.reset_conversation()
        except Exception as e:
            print(f"❌ Error: {e}")

    print("\n" + "="*70)
    print("✅ Demo completed!")
    print("\nYou can now ask questions about ANY of these tables:")
    print("  - BOQs, RFQs, Quotes")
    print("  - Materials, Equipment")
    print("  - Contractors, Projects")
    print("  - Meetings, Clients")
    print("  - Installations, Activations")
    print("  - VPS monitoring data")
    print("  - And 20+ more tables!")
    print("="*70)


if __name__ == "__main__":
    main()
