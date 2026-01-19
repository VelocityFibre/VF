import os
import json
from typing import List, Dict, Any

class BaseAgent:
    """Base class for all FibreFlow agents"""

    def __init__(self, anthropic_api_key: str, model: str = "claude-3-haiku-20240307"):
        """
        Initialize BaseAgent with API credentials and model selection

        :param anthropic_api_key: API key for Anthropic Claude
        :param model: Claude model to use, defaults to haiku
        """
        self.anthropic_api_key = anthropic_api_key
        self.model = model
        self._tools = []  # Initialize empty tools list

    def define_tools(self) -> List[Dict[str, Any]]:
        """
        Define available tools for the agent.
        Subclasses should override this method.

        :return: List of tool definitions
        """
        return self._tools

    def execute_tool(self, tool_name: str, tool_input: Dict[str, Any]) -> str:
        """
        Execute a specific tool with given input.
        Subclasses should implement specific tool logic.

        :param tool_name: Name of the tool to execute
        :param tool_input: Input parameters for the tool
        :return: JSON string with execution result
        """
        return json.dumps({"error": f"Tool {tool_name} not implemented"})

    def get_system_prompt(self) -> str:
        """
        Generate system prompt for the agent.
        Subclasses should provide specific prompts.

        :return: System prompt string
        """
        return "You are a FibreFlow agent, ready to assist with tasks."

    def chat(self, message: str) -> str:
        """
        Basic chat method to be overridden by subclasses.
        
        :param message: User message
        :return: Agent response
        """
        return f"Received message: {message}"