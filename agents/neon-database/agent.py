#!/usr/bin/env python3
"""
Neon Database Agent - Claude Agent SDK Integration
Connects Claude AI with your Neon PostgreSQL database for intelligent data operations.
"""

import os
import json
import sys
import psycopg2
from pathlib import Path
from psycopg2 import pool
from psycopg2.extras import RealDictCursor
from typing import List, Dict, Any, Optional

# Add project root to path for shared imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from shared.base_agent import BaseAgent


class PostgresClient:
    """
    Client for interacting with PostgreSQL/Neon database.
    Handles all database connections and queries with connection pooling.

    Connection pooling improves performance by reusing database connections
    instead of creating new ones for each query.
    """

    def __init__(self, connection_string: str, minconn: int = 1, maxconn: int = 10):
        """
        Initialize PostgreSQL client with connection pooling.

        Args:
            connection_string: PostgreSQL connection string
            minconn: Minimum number of connections in pool (default: 1)
            maxconn: Maximum number of connections in pool (default: 10)
        """
        self.connection_string = connection_string
        self.pool = pool.SimpleConnectionPool(
            minconn=minconn,
            maxconn=maxconn,
            dsn=connection_string,
            cursor_factory=RealDictCursor
        )

    def get_connection(self):
        """Get a connection from the pool."""
        return self.pool.getconn()

    def return_connection(self, conn):
        """Return a connection to the pool."""
        self.pool.putconn(conn)

    def connect(self):
        """Get a connection from pool (for backward compatibility)."""
        return self.get_connection()

    def close(self):
        """Close all connections in the pool."""
        if self.pool:
            self.pool.closeall()

    def execute_query(self, query: str, params: tuple = None) -> List[Dict[str, Any]]:
        """
        Execute a SELECT query and return results using connection from pool.

        Args:
            query: SQL query string
            params: Query parameters (for parameterized queries)

        Returns:
            List of result rows as dictionaries
        """
        conn = None
        try:
            conn = self.get_connection()
            with conn.cursor() as cursor:
                cursor.execute(query, params)
                results = cursor.fetchall()
                return [dict(row) for row in results]
        except Exception as e:
            return {"error": str(e), "query": query}
        finally:
            if conn:
                self.return_connection(conn)

    def execute_mutation(self, query: str, params: tuple = None) -> Dict[str, Any]:
        """
        Execute an INSERT, UPDATE, or DELETE query using connection from pool.

        Args:
            query: SQL query string
            params: Query parameters

        Returns:
            Result dictionary with rowcount and status
        """
        conn = None
        try:
            conn = self.get_connection()
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
        finally:
            if conn:
                self.return_connection(conn)

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


class NeonAgent(BaseAgent):
    """
    AI Agent connected to Neon PostgreSQL database.
    Combines Claude's intelligence with your database.
    Inherits common agent functionality from BaseAgent.
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

        # Initialize base agent
        super().__init__(
            anthropic_api_key=api_key,
            model=model,
            max_tokens=4096
        )

        # Load database configuration
        self.connection_string = connection_string or os.environ.get("NEON_DATABASE_URL")

        if not self.connection_string:
            raise ValueError("NEON_DATABASE_URL not provided and not in environment")

        # Initialize PostgreSQL client with connection pool
        self.db = PostgresClient(self.connection_string, minconn=1, maxconn=10)

        # Test connection pool
        conn = None
        try:
            conn = self.db.get_connection()
        except Exception as e:
            raise ValueError(f"Failed to initialize database connection pool: {e}")
        finally:
            if conn:
                self.db.return_connection(conn)

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

    def get_system_prompt(self) -> str:
        """
        Get Neon database agent system prompt.

        Returns:
            System prompt for database operations
        """
        return """You are a helpful database assistant with access to a PostgreSQL/Neon database.

You can:
- Explore the database schema (list tables, describe tables, get statistics)
- Execute SELECT queries to retrieve data
- Execute INSERT, UPDATE, DELETE queries to modify data
- Count rows and analyze data

Always:
- Write safe, parameterized SQL queries
- Explain what you're doing before executing queries
- Format results in a clear, readable way
- Be cautious with DELETE and UPDATE operations
- Suggest optimizations when appropriate

When the user asks about data, explore the schema first if needed to understand the available tables and columns."""

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
