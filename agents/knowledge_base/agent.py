"""
Knowledge Base Agent

Centralized documentation management for Velocity Fibre operations
"""

from typing import List, Dict, Any
from shared.base_agent import BaseAgent
from agents.knowledge_base.tools.server_docs import ServerDocumentationTool
import json
import os


class KnowledgeBaseAgent(BaseAgent):
    """
    Knowledge Base Agent for centralized documentation management
    """

    def __init__(
        self, 
        anthropic_api_key: str, 
        model: str = "claude-3-haiku-20240307",
        server_doc_tool: ServerDocumentationTool = None
    ):
        """
        Initialize Knowledge Base Agent

        Args:
            anthropic_api_key (str): Claude API key
            model (str, optional): Claude model. Defaults to haiku.
            server_doc_tool (ServerDocumentationTool, optional): Server documentation tool
        """
        super().__init__(anthropic_api_key, model)
        
        # Initialize tools
        self.server_doc_tool = server_doc_tool or ServerDocumentationTool()

    def define_tools(self) -> List[Dict[str, Any]]:
        """
        Define available tools for the Knowledge Base Agent

        Returns:
            List of tool definitions
        """
        return [
            {
                "name": "extract_server_docs",
                "description": "Extract comprehensive server documentation",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "server_name": {
                            "type": "string",
                            "description": "Name of the server (hostinger_vps, vf_server)",
                            "enum": ["hostinger_vps", "vf_server"]
                        },
                        "format": {
                            "type": "string",
                            "description": "Documentation output format",
                            "enum": ["markdown", "json"],
                            "default": "markdown"
                        }
                    },
                    "required": ["server_name"]
                }
            }
        ]

    def execute_tool(self, tool_name: str, tool_input: Dict[str, Any]) -> str:
        """
        Execute a specific tool

        Args:
            tool_name (str): Name of the tool to execute
            tool_input (Dict[str, Any]): Tool parameters

        Returns:
            JSON-serialized result string
        """
        if tool_name == "extract_server_docs":
            server_name = tool_input.get("server_name")
            format_type = tool_input.get("format", "markdown")

            doc = self.server_doc_tool.document_server(server_name)
            
            return doc.get(format_type, doc['markdown'])

        return json.dumps({"error": f"Unknown tool: {tool_name}"})

    def get_system_prompt(self) -> str:
        """
        System prompt for the Knowledge Base Agent

        Returns:
            Comprehensive system description
        """
        return """You are a FibreFlow Knowledge Base Agent.

Your role is to centralize and manage documentation for Velocity Fibre operations.

Key Capabilities:
- Generate server documentation
- Extract configuration details
- Support multiple server types
- Create web-friendly Markdown docs

Available Tools:
- extract_server_docs: Generate comprehensive server documentation

When asked about server configuration, use extract_server_docs tool.
Focus on clarity, conciseness, and practical information.
"""