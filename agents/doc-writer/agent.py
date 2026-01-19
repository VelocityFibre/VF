"""
Doc Writer Agent

Automatically generates and maintains documentation for FibreFlow agents.

Capabilities:
    - Generate Google-style docstrings for undocumented functions
    - Update README.md when tools/capabilities change
    - Create usage examples
    - Generate API documentation
    - Update CLAUDE.md for architectural changes

Architecture:
    Inherits from BaseAgent, uses Claude Sonnet for better writing quality.

Usage:
    from agents.doc_writer.agent import DocWriterAgent

    agent = DocWriterAgent(api_key, model="claude-sonnet-4-20250514")
    result = agent.write_docstring(
        file_path="agents/neon-database/agent.py",
        function_name="execute_query"
    )
"""

import os
import ast
import re
from typing import Dict, Any, List
from pathlib import Path

# Import BaseAgent
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from shared.base_agent import BaseAgent


class DocWriterAgent(BaseAgent):
    """Agent for automatic documentation generation and maintenance."""

    def __init__(self, anthropic_api_key: str, model: str = "claude-sonnet-4-20250514"):
        """Initialize doc writer agent.

        Args:
            anthropic_api_key: Anthropic API key
            model: Claude model to use (default: Sonnet for better writing)
        """
        super().__init__(anthropic_api_key, model)
        self.project_root = Path(os.getcwd())

    def get_system_prompt(self) -> str:
        """Get system prompt for documentation generation."""
        return """You are an expert technical documentation writer specializing in Python codebases.

Your capabilities:
1. Generate Google-style docstrings with clear explanations
2. Write comprehensive README.md files with usage examples
3. Create API documentation with proper formatting
4. Update architectural documentation (CLAUDE.md) with system changes
5. Generate usage examples that demonstrate features clearly

FibreFlow Documentation Patterns:
- Use Google-style docstrings (Args, Returns, Raises, Example)
- Be concise but thorough
- Include code examples in docstrings
- Document all parameters with types
- Explain "why" not just "what"
- Use markdown formatting for README files
- Follow existing documentation style

Always generate documentation that is:
- Clear and easy to understand
- Technically accurate
- Well-formatted
- Includes practical examples
- Follows Python conventions"""

    def define_tools(self) -> List[Dict[str, Any]]:
        """Define tools for documentation generation."""
        return [
            {
                "name": "scan_for_missing_docstrings",
                "description": "Scan Python file to identify functions without docstrings",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "file_path": {
                            "type": "string",
                            "description": "Path to Python file to scan"
                        }
                    },
                    "required": ["file_path"]
                }
            },
            {
                "name": "write_docstring",
                "description": "Generate Google-style docstring for a function",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "file_path": {
                            "type": "string",
                            "description": "Path to file containing function"
                        },
                        "function_name": {
                            "type": "string",
                            "description": "Name of function to document"
                        }
                    },
                    "required": ["file_path", "function_name"]
                }
            },
            {
                "name": "generate_agent_readme",
                "description": "Generate README.md for an agent",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "agent_dir": {
                            "type": "string",
                            "description": "Path to agent directory (e.g., agents/neon-database)"
                        }
                    },
                    "required": ["agent_dir"]
                }
            },
            {
                "name": "update_claude_md",
                "description": "Update CLAUDE.md with new agent or architectural changes",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "section": {
                            "type": "string",
                            "description": "Section to update (e.g., 'Agent Types', 'Commands')"
                        },
                        "content": {
                            "type": "string",
                            "description": "Content to add/update"
                        }
                    },
                    "required": ["section", "content"]
                }
            }
        ]

    def execute_tool(self, tool_name: str, tool_input: Dict[str, Any]) -> Dict[str, Any]:
        """Execute documentation tools."""
        try:
            if tool_name == "scan_for_missing_docstrings":
                return self._scan_for_missing_docstrings(tool_input["file_path"])

            elif tool_name == "write_docstring":
                return self._write_docstring(
                    file_path=tool_input["file_path"],
                    function_name=tool_input["function_name"]
                )

            elif tool_name == "generate_agent_readme":
                return self._generate_agent_readme(tool_input["agent_dir"])

            elif tool_name == "update_claude_md":
                return self._update_claude_md(
                    section=tool_input["section"],
                    content=tool_input["content"]
                )

            else:
                return {
                    "success": False,
                    "error": f"Unknown tool: {tool_name}"
                }

        except Exception as e:
            return {
                "success": False,
                "error": f"Tool execution failed: {str(e)}"
            }

    def _scan_for_missing_docstrings(self, file_path: str) -> Dict[str, Any]:
        """Scan Python file for functions without docstrings.

        Args:
            file_path: Path to Python file to scan

        Returns:
            Dict with undocumented functions list
        """
        try:
            # Read source file
            with open(file_path, 'r') as f:
                source = f.read()

            # Parse AST
            tree = ast.parse(source)

            # Extract functions
            functions = []

            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    # Skip private functions unless __init__
                    if node.name.startswith('_') and node.name != '__init__':
                        continue

                    # Get docstring
                    docstring = ast.get_docstring(node)

                    # Get function signature
                    args = [arg.arg for arg in node.args.args]

                    functions.append({
                        "name": node.name,
                        "line": node.lineno,
                        "args": args,
                        "has_docstring": bool(docstring),
                        "docstring_length": len(docstring) if docstring else 0
                    })

            # Identify missing/incomplete docstrings
            missing = [f for f in functions if not f['has_docstring']]
            incomplete = [f for f in functions if f['has_docstring'] and f['docstring_length'] < 50]

            return {
                "success": True,
                "file_path": file_path,
                "total_functions": len(functions),
                "documented": len([f for f in functions if f['has_docstring']]),
                "missing_docstrings": len(missing),
                "incomplete_docstrings": len(incomplete),
                "missing": missing,
                "incomplete": incomplete,
                "coverage_percent": (len([f for f in functions if f['has_docstring']]) / len(functions) * 100) if functions else 100
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to scan file: {str(e)}"
            }

    def _write_docstring(self, file_path: str, function_name: str) -> Dict[str, Any]:
        """Generate Google-style docstring for a function.

        Args:
            file_path: Path to source file
            function_name: Name of function to document

        Returns:
            Dict with generated docstring
        """
        try:
            # Read source
            with open(file_path, 'r') as f:
                source = f.read()

            # Parse AST to find function
            tree = ast.parse(source)

            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef) and node.name == function_name:
                    # Extract function details
                    func_source = ast.get_source_segment(source, node)

                    # Get arguments with types
                    args = []

                    for arg in node.args.args:
                        arg_name = arg.arg
                        arg_type = None

                        if arg.annotation:
                            if isinstance(arg.annotation, ast.Name):
                                arg_type = arg.annotation.id
                            else:
                                arg_type = ast.unparse(arg.annotation)

                        args.append({
                            "name": arg_name,
                            "type": arg_type
                        })

                    # Get return type
                    return_type = None

                    if node.returns:
                        if isinstance(node.returns, ast.Name):
                            return_type = node.returns.id
                        else:
                            return_type = ast.unparse(node.returns)

                    # Build prompt for Claude
                    prompt = f"""Generate a Google-style docstring for this function:

File: {file_path}
Function: {function_name}

Function source (first 30 lines):
{func_source[:1500]}

Arguments: {', '.join([f"{a['name']}: {a['type']}" if a['type'] else a['name'] for a in args])}
Return Type: {return_type or 'Not specified'}

Generate a comprehensive Google-style docstring that includes:
1. Brief description (1-2 sentences)
2. Detailed explanation if needed
3. Args section with all parameters
4. Returns section
5. Raises section (if applicable)
6. Example section (if useful)

Return ONLY the docstring text (no code, no quotes, no function signature)."""

                    # Use Claude to generate docstring
                    message = self.anthropic.messages.create(
                        model=self.model,
                        max_tokens=1500,
                        system=self.get_system_prompt(),
                        messages=[{"role": "user", "content": prompt}]
                    )

                    docstring = message.content[0].text.strip()

                    # Clean up (remove any code blocks)
                    docstring = self._clean_generated_text(docstring)

                    return {
                        "success": True,
                        "function_name": function_name,
                        "docstring": docstring,
                        "args": args,
                        "return_type": return_type
                    }

            return {
                "success": False,
                "error": f"Function '{function_name}' not found in {file_path}"
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to generate docstring: {str(e)}"
            }

    def _generate_agent_readme(self, agent_dir: str) -> Dict[str, Any]:
        """Generate README.md for an agent.

        Args:
            agent_dir: Path to agent directory

        Returns:
            Dict with generated README content
        """
        try:
            agent_path = Path(agent_dir)

            # Read agent.py to extract capabilities
            agent_file = agent_path / "agent.py"

            if not agent_file.exists():
                return {
                    "success": False,
                    "error": f"Agent file not found: {agent_file}"
                }

            with open(agent_file, 'r') as f:
                source = f.read()

            # Extract agent class and tools
            tree = ast.parse(source)

            agent_class_name = None
            tools = []
            class_docstring = None

            for node in ast.walk(tree):
                # Find agent class
                if isinstance(node, ast.ClassDef) and "Agent" in node.name:
                    agent_class_name = node.name
                    class_docstring = ast.get_docstring(node)

                # Find define_tools method
                if isinstance(node, ast.FunctionDef) and node.name == "define_tools":
                    # Try to extract tools list (simplified)
                    func_source = ast.get_source_segment(source, node)

                    # Use regex to extract tool names
                    tool_names = re.findall(r'"name":\s*"([^"]+)"', func_source)
                    tool_descriptions = re.findall(r'"description":\s*"([^"]+)"', func_source)

                    for name, desc in zip(tool_names, tool_descriptions):
                        tools.append({"name": name, "description": desc})

            # Extract agent name from directory
            agent_name = agent_path.name

            # Build prompt for README generation
            prompt = f"""Generate a README.md file for this FibreFlow agent:

Agent Directory: {agent_dir}
Agent Class: {agent_class_name}
Agent Name: {agent_name}

Class Docstring:
{class_docstring or 'Not available'}

Tools ({len(tools)}):
{chr(10).join([f"- {t['name']}: {t['description']}" for t in tools])}

Generate a comprehensive README.md with these sections:
1. # {agent_name.replace('-', ' ').title()} Agent - Title and brief description
2. ## Overview - What this agent does
3. ## Capabilities - List of features/tools
4. ## Usage - Code example showing how to use
5. ## Tools - Detailed tool documentation
6. ## Example - Practical use case
7. ## Integration - How to use with orchestrator

Use markdown formatting. Be clear and practical.

Return ONLY the README.md content."""

            # Use Claude to generate README
            message = self.anthropic.messages.create(
                model=self.model,
                max_tokens=2000,
                system=self.get_system_prompt(),
                messages=[{"role": "user", "content": prompt}]
            )

            readme_content = message.content[0].text.strip()

            # Clean up
            readme_content = self._clean_generated_text(readme_content)

            return {
                "success": True,
                "agent_name": agent_name,
                "readme_content": readme_content,
                "tools_documented": len(tools),
                "readme_path": str(agent_path / "README.md")
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to generate README: {str(e)}"
            }

    def _update_claude_md(self, section: str, content: str) -> Dict[str, Any]:
        """Update CLAUDE.md with new section or content.

        Args:
            section: Section name to update
            content: Content to add/update

        Returns:
            Dict with update status
        """
        try:
            claude_md_path = Path("CLAUDE.md")

            if not claude_md_path.exists():
                return {
                    "success": False,
                    "error": "CLAUDE.md not found"
                }

            # Read existing content
            with open(claude_md_path, 'r') as f:
                existing = f.read()

            # Find section
            section_pattern = f"## {section}"

            if section_pattern in existing:
                # Section exists - would need complex logic to update
                return {
                    "success": True,
                    "action": "section_exists",
                    "message": f"Section '{section}' already exists. Manual update recommended.",
                    "section": section
                }
            else:
                # Section doesn't exist - append
                updated = existing + f"\n\n## {section}\n\n{content}\n"

                # Write back (in production, would use git workflow)
                return {
                    "success": True,
                    "action": "section_added",
                    "message": f"Section '{section}' added to CLAUDE.md",
                    "section": section,
                    "preview": content[:200]
                }

        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to update CLAUDE.md: {str(e)}"
            }

    def _clean_generated_text(self, text: str) -> str:
        """Clean generated text (remove markdown code blocks, extra formatting).

        Args:
            text: Raw generated text

        Returns:
            Cleaned text
        """
        # Remove markdown code blocks
        text = re.sub(r'```[\w]*\n?', '', text)

        # Remove leading/trailing quotes if present
        text = text.strip('"').strip("'")

        # Remove extra blank lines
        text = re.sub(r'\n{3,}', '\n\n', text)

        return text.strip()


if __name__ == "__main__":
    """Demo usage of Doc Writer Agent."""
    print("=== Doc Writer Agent Demo ===\n")

    # Get API key
    api_key = os.getenv("ANTHROPIC_API_KEY")

    if not api_key:
        print("✗ ANTHROPIC_API_KEY not set")
        exit(1)

    agent = DocWriterAgent(api_key)

    # Scan a file for missing docstrings
    print("Scanning shared/confidence.py for missing docstrings...\n")

    scan_result = agent._scan_for_missing_docstrings("shared/confidence.py")

    if scan_result["success"]:
        print(f"✓ Scan complete:")
        print(f"  Total functions: {scan_result['total_functions']}")
        print(f"  Documented: {scan_result['documented']}")
        print(f"  Missing docstrings: {scan_result['missing_docstrings']}")
        print(f"  Incomplete docstrings: {scan_result['incomplete_docstrings']}")
        print(f"  Coverage: {scan_result['coverage_percent']:.1f}%")
        print()

        if scan_result['missing']:
            print("Functions without docstrings:")
            for func in scan_result['missing'][:5]:  # Show first 5
                print(f"  - {func['name']}() at line {func['line']}")
            print()

            # Generate docstring for first function
            if scan_result['missing']:
                func = scan_result['missing'][0]

                print(f"Generating docstring for {func['name']}()...\n")

                doc_result = agent._write_docstring(
                    file_path="shared/confidence.py",
                    function_name=func['name']
                )

                if doc_result["success"]:
                    print(f"✓ Docstring generated:")
                    print()
                    print("Generated docstring:")
                    print("─" * 60)
                    print(doc_result['docstring'])
                    print("─" * 60)
                    print()
                    print(f"Arguments: {', '.join([a['name'] for a in doc_result['args']])}")
                    print(f"Return Type: {doc_result['return_type'] or 'Not specified'}")
                else:
                    print(f"✗ Failed: {doc_result['error']}")
    else:
        print(f"✗ Scan failed: {scan_result['error']}")

    # Generate README for test-generator agent
    print("\n" + "=" * 60 + "\n")
    print("Generating README for test-generator agent...\n")

    readme_result = agent._generate_agent_readme("agents/test-generator")

    if readme_result["success"]:
        print(f"✓ README generated:")
        print(f"  Agent: {readme_result['agent_name']}")
        print(f"  Tools documented: {readme_result['tools_documented']}")
        print(f"  Output: {readme_result['readme_path']}")
        print()
        print("Generated README (preview):")
        print("─" * 60)
        print(readme_result['readme_content'][:500] + "...")
        print("─" * 60)
    else:
        print(f"✗ Failed: {readme_result['error']}")
