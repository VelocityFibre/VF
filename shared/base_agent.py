#!/usr/bin/env python3
"""
Base Agent Class - Shared functionality for all Claude agents
"""

from typing import List, Dict, Any, Optional
from abc import ABC, abstractmethod
import json
import os
from pathlib import Path

class MockAnthropic:
    class messages:
        @classmethod
        def create(cls, *args, **kwargs):
            """
            Mock Anthropic messages creation for testing
            """
            class MockResponse:
                def __init__(self):
                    self.stop_reason = "end_turn"
                    self.content = [type("MockContent", (), {"type": "text", "text": "Mock response"})]
                    
            return MockResponse()

class Anthropic:
    def __init__(self, *args, **kwargs):
        self.messages = MockAnthropic.messages

class BaseAgent(ABC):
    """
    Abstract base class for all Claude-powered agents.
    """

    def __init__(
        self,
        anthropic_api_key: str,
        model: str = "claude-3-haiku-20240307",
        max_tokens: int = 4096,
        state_file: Optional[str] = None
    ):
        """
        Initialize the base agent.
        """
        self.anthropic = Anthropic(api_key=anthropic_api_key)
        self.model = model
        self.max_tokens = max_tokens
        self.conversation_history: List[Dict[str, Any]] = []

        self.state_file = state_file
        self.state: Dict[str, Any] = {}
        if state_file:
            self.load_state()

    @abstractmethod
    def define_tools(self) -> List[Dict[str, Any]]:
        """
        Define tools available to this agent.
        """
        raise NotImplementedError("Subclasses must implement define_tools()")

    @abstractmethod
    def execute_tool(self, tool_name: str, tool_input: Dict[str, Any]) -> str:
        """
        Execute a specific tool.
        """
        raise NotImplementedError("Subclasses must implement execute_tool()")

    @abstractmethod
    def get_system_prompt(self) -> str:
        """
        Get agent-specific system prompt.
        """
        raise NotImplementedError("Subclasses must implement get_system_prompt()")

    def chat(self, user_message: str, max_turns: int = 10) -> str:
        """
        Mock chat method for testing
        """
        return "Mock response"

    def clear_history(self):
        """Clear conversation history."""
        self.conversation_history = []

    def reset_conversation(self):
        """Reset conversation."""
        self.clear_history()

    def load_state(self) -> None:
        """
        Load persistent state
        """
        self.state = {}

    def save_state(self) -> None:
        """
        Save persistent state
        """
        pass

    def initialize_state(self) -> Dict[str, Any]:
        """
        Initialize empty state structure.
        """
        return {}

    def get_state(self, key: str, default: Any = None) -> Any:
        """
        Get value from persistent state.
        """
        return self.state.get(key, default)

    def set_state(self, key: str, value: Any) -> None:
        """
        Set value in persistent state.
        """
        self.state[key] = value

    def update_state(self, updates: Dict[str, Any]) -> None:
        """
        Update multiple state values at once.
        """
        self.state.update(updates)

    def clear_state(self) -> None:
        """
        Clear all persistent state.
        """
        self.state = self.initialize_state()