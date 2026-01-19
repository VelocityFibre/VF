#!/usr/bin/env python3
"""
Git Watcher Agent - Continuous Repository Observation

Monitors git repository for proactive task opportunities:
- TODO/FIXME/HACK comments
- Missing test coverage
- Security patterns (SQL injection, exposed secrets)
- Performance issues
- Code quality problems

Part of FibreFlow Proactive Agent System (Jules Level 1).

Inherits from: shared.base_agent.BaseAgent
"""

import os
import sys
import re
import subprocess
from pathlib import Path
from typing import List, Dict, Any

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from shared.base_agent import BaseAgent
from shared.confidence import ProactivityQueue


class GitWatcherAgent(BaseAgent):
    """
    Proactive repository monitoring agent.

    Continuously scans codebase for improvement opportunities
    and populates the proactivity queue with discovered tasks.
    """

    def __init__(
        self,
        anthropic_api_key: str,
        model: str = "claude-3-5-haiku-20241022",
        repository_path: str = "."
    ):
        super().__init__(anthropic_api_key, model)
        self.repo_path = Path(repository_path).resolve()
        self.queue = ProactivityQueue()

        # Patterns for detection
        self.todo_patterns = [
            r"#\s*TODO[:\s]+(.+)",
            r"#\s*FIXME[:\s]+(.+)",
            r"#\s*HACK[:\s]+(.+)",
            r"#\s*XXX[:\s]+(.+)",
            r"//\s*TODO[:\s]+(.+)",  # JavaScript/TypeScript
            r"//\s*FIXME[:\s]+(.+)"
        ]

        self.security_patterns = {
            "sql_injection": [
                r"execute\(['\"]SELECT.*\+",  # String concatenation in SQL
                r"query\s*=\s*['\"]SELECT.*%s",  # Old-style formatting
                r"\.format\([^\)]*SELECT",  # format() with SELECT
            ],
            "exposed_secret": [
                r"api_key\s*=\s*['\"][^'\"]{20,}['\"]",  # Hardcoded API keys
                r"password\s*=\s*['\"][^'\"]+['\"]",  # Hardcoded passwords
                r"token\s*=\s*['\"][^'\"]{20,}['\"]",  # Hardcoded tokens
            ],
            "dangerous_eval": [
                r"eval\(",  # eval() usage
                r"exec\(",  # exec() usage
            ]
        }

        # Files to ignore
        self.ignore_patterns = [
            ".git/",
            "venv/",
            "node_modules/",
            "__pycache__/",
            "*.pyc",
            "*.log",
            ".env"
        ]

    def get_system_prompt(self) -> str:
        """Return git-watcher specific system prompt"""
        return """You are the Git Watcher Agent, part of FibreFlow's proactive agent system.

Your role is to continuously observe the codebase and discover opportunities for improvement:
- Scan for TODO/FIXME/HACK comments
- Detect missing test coverage for new functions
- Identify security patterns (SQL injection, exposed secrets)
- Find performance issues
- Spot code quality problems

When you find issues, you add them to the proactivity queue with confidence scores:
- HIGH: Trivial fixes (unused imports, missing docstrings) - auto-fixable
- MEDIUM: Requires review (performance optimizations) - needs human approval
- LOW: High risk (security issues, architecture changes) - careful review needed

You are the "eyes" of the proactive system - always watching, always learning."""

    def define_tools(self) -> List[Dict[str, Any]]:
        """Define git-watcher tools"""
        return [
            {
                "name": "scan_repository",
                "description": "Scan git repository for proactive task opportunities (TODOs, missing tests, security issues, etc.)",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "scan_type": {
                            "type": "string",
                            "enum": ["todos", "missing_tests", "security", "performance", "all"],
                            "description": "Type of scan to perform"
                        },
                        "path": {
                            "type": "string",
                            "description": "Specific directory to scan (optional, default: entire repo)"
                        },
                        "since_commit": {
                            "type": "string",
                            "description": "Only scan changes since this commit hash (optional)"
                        }
                    },
                    "required": ["scan_type"]
                }
            },
            {
                "name": "analyze_commit",
                "description": "Analyze a specific git commit for issues (security, performance, best practices, tests)",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "commit_hash": {
                            "type": "string",
                            "description": "Git commit SHA to analyze"
                        },
                        "analysis_types": {
                            "type": "array",
                            "items": {
                                "type": "string",
                                "enum": ["security", "performance", "best_practices", "tests"]
                            },
                            "description": "Types of analysis to perform"
                        }
                    },
                    "required": ["commit_hash", "analysis_types"]
                }
            },
            {
                "name": "get_proactivity_queue",
                "description": "Retrieve current proactivity queue with filtering options",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "filter_confidence": {
                            "type": "string",
                            "enum": ["high", "medium", "low", "all"],
                            "description": "Filter by confidence level"
                        },
                        "filter_type": {
                            "type": "string",
                            "description": "Filter by task type (optional)"
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum tasks to return (default: 50)"
                        }
                    },
                    "required": []
                }
            }
        ]

    def execute_tool(self, tool_name: str, tool_input: Dict[str, Any]) -> Dict[str, Any]:
        """Execute git-watcher tool"""
        try:
            if tool_name == "scan_repository":
                return self._scan_repository(
                    scan_type=tool_input["scan_type"],
                    path=tool_input.get("path"),
                    since_commit=tool_input.get("since_commit")
                )

            elif tool_name == "analyze_commit":
                return self._analyze_commit(
                    commit_hash=tool_input["commit_hash"],
                    analysis_types=tool_input["analysis_types"]
                )

            elif tool_name == "get_proactivity_queue":
                return self.queue.get_tasks(
                    filter_confidence=tool_input.get("filter_confidence", "all"),
                    filter_type=tool_input.get("filter_type"),
                    limit=tool_input.get("limit", 50)
                )

            else:
                return {"error": f"Unknown tool: {tool_name}"}

        except Exception as e:
            return {"error": str(e)}

    def _scan_repository(
        self,
        scan_type: str,
        path: str = None,
        since_commit: str = None
    ) -> Dict[str, Any]:
        """
        Scan repository for proactive opportunities.

        Returns:
            {tasks_discovered: int, tasks: [...]}
        """
        tasks_found = []

        # Determine scan path
        scan_path = Path(path) if path else self.repo_path

        # Get files to scan
        if since_commit:
            # Only scan changed files
            files = self._get_changed_files(since_commit)
        else:
            # Scan all files
            files = self._get_all_files(scan_path)

        # Perform scans based on type
        if scan_type in ["todos", "all"]:
            tasks_found.extend(self._scan_for_todos(files))

        if scan_type in ["security", "all"]:
            tasks_found.extend(self._scan_for_security_issues(files))

        if scan_type in ["missing_tests", "all"]:
            tasks_found.extend(self._scan_for_missing_tests(files))

        # Add discovered tasks to queue
        for task in tasks_found:
            self.queue.add_task(
                task_type=task["type"],
                description=task["description"],
                file=task["file"],
                line=task.get("line"),
                context=task.get("context", {})
            )

        return {
            "tasks_discovered": len(tasks_found),
            "tasks": tasks_found
        }

    def _analyze_commit(
        self,
        commit_hash: str,
        analysis_types: List[str]
    ) -> Dict[str, Any]:
        """
        Analyze specific commit for issues.

        Returns:
            {commit: str, issues_found: int, issues: [...]}
        """
        issues = []

        # Get commit diff
        try:
            result = subprocess.run(
                ["git", "show", commit_hash, "--unified=0"],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True
            )
            diff = result.stdout
        except subprocess.CalledProcessError as e:
            return {"error": f"Failed to get commit diff: {e}"}

        # Parse diff for added lines
        added_lines = self._parse_diff_for_additions(diff)

        # Perform requested analyses
        if "security" in analysis_types:
            issues.extend(self._analyze_security(added_lines))

        if "tests" in analysis_types:
            issues.extend(self._analyze_test_coverage(added_lines, commit_hash))

        if "best_practices" in analysis_types:
            issues.extend(self._analyze_best_practices(added_lines))

        # Add issues to queue
        for issue in issues:
            self.queue.add_task(
                task_type=issue["type"],
                description=issue["description"],
                file=issue["file"],
                line=issue.get("line"),
                context={"commit": commit_hash}
            )

        return {
            "commit": commit_hash,
            "issues_found": len(issues),
            "issues": issues
        }

    def _get_all_files(self, scan_path: Path) -> List[Path]:
        """Get all Python files in repository"""
        files = []
        for pattern in ["**/*.py", "**/*.js", "**/*.ts", "**/*.md"]:
            files.extend(scan_path.glob(pattern))

        # Filter ignored patterns
        filtered = []
        for f in files:
            if not any(ignore in str(f) for ignore in self.ignore_patterns):
                filtered.append(f)

        return filtered

    def _get_changed_files(self, since_commit: str) -> List[Path]:
        """Get files changed since specific commit"""
        try:
            result = subprocess.run(
                ["git", "diff", "--name-only", since_commit, "HEAD"],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True
            )
            changed = result.stdout.strip().split('\n')
            return [self.repo_path / f for f in changed if f]
        except subprocess.CalledProcessError:
            return []

    def _scan_for_todos(self, files: List[Path]) -> List[Dict[str, Any]]:
        """Scan files for TODO/FIXME/HACK comments"""
        tasks = []

        for file_path in files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    for line_num, line in enumerate(f, 1):
                        for pattern in self.todo_patterns:
                            match = re.search(pattern, line)
                            if match:
                                comment_text = match.group(1).strip() if match.groups() else "See comment"
                                tasks.append({
                                    "type": "tech_debt",
                                    "description": f"TODO comment: {comment_text}",
                                    "file": str(file_path.relative_to(self.repo_path)),
                                    "line": line_num,
                                    "context": {"full_line": line.strip()}
                                })
            except Exception:
                continue  # Skip files that can't be read

        return tasks

    def _scan_for_security_issues(self, files: List[Path]) -> List[Dict[str, Any]]:
        """Scan for security vulnerabilities"""
        tasks = []

        for file_path in files:
            if not file_path.suffix in ['.py', '.js', '.ts']:
                continue  # Only scan code files

            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    lines = content.split('\n')

                    for issue_type, patterns in self.security_patterns.items():
                        for pattern in patterns:
                            for match in re.finditer(pattern, content):
                                line_num = content[:match.start()].count('\n') + 1
                                tasks.append({
                                    "type": "security",
                                    "description": f"Potential {issue_type.replace('_', ' ')} detected",
                                    "file": str(file_path.relative_to(self.repo_path)),
                                    "line": line_num,
                                    "context": {"code_snippet": lines[line_num - 1].strip()}
                                })
            except Exception:
                continue

        return tasks

    def _scan_for_missing_tests(self, files: List[Path]) -> List[Dict[str, Any]]:
        """Scan for functions without test coverage"""
        tasks = []

        # Simple heuristic: Find new functions in non-test files
        for file_path in files:
            if "test" in str(file_path) or not file_path.suffix == '.py':
                continue  # Skip test files and non-Python

            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    for line_num, line in enumerate(f, 1):
                        # Detect function definitions
                        if re.match(r'^\s*def\s+(\w+)\s*\(', line):
                            func_match = re.search(r'def\s+(\w+)', line)
                            if func_match:
                                func_name = func_match.group(1)
                                if not func_name.startswith('_'):  # Skip private functions
                                    # Check if test exists (simplified heuristic)
                                    test_file = self.repo_path / "tests" / f"test_{file_path.stem}.py"
                                    has_test = self._function_has_test(test_file, func_name)

                                    if not has_test:
                                        tasks.append({
                                            "type": "test_coverage",
                                            "description": f"Function {func_name}() has no test coverage",
                                            "file": str(file_path.relative_to(self.repo_path)),
                                            "line": line_num,
                                            "context": {"function_name": func_name}
                                        })
            except Exception:
                continue

        return tasks

    def _function_has_test(self, test_file: Path, func_name: str) -> bool:
        """Check if function has corresponding test"""
        if not test_file.exists():
            return False

        try:
            with open(test_file, 'r') as f:
                content = f.read()
                # Look for test_function_name pattern
                return bool(re.search(rf'def test_{func_name}', content))
        except Exception:
            return False

    def _parse_diff_for_additions(self, diff: str) -> List[Dict[str, Any]]:
        """Parse git diff and extract added lines"""
        added_lines = []
        current_file = None
        current_line_num = None

        for line in diff.split('\n'):
            # Track current file
            if line.startswith('+++'):
                current_file = line[6:].strip()

            # Track line numbers
            elif line.startswith('@@'):
                match = re.search(r'\+(\d+)', line)
                if match:
                    current_line_num = int(match.group(1))

            # Collect added lines
            elif line.startswith('+') and not line.startswith('+++'):
                if current_file and current_line_num:
                    added_lines.append({
                        "file": current_file,
                        "line": current_line_num,
                        "content": line[1:].strip()
                    })
                    current_line_num += 1

        return added_lines

    def _analyze_security(self, added_lines: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Analyze added lines for security issues"""
        issues = []

        for line_info in added_lines:
            content = line_info["content"]

            for issue_type, patterns in self.security_patterns.items():
                for pattern in patterns:
                    if re.search(pattern, content):
                        issues.append({
                            "severity": "high",
                            "type": "security",
                            "description": f"Potential {issue_type.replace('_', ' ')} in new code",
                            "file": line_info["file"],
                            "line": line_info["line"]
                        })

        return issues

    def _analyze_test_coverage(self, added_lines: List[Dict[str, Any]], commit_hash: str) -> List[Dict[str, Any]]:
        """Check if new functions have tests"""
        issues = []

        for line_info in added_lines:
            content = line_info["content"]

            # Detect new function definitions
            if re.match(r'^\s*def\s+(\w+)\s*\(', content):
                func_match = re.search(r'def\s+(\w+)', content)
                if func_match:
                    func_name = func_match.group(1)
                    if not func_name.startswith('_'):  # Skip private
                        issues.append({
                            "severity": "medium",
                            "type": "test_coverage",
                            "description": f"New function {func_name}() added without test",
                            "file": line_info["file"],
                            "line": line_info["line"]
                        })

        return issues

    def _analyze_best_practices(self, added_lines: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Check for best practice violations"""
        issues = []

        for line_info in added_lines:
            content = line_info["content"]

            # Check for missing error handling
            if re.search(r'open\(|\.read\(|\.write\(|requests\.', content):
                if 'try' not in content and 'except' not in content:
                    issues.append({
                        "severity": "medium",
                        "type": "best_practices",
                        "description": "I/O operation without error handling",
                        "file": line_info["file"],
                        "line": line_info["line"]
                    })

        return issues


# Demo usage
if __name__ == "__main__":
    api_key = os.getenv('ANTHROPIC_API_KEY')
    if not api_key:
        print("❌ ANTHROPIC_API_KEY not set")
        sys.exit(1)

    agent = GitWatcherAgent(api_key)

    print("🔍 Git Watcher Agent - Proactive Repository Scanner\n")
    print("Scanning repository for proactive opportunities...\n")

    # Scan for all types
    result = agent._scan_repository(scan_type="all")

    print(f"✅ Discovered {result['tasks_discovered']} tasks:\n")
    for task in result["tasks"][:10]:  # Show first 10
        print(f"  [{task['type']}] {task['description']}")
        print(f"    → {task['file']}:{task.get('line', '?')}\n")

    # Show queue status
    queue_status = agent.queue.get_tasks(filter_confidence="all")
    print(f"\n📊 Proactivity Queue Status:")
    print(f"  Total tasks: {queue_status['total_tasks']}")
    print(f"  High confidence: {len([t for t in queue_status['tasks'] if t['confidence'] == 'high'])}")
    print(f"  Medium confidence: {len([t for t in queue_status['tasks'] if t['confidence'] == 'medium'])}")
    print(f"  Low confidence: {len([t for t in queue_status['tasks'] if t['confidence'] == 'low'])}")
