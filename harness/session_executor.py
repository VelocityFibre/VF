#!/usr/bin/env python3
"""
Session Executor - Production SDK Integration with Tool Calling

Executes Claude Code sessions using Anthropic Python SDK for autonomous agent development.
Implements full conversation loop with tool calling support.
"""

import os
import subprocess
import json
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime
from anthropic import Anthropic


class SessionExecutor:
    """
    Executes autonomous coding sessions using Anthropic SDK.

    Integrates with:
    - Phase 1: Git worktrees (sessions run in isolated worktrees)
    - Phase 2: Self-healing (prompts include validation loops)
    - Phase 3: Parallel execution (multiple sessions run concurrently)
    """

    def __init__(self, model: str = "claude-3-5-haiku-20241022", timeout_minutes: int = 30):
        """
        Initialize session executor.

        Args:
            model: Claude model to use (haiku/sonnet/opus)
            timeout_minutes: Maximum session duration
        """
        self.model = model
        self.timeout_minutes = timeout_minutes
        self.timeout_seconds = timeout_minutes * 60

        # Initialize Anthropic client
        api_key = os.environ.get('ANTHROPIC_API_KEY') or os.environ.get('CLAUDE_TOKEN')
        if not api_key:
            raise RuntimeError("No Claude credentials found (ANTHROPIC_API_KEY or CLAUDE_TOKEN)")

        self.client = Anthropic(api_key=api_key)

        # Tool definitions (Claude Code tools)
        self.tools = [
            {
                "name": "Bash",
                "description": "Execute bash commands in the working directory",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "command": {
                            "type": "string",
                            "description": "The bash command to execute"
                        }
                    },
                    "required": ["command"]
                }
            },
            {
                "name": "Read",
                "description": "Read contents of a file",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "file_path": {
                            "type": "string",
                            "description": "Path to the file to read"
                        }
                    },
                    "required": ["file_path"]
                }
            },
            {
                "name": "Write",
                "description": "Write contents to a file (creates or overwrites)",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "file_path": {
                            "type": "string",
                            "description": "Path to the file to write"
                        },
                        "content": {
                            "type": "string",
                            "description": "Content to write to the file"
                        }
                    },
                    "required": ["file_path", "content"]
                }
            },
            {
                "name": "Edit",
                "description": "Edit a file by replacing old_string with new_string",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "file_path": {
                            "type": "string",
                            "description": "Path to the file to edit"
                        },
                        "old_string": {
                            "type": "string",
                            "description": "The exact string to replace"
                        },
                        "new_string": {
                            "type": "string",
                            "description": "The new string to insert"
                        }
                    },
                    "required": ["file_path", "old_string", "new_string"]
                }
            }
        ]

    def execute_session(
        self,
        prompt: str,
        context: Dict[str, Any],
        session_log: Path,
        working_dir: Optional[Path] = None
    ) -> bool:
        """
        Execute a single Claude Code session with full tool calling support.

        Args:
            prompt: The prompt to send to Claude (from initializer.md or coding_agent.md)
            context: Context dictionary with agent_name, run_dir, etc.
            session_log: Path to write session output
            working_dir: Working directory for the session (for worktree isolation)

        Returns:
            bool: True if session succeeded, False otherwise
        """
        # Prepare prompt with context substitution
        formatted_prompt = self._format_prompt(prompt, context)

        # Set working directory
        if working_dir:
            original_cwd = Path.cwd()
            os.chdir(working_dir)
        else:
            original_cwd = None

        try:
            start_time = datetime.now()

            # Initialize session log
            with open(session_log, 'w') as log_file:
                log_file.write(f"=== Claude Code Session Started ===\n")
                log_file.write(f"Time: {start_time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                log_file.write(f"Model: {self.model}\n")
                log_file.write(f"Working Dir: {working_dir or Path.cwd()}\n")
                log_file.write(f"Prompt length: {len(formatted_prompt)} characters\n")
                log_file.write(f"\n{'=' * 70}\n\n")

            # Execute conversation loop with tool calling
            success = self._conversation_loop(
                formatted_prompt,
                session_log,
                working_dir or Path.cwd()
            )

            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()

            # Append summary to log
            with open(session_log, 'a') as log_file:
                log_file.write(f"\n\n{'=' * 70}\n")
                log_file.write(f"=== Session Complete ===\n")
                log_file.write(f"Duration: {duration:.1f} seconds\n")
                log_file.write(f"Status: {'SUCCESS' if success else 'FAILED'}\n")

            return success

        except Exception as e:
            with open(session_log, 'a') as log_file:
                log_file.write(f"\n\n{'=' * 70}\n")
                log_file.write(f"=== Session ERROR ===\n")
                log_file.write(f"Error: {e}\n")
            return False

        finally:
            # Restore original directory
            if original_cwd:
                os.chdir(original_cwd)

    def _conversation_loop(
        self,
        initial_prompt: str,
        session_log: Path,
        working_dir: Path
    ) -> bool:
        """
        Execute the conversation loop with tool calling.

        Args:
            initial_prompt: The formatted prompt
            session_log: Path to session log
            working_dir: Working directory for tool execution

        Returns:
            bool: True if conversation completed successfully
        """
        messages = [{"role": "user", "content": initial_prompt}]
        turn_count = 0
        max_turns = 100  # Prevent infinite loops

        with open(session_log, 'a') as log_file:
            log_file.write(f"[TURN {turn_count}] User prompt sent\n\n")

            while turn_count < max_turns:
                turn_count += 1

                try:
                    # Call Claude API
                    response = self.client.messages.create(
                        model=self.model,
                        max_tokens=4096,
                        tools=self.tools,
                        messages=messages
                    )

                    log_file.write(f"[TURN {turn_count}] Claude response\n")
                    log_file.write(f"Stop reason: {response.stop_reason}\n")
                    log_file.flush()

                    # Handle response based on stop reason
                    if response.stop_reason == "end_turn":
                        # Task complete
                        for block in response.content:
                            if hasattr(block, 'text'):
                                log_file.write(f"\n{block.text}\n")
                        log_file.write(f"\n[TURN {turn_count}] Conversation complete\n")
                        return True

                    elif response.stop_reason == "tool_use":
                        # Process tool calls
                        assistant_message = {"role": "assistant", "content": response.content}
                        messages.append(assistant_message)

                        # Log assistant message
                        for block in response.content:
                            if hasattr(block, 'text') and block.text:
                                log_file.write(f"\nClaude: {block.text}\n")
                            elif block.type == "tool_use":
                                log_file.write(f"\n[TOOL] {block.name}({json.dumps(block.input, indent=2)})\n")

                        # Execute tools and collect results
                        tool_results = []
                        for block in response.content:
                            if block.type == "tool_use":
                                tool_result = self._execute_tool(
                                    block.name,
                                    block.input,
                                    block.id,
                                    working_dir,
                                    log_file
                                )
                                tool_results.append(tool_result)

                        # Add tool results to conversation
                        messages.append({"role": "user", "content": tool_results})

                        log_file.flush()

                    elif response.stop_reason == "max_tokens":
                        log_file.write(f"\n[WARNING] Hit max tokens limit\n")
                        # Continue with truncated response
                        messages.append({"role": "assistant", "content": response.content})

                    else:
                        log_file.write(f"\n[ERROR] Unexpected stop reason: {response.stop_reason}\n")
                        return False

                except Exception as e:
                    log_file.write(f"\n[ERROR] API call failed: {e}\n")
                    return False

            log_file.write(f"\n[ERROR] Reached max turns ({max_turns})\n")
            return False

    def _execute_tool(
        self,
        tool_name: str,
        tool_input: Dict[str, Any],
        tool_use_id: str,
        working_dir: Path,
        log_file
    ) -> Dict[str, Any]:
        """
        Execute a tool and return the result.

        Args:
            tool_name: Name of the tool to execute
            tool_input: Tool parameters
            tool_use_id: Tool use ID for correlation
            working_dir: Working directory
            log_file: Log file handle

        Returns:
            Tool result in Claude format
        """
        try:
            if tool_name == "Bash":
                result = self._execute_bash(tool_input["command"], working_dir)
            elif tool_name == "Read":
                result = self._execute_read(tool_input["file_path"], working_dir)
            elif tool_name == "Write":
                result = self._execute_write(
                    tool_input["file_path"],
                    tool_input["content"],
                    working_dir
                )
            elif tool_name == "Edit":
                result = self._execute_edit(
                    tool_input["file_path"],
                    tool_input["old_string"],
                    tool_input["new_string"],
                    working_dir
                )
            else:
                result = f"Error: Unknown tool '{tool_name}'"

            log_file.write(f"[RESULT] {result[:500]}{'...' if len(str(result)) > 500 else ''}\n\n")

            return {
                "type": "tool_result",
                "tool_use_id": tool_use_id,
                "content": str(result)
            }

        except Exception as e:
            error_msg = f"Error executing {tool_name}: {e}"
            log_file.write(f"[ERROR] {error_msg}\n\n")
            return {
                "type": "tool_result",
                "tool_use_id": tool_use_id,
                "content": error_msg,
                "is_error": True
            }

    def _execute_bash(self, command: str, working_dir: Path) -> str:
        """Execute bash command."""
        result = subprocess.run(
            command,
            shell=True,
            cwd=working_dir,
            capture_output=True,
            text=True,
            timeout=60
        )
        output = result.stdout + result.stderr
        return output if output else f"Command completed with exit code {result.returncode}"

    def _execute_read(self, file_path: str, working_dir: Path) -> str:
        """Read file contents."""
        full_path = working_dir / file_path
        with open(full_path, 'r') as f:
            return f.read()

    def _execute_write(self, file_path: str, content: str, working_dir: Path) -> str:
        """Write file contents."""
        full_path = working_dir / file_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        with open(full_path, 'w') as f:
            f.write(content)
        return f"Successfully wrote {len(content)} characters to {file_path}"

    def _execute_edit(self, file_path: str, old_string: str, new_string: str, working_dir: Path) -> str:
        """Edit file by replacing old_string with new_string."""
        full_path = working_dir / file_path
        content = full_path.read_text()

        if old_string not in content:
            return f"Error: old_string not found in {file_path}"

        new_content = content.replace(old_string, new_string, 1)
        full_path.write_text(new_content)
        return f"Successfully edited {file_path}"

    def _format_prompt(self, prompt: str, context: Dict[str, Any]) -> str:
        """
        Format prompt with context variable substitution.

        Args:
            prompt: Raw prompt template
            context: Dictionary of context variables

        Returns:
            Formatted prompt with variables substituted
        """
        formatted = prompt

        # Replace common context variables
        replacements = {
            "{agent_name}": context.get("agent_name", "unknown"),
            "{run_dir}": str(context.get("run_dir", ".")),
            "{session_number}": str(context.get("session_number", 0)),
            "{spec_file}": str(context.get("spec_file", "")),
            "{feature_list}": str(context.get("feature_list", "")),
            "{progress_file}": str(context.get("progress_file", "")),
        }

        for placeholder, value in replacements.items():
            formatted = formatted.replace(placeholder, value)

        return formatted


def create_executor(model: str = "claude-3-5-haiku-20241022", timeout_minutes: int = 30) -> SessionExecutor:
    """
    Factory function to create a SessionExecutor.

    Args:
        model: Claude model to use
        timeout_minutes: Session timeout

    Returns:
        SessionExecutor instance
    """
    return SessionExecutor(model=model, timeout_minutes=timeout_minutes)
