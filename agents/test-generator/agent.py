"""
Test Generator Agent

Automatically generates missing test coverage for FibreFlow agents and shared modules.

Capabilities:
    - Detect functions without tests
    - Generate pytest test stubs
    - Infer test cases from docstrings
    - Create integration tests for tools
    - Mock external dependencies

Architecture:
    Inherits from BaseAgent, uses Claude Haiku for cost-effective test generation.

Usage:
    from agents.test_generator.agent import TestGeneratorAgent

    agent = TestGeneratorAgent(api_key)
    result = agent.generate_tests(
        file_path="agents/neon-database/agent.py",
        function_name="execute_query",
        test_type="unit"
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


class TestGeneratorAgent(BaseAgent):
    """Agent for automatic test generation with pytest patterns."""

    def __init__(self, anthropic_api_key: str, model: str = "claude-3-5-haiku-20241022"):
        """Initialize test generator agent.

        Args:
            anthropic_api_key: Anthropic API key
            model: Claude model to use (default: Haiku for cost efficiency)
        """
        super().__init__(anthropic_api_key, model)
        self.project_root = Path(os.getcwd())

    def get_system_prompt(self) -> str:
        """Get system prompt for test generation."""
        return """You are an expert Python test engineer specializing in pytest test generation.

Your capabilities:
1. Generate pytest tests following FibreFlow patterns
2. Infer test cases from function signatures and docstrings
3. Create appropriate mocks for external dependencies
4. Follow pytest markers (@pytest.mark.unit, @pytest.mark.integration)
5. Generate comprehensive test coverage (happy path, edge cases, errors)

FibreFlow Test Patterns:
- Use pytest fixtures for agent initialization
- Add appropriate markers (@pytest.mark.unit, @pytest.mark.agent_name)
- Test both success and failure scenarios
- Mock external dependencies (API calls, database, SSH)
- Follow Google-style docstrings
- Use descriptive test names (test_<function>_<scenario>)

Always generate runnable, high-quality tests that follow best practices."""

    def define_tools(self) -> List[Dict[str, Any]]:
        """Define tools for test generation."""
        return [
            {
                "name": "scan_for_untested_functions",
                "description": "Scan Python file to identify functions without test coverage",
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
                "name": "generate_tests",
                "description": "Generate pytest tests for a specific function",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "file_path": {
                            "type": "string",
                            "description": "Path to file containing function"
                        },
                        "function_name": {
                            "type": "string",
                            "description": "Name of function to test"
                        },
                        "test_type": {
                            "type": "string",
                            "enum": ["unit", "integration"],
                            "description": "Type of test to generate"
                        },
                        "include_edge_cases": {
                            "type": "boolean",
                            "description": "Whether to include edge case tests (default: true)"
                        }
                    },
                    "required": ["file_path", "function_name", "test_type"]
                }
            },
            {
                "name": "analyze_function_signature",
                "description": "Extract function signature, docstring, and context for test generation",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "file_path": {
                            "type": "string",
                            "description": "Path to Python file"
                        },
                        "function_name": {
                            "type": "string",
                            "description": "Name of function to analyze"
                        }
                    },
                    "required": ["file_path", "function_name"]
                }
            },
            {
                "name": "validate_generated_tests",
                "description": "Run generated tests to ensure they're valid",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "test_file_path": {
                            "type": "string",
                            "description": "Path to generated test file"
                        }
                    },
                    "required": ["test_file_path"]
                }
            }
        ]

    def execute_tool(self, tool_name: str, tool_input: Dict[str, Any]) -> Dict[str, Any]:
        """Execute test generation tools."""
        try:
            if tool_name == "scan_for_untested_functions":
                return self._scan_for_untested_functions(tool_input["file_path"])

            elif tool_name == "generate_tests":
                return self._generate_tests(
                    file_path=tool_input["file_path"],
                    function_name=tool_input["function_name"],
                    test_type=tool_input["test_type"],
                    include_edge_cases=tool_input.get("include_edge_cases", True)
                )

            elif tool_name == "analyze_function_signature":
                return self._analyze_function_signature(
                    file_path=tool_input["file_path"],
                    function_name=tool_input["function_name"]
                )

            elif tool_name == "validate_generated_tests":
                return self._validate_generated_tests(tool_input["test_file_path"])

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

    def _scan_for_untested_functions(self, file_path: str) -> Dict[str, Any]:
        """Scan Python file for functions without tests.

        Args:
            file_path: Path to Python file to scan

        Returns:
            Dict with untested functions list
        """
        try:
            # Read source file
            with open(file_path, 'r') as f:
                source = f.read()

            # Parse AST
            tree = ast.parse(source)

            # Extract functions and methods
            functions = []

            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    # Skip private functions (start with _) unless they're special methods
                    if node.name.startswith('_') and not node.name.startswith('__'):
                        continue

                    # Get function signature
                    args = [arg.arg for arg in node.args.args]

                    # Get docstring
                    docstring = ast.get_docstring(node)

                    functions.append({
                        "name": node.name,
                        "line": node.lineno,
                        "args": args,
                        "has_docstring": bool(docstring),
                        "docstring": docstring[:200] if docstring else None
                    })

            # Determine test file path
            test_file_path = self._get_test_file_path(file_path)

            # Check which functions have tests
            existing_tests = set()

            if os.path.exists(test_file_path):
                with open(test_file_path, 'r') as f:
                    test_source = f.read()

                # Look for test functions
                for func in functions:
                    # Common test patterns
                    patterns = [
                        f"def test_{func['name']}",
                        f"def test_{func['name']}_success",
                        f"def test_{func['name']}_error"
                    ]

                    if any(pattern in test_source for pattern in patterns):
                        existing_tests.add(func['name'])

            # Identify untested functions
            untested = [f for f in functions if f['name'] not in existing_tests]

            return {
                "success": True,
                "file_path": file_path,
                "test_file_path": test_file_path,
                "total_functions": len(functions),
                "tested_functions": len(existing_tests),
                "untested_functions": len(untested),
                "untested": untested,
                "coverage_percent": (len(existing_tests) / len(functions) * 100) if functions else 100
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to scan file: {str(e)}"
            }

    def _generate_tests(self, file_path: str, function_name: str, test_type: str, include_edge_cases: bool = True) -> Dict[str, Any]:
        """Generate pytest tests for a function.

        Args:
            file_path: Path to source file
            function_name: Name of function to test
            test_type: Type of test (unit/integration)
            include_edge_cases: Whether to include edge case tests

        Returns:
            Dict with generated test code
        """
        try:
            # Analyze function
            analysis = self._analyze_function_signature(file_path, function_name)

            if not analysis["success"]:
                return analysis

            # Determine agent/module name for markers
            path_parts = Path(file_path).parts

            if "agents" in path_parts:
                agent_idx = path_parts.index("agents")
                module_name = path_parts[agent_idx + 1] if len(path_parts) > agent_idx + 1 else "unknown"
            elif "shared" in path_parts:
                module_name = "shared"
            else:
                module_name = "core"

            # Build test generation prompt
            prompt = f"""Generate pytest tests for this function:

File: {file_path}
Function: {function_name}
Type: {test_type} test
Include Edge Cases: {include_edge_cases}

Function Details:
{analysis['signature']}

{f'Docstring: {analysis["docstring"]}' if analysis['docstring'] else 'No docstring available'}

Requirements:
1. Follow FibreFlow test patterns
2. Use @pytest.mark.{test_type} marker
3. Use @pytest.mark.{module_name.replace('-', '_')} marker
4. Generate happy path test
5. Generate error handling test
6. {'Include edge case tests' if include_edge_cases else 'Skip edge cases'}
7. Mock external dependencies appropriately
8. Use descriptive test names: test_{function_name}_<scenario>

Return ONLY the test code (no explanations)."""

            # Use Claude to generate tests
            message = self.anthropic.messages.create(
                model=self.model,
                max_tokens=2000,
                system=self.get_system_prompt(),
                messages=[{"role": "user", "content": prompt}]
            )

            test_code = message.content[0].text

            # Clean up code (remove markdown formatting if present)
            test_code = self._clean_generated_code(test_code)

            return {
                "success": True,
                "function_name": function_name,
                "test_type": test_type,
                "test_code": test_code,
                "test_file_path": self._get_test_file_path(file_path)
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to generate tests: {str(e)}"
            }

    def _analyze_function_signature(self, file_path: str, function_name: str) -> Dict[str, Any]:
        """Extract function signature and context.

        Args:
            file_path: Path to Python file
            function_name: Name of function to analyze

        Returns:
            Dict with function analysis
        """
        try:
            # Read source
            with open(file_path, 'r') as f:
                source = f.read()

            # Parse AST
            tree = ast.parse(source)

            # Find function
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef) and node.name == function_name:
                    # Get source code of function
                    func_source = ast.get_source_segment(source, node)

                    # Get docstring
                    docstring = ast.get_docstring(node)

                    # Get arguments
                    args = []
                    for arg in node.args.args:
                        arg_name = arg.arg
                        arg_type = None

                        if arg.annotation:
                            if isinstance(arg.annotation, ast.Name):
                                arg_type = arg.annotation.id
                            elif isinstance(arg.annotation, ast.Subscript):
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

                    # Build signature string
                    arg_str = ", ".join([
                        f"{a['name']}: {a['type']}" if a['type'] else a['name']
                        for a in args
                    ])
                    signature = f"def {function_name}({arg_str})"

                    if return_type:
                        signature += f" -> {return_type}"

                    return {
                        "success": True,
                        "function_name": function_name,
                        "signature": signature,
                        "docstring": docstring,
                        "args": args,
                        "return_type": return_type,
                        "source": func_source[:500]  # First 500 chars
                    }

            return {
                "success": False,
                "error": f"Function '{function_name}' not found in {file_path}"
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to analyze function: {str(e)}"
            }

    def _validate_generated_tests(self, test_file_path: str) -> Dict[str, Any]:
        """Run generated tests to validate they execute.

        Args:
            test_file_path: Path to test file

        Returns:
            Dict with validation results
        """
        try:
            import subprocess

            # Run pytest on generated tests
            result = subprocess.run(
                ["pytest", test_file_path, "-v", "--tb=short"],
                capture_output=True,
                text=True,
                timeout=30
            )

            return {
                "success": result.returncode == 0,
                "test_file": test_file_path,
                "exit_code": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "tests_passed": "passed" in result.stdout
            }

        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": "Test validation timed out (30s)"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to validate tests: {str(e)}"
            }

    def _get_test_file_path(self, source_file_path: str) -> str:
        """Determine test file path for a source file.

        Args:
            source_file_path: Path to source file

        Returns:
            Path to corresponding test file
        """
        path = Path(source_file_path)

        # Extract filename
        filename = path.stem  # Without extension

        # Determine test directory and filename
        if "agents" in path.parts:
            # Agent file: tests/test_<agent_name>.py
            agent_idx = path.parts.index("agents")

            if len(path.parts) > agent_idx + 1:
                agent_name = path.parts[agent_idx + 1]
                return f"tests/test_{agent_name.replace('-', '_')}.py"

        elif "shared" in path.parts:
            # Shared module: tests/test_<module_name>.py
            return f"tests/test_{filename}.py"

        # Default
        return f"tests/test_{filename}.py"

    def _clean_generated_code(self, code: str) -> str:
        """Clean generated code (remove markdown formatting).

        Args:
            code: Raw generated code

        Returns:
            Cleaned Python code
        """
        # Remove markdown code blocks
        code = re.sub(r'```python\n?', '', code)
        code = re.sub(r'```\n?', '', code)

        # Remove leading/trailing whitespace
        code = code.strip()

        return code


if __name__ == "__main__":
    """Demo usage of Test Generator Agent."""
    print("=== Test Generator Agent Demo ===\n")

    # Get API key
    api_key = os.getenv("ANTHROPIC_API_KEY")

    if not api_key:
        print("✗ ANTHROPIC_API_KEY not set")
        exit(1)

    agent = TestGeneratorAgent(api_key)

    # Scan a file for untested functions
    print("Scanning shared/confidence.py for untested functions...\n")

    scan_result = agent._scan_for_untested_functions("shared/confidence.py")

    if scan_result["success"]:
        print(f"✓ Scan complete:")
        print(f"  Total functions: {scan_result['total_functions']}")
        print(f"  Tested: {scan_result['tested_functions']}")
        print(f"  Untested: {scan_result['untested_functions']}")
        print(f"  Coverage: {scan_result['coverage_percent']:.1f}%")
        print()

        if scan_result['untested']:
            print("Untested functions:")
            for func in scan_result['untested'][:5]:  # Show first 5
                print(f"  - {func['name']}() at line {func['line']}")
            print()

            # Generate test for first untested function
            if scan_result['untested']:
                func = scan_result['untested'][0]

                print(f"Generating unit test for {func['name']}()...\n")

                test_result = agent._generate_tests(
                    file_path="shared/confidence.py",
                    function_name=func['name'],
                    test_type="unit",
                    include_edge_cases=True
                )

                if test_result["success"]:
                    print(f"✓ Test generated:")
                    print(f"  Test file: {test_result['test_file_path']}")
                    print()
                    print("Generated code:")
                    print("─" * 60)
                    print(test_result['test_code'])
                    print("─" * 60)
                else:
                    print(f"✗ Failed: {test_result['error']}")
    else:
        print(f"✗ Scan failed: {scan_result['error']}")
