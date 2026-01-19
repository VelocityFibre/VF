#!/usr/bin/env python3
"""
Neon Database Agent - Claude Agent SDK Integration
Connects Claude AI with your Neon PostgreSQL database for intelligent data operations.
"""

import os
import json
import psycopg2
from psycopg2.extras import RealDictCursor
from typing import List, Dict, Any, Optional
from anthropic import Anthropic


class PostgresClient:
    """
    Client for interacting with PostgreSQL/Neon database.
    Handles all database connections and queries.
    """

    def __init__(self, connection_string: str):
        """
        Initialize PostgreSQL client.

        Args:
            connection_string: PostgreSQL connection string
        """
        self.connection_string = connection_string
        self.connection = None

    def connect(self):
        """Establish database connection."""
        if not self.connection or self.connection.closed:
            self.connection = psycopg2.connect(
                self.connection_string,
                cursor_factory=RealDictCursor
            )
        return self.connection

    def close(self):
        """Close database connection."""
        if self.connection and not self.connection.closed:
            self.connection.close()

    def execute_query(self, query: str, params: tuple = None) -> List[Dict[str, Any]]:
        """
        Execute a SELECT query and return results.

        Args:
            query: SQL query string
            params: Query parameters (for parameterized queries)

        Returns:
            List of result rows as dictionaries
        """
        try:
            conn = self.connect()
            with conn.cursor() as cursor:
                cursor.execute(query, params)
                results = cursor.fetchall()
                return [dict(row) for row in results]
        except Exception as e:
            return {"error": str(e), "query": query}

    def execute_mutation(self, query: str, params: tuple = None) -> Dict[str, Any]:
        """
        Execute an INSERT, UPDATE, or DELETE query.

        Args:
            query: SQL query string
            params: Query parameters

        Returns:
            Result dictionary with rowcount and status
        """
        try:
            conn = self.connect()
            with conn.cursor() as cursor:
                cursor.execute(query, params)
                conn.commit()
                return {
                    "success": True,
                    "rowcount": cursor.rowcount,
                    "message": f"Query executed successfully. {cursor.rowcount} row(s) affected."
                }
        except Exception as e:
            if conn:
                conn.rollback()
            return {"error": str(e), "success": False, "query": query}

    def list_tables(self) -> List[Dict[str, Any]]:
        """
        List all tables in the database.

        Returns:
            List of table information
        """
        query = """
            SELECT
                table_name,
                table_type
            FROM information_schema.tables
            WHERE table_schema = 'public'
            ORDER BY table_name;
        """
        return self.execute_query(query)

    def describe_table(self, table_name: str) -> List[Dict[str, Any]]:
        """
        Get schema information for a specific table.

        Args:
            table_name: Name of the table

        Returns:
            List of column information
        """
        query = """
            SELECT
                column_name,
                data_type,
                character_maximum_length,
                is_nullable,
                column_default
            FROM information_schema.columns
            WHERE table_schema = 'public'
              AND table_name = %s
            ORDER BY ordinal_position;
        """
        return self.execute_query(query, (table_name,))

    def get_table_stats(self, table_name: str) -> Dict[str, Any]:
        """
        Get statistics for a table (row count, size, etc.).

        Args:
            table_name: Name of the table

        Returns:
            Table statistics
        """
        try:
            # Get row count
            count_query = f"SELECT COUNT(*) as count FROM {table_name};"
            count_result = self.execute_query(count_query)

            # Get table size
            size_query = """
                SELECT
                    pg_size_pretty(pg_total_relation_size(%s)) as total_size,
                    pg_size_pretty(pg_relation_size(%s)) as table_size
            """
            size_result = self.execute_query(size_query, (table_name, table_name))

            return {
                "table_name": table_name,
                "row_count": count_result[0]["count"] if count_result else 0,
                "total_size": size_result[0]["total_size"] if size_result else "Unknown",
                "table_size": size_result[0]["table_size"] if size_result else "Unknown"
            }
        except Exception as e:
            return {"error": str(e), "table_name": table_name}


class NeonAgent:
    """
    AI Agent connected to Neon PostgreSQL database.
    Combines Claude's intelligence with your database.
    """

    def __init__(
        self,
        model: str = "claude-3-haiku-20240307",
        connection_string: Optional[str] = None
    ):
        """
        Initialize the Neon Agent.

        Args:
            model: Claude model to use
            connection_string: PostgreSQL connection string (from env if not provided)
        """
        # Load API key
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable not set")

        self.client = Anthropic(api_key=api_key)
        self.model = model
        self.conversation_history: List[Dict[str, Any]] = []
        self.max_tokens = 4096

        # Load database configuration
        self.connection_string = connection_string or os.environ.get("NEON_DATABASE_URL")

        if not self.connection_string:
            raise ValueError("NEON_DATABASE_URL not provided and not in environment")

        # Initialize PostgreSQL client
        self.db = PostgresClient(self.connection_string)

        # Test connection
        try:
            self.db.connect()
            print(f"✅ Neon Agent initialized")
            print(f"   Model: {model}")
            print(f"   Database: Connected to Neon PostgreSQL")
        except Exception as e:
            raise ValueError(f"Failed to connect to database: {e}")

    def define_tools(self) -> List[Dict[str, Any]]:
        """
        Define PostgreSQL database tools for the agent.
        These tools allow Claude to interact with your database.
        """
        return [
            # Schema Discovery Tools
            {
                "name": "list_tables",
                "description": "List all tables in the database. Shows table names and types.",
                "input_schema": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            },
            {
                "name": "describe_table",
                "description": "Get detailed schema information for a specific table including columns, data types, and constraints.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "table_name": {
                            "type": "string",
                            "description": "The name of the table to describe"
                        }
                    },
                    "required": ["table_name"]
                }
            },
            {
                "name": "get_table_stats",
                "description": "Get statistics for a table including row count and size.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "table_name": {
                            "type": "string",
                            "description": "The name of the table"
                        }
                    },
                    "required": ["table_name"]
                }
            },
            # Query Execution Tools
            {
                "name": "execute_select",
                "description": "Execute a SELECT query to retrieve data from the database. Use this for reading data.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "The SQL SELECT query to execute"
                        }
                    },
                    "required": ["query"]
                }
            },
            {
                "name": "execute_insert",
                "description": "Execute an INSERT query to add new data to the database.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "The SQL INSERT query to execute"
                        }
                    },
                    "required": ["query"]
                }
            },
            {
                "name": "execute_update",
                "description": "Execute an UPDATE query to modify existing data in the database.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "The SQL UPDATE query to execute"
                        }
                    },
                    "required": ["query"]
                }
            },
            {
                "name": "execute_delete",
                "description": "Execute a DELETE query to remove data from the database. Use with caution.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "The SQL DELETE query to execute"
                        }
                    },
                    "required": ["query"]
                }
            },
            # Analysis Tools
            {
                "name": "count_rows",
                "description": "Count the number of rows in a table, optionally with a WHERE condition.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "table_name": {
                            "type": "string",
                            "description": "The name of the table"
                        },
                        "where_clause": {
                            "type": "string",
                            "description": "Optional WHERE clause (without the WHERE keyword)"
                        }
                    },
                    "required": ["table_name"]
                }
            }
        ]

    def execute_tool(self, tool_name: str, tool_input: Dict[str, Any]) -> str:
        """
        Execute a database tool.

        Args:
            tool_name: The tool to execute
            tool_input: Tool arguments

        Returns:
            JSON-serialized result
        """
        try:
            # Schema discovery tools
            if tool_name == "list_tables":
                result = self.db.list_tables()

            elif tool_name == "describe_table":
                table_name = tool_input.get("table_name")
                result = self.db.describe_table(table_name)

            elif tool_name == "get_table_stats":
                table_name = tool_input.get("table_name")
                result = self.db.get_table_stats(table_name)

            # Query execution tools
            elif tool_name == "execute_select":
                query = tool_input.get("query")
                result = self.db.execute_query(query)

            elif tool_name in ["execute_insert", "execute_update", "execute_delete"]:
                query = tool_input.get("query")
                result = self.db.execute_mutation(query)

            # Analysis tools
            elif tool_name == "count_rows":
                table_name = tool_input.get("table_name")
                where_clause = tool_input.get("where_clause", "")
                query = f"SELECT COUNT(*) as count FROM {table_name}"
                if where_clause:
                    query += f" WHERE {where_clause}"
                result = self.db.execute_query(query)

            else:
                return json.dumps({"error": f"Unknown tool: {tool_name}"})

            return json.dumps(result, indent=2, default=str)

        except Exception as e:
            return json.dumps({
                "error": str(e),
                "tool": tool_name
            })

    def chat(self, user_message: str) -> str:
        """
        Send a message to the agent and get a response.
        The agent can query and modify your database as needed.

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
                    print(f"   Input: {json.dumps(tool_use.input, indent=2)}")

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

    def __del__(self):
        """Cleanup: close database connection."""
        if hasattr(self, 'db'):
            self.db.close()


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
    """Demo of Neon Agent capabilities."""
    print("\n" + "="*60)
    print("Neon Database Agent - Demo")
    print("="*60 + "\n")

    # Load environment
    load_env()

    # Initialize agent
    agent = NeonAgent()

    print("\n" + "="*60)
    print("Example 1: Explore Database Schema")
    print("="*60 + "\n")

    response = agent.chat("What tables do we have in the database?")
    print(f"Agent: {response}\n")

    print("\n" + "="*60)
    print("Example 2: Analyze Data")
    print("="*60 + "\n")

    response = agent.chat("Can you analyze the data in our database and give me some insights?")
    print(f"Agent: {response}\n")

    print("\n" + "="*60)
    print("✅ Demo completed!")
    print("="*60)


if __name__ == "__main__":
    main()
