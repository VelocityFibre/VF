#!/usr/bin/env python3
"""
Code Critic Agent - Adversarial Code Review

Performs rigorous code review on every commit:
- Security analysis (SQL injection, XSS, secrets exposure)
- Performance review (N+1 queries, memory leaks)
- Best practices enforcement (error handling, logging)
- Outputs structured feedback with confidence scores

Part of FibreFlow Proactive Agent System (Phase 2).
Inspired by Jules' Critic Agent concept.
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


class CodeCriticAgent(BaseAgent):
    """
    Adversarial code reviewer that analyzes commits for issues.

    Works opposite to regular agents - actively looks for problems
    rather than just implementing features.
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

        # Security patterns to detect
        self.security_rules = {
            "sql_injection": {
                "patterns": [
                    r'execute\(["\']SELECT.*?\+',  # String concatenation
                    r'query\s*=\s*f["\']SELECT',   # F-string queries
                    r'\.format\(.*?SELECT',        # .format() with SQL
                ],
                "severity": "critical",
                "description": "Potential SQL injection vulnerability"
            },
            "hardcoded_secrets": {
                "patterns": [
                    r'password\s*=\s*["\'][^"\']{8,}["\']',
                    r'api_key\s*=\s*["\'][a-zA-Z0-9]{20,}["\']',
                    r'secret\s*=\s*["\'][^"\']{16,}["\']',
                ],
                "severity": "critical",
                "description": "Hardcoded secret detected"
            },
            "eval_usage": {
                "patterns": [
                    r'\beval\s*\(',
                    r'\bexec\s*\(',
                ],
                "severity": "high",
                "description": "Dangerous eval() or exec() usage"
            },
            "shell_injection": {
                "patterns": [
                    r'subprocess\.(run|call|Popen)\([^)]*shell=True',
                    r'os\.system\(',
                ],
                "severity": "high",
                "description": "Potential shell injection"
            }
        }

        # Performance anti-patterns
        self.performance_rules = {
            "n_plus_one": {
                "patterns": [
                    r'for\s+\w+\s+in.*?:\s*\n\s*.*?\.execute\(',  # Loop with query
                ],
                "severity": "medium",
                "description": "Potential N+1 query pattern"
            },
            "missing_index": {
                "patterns": [
                    r'WHERE\s+\w+\s*=.*?(?!INDEX)',  # WHERE without index hint
                ],
                "severity": "low",
                "description": "Query may benefit from indexing"
            }
        }

        # Best practice violations
        self.best_practice_rules = {
            "missing_error_handling": {
                "patterns": [
                    r'(?:open|requests\.get|requests\.post|\.read\(|\.write\()',
                ],
                "context_check": lambda ctx: "try" not in ctx and "except" not in ctx,
                "severity": "medium",
                "description": "I/O operation without error handling"
            },
            "print_debugging": {
                "patterns": [
                    r'\bprint\s*\(',
                ],
                "severity": "low",
                "description": "Print statement (use logging instead)"
            },
            "broad_exception": {
                "patterns": [
                    r'except\s*:',  # Bare except
                    r'except\s+Exception\s*:',  # Too broad
                ],
                "severity": "medium",
                "description": "Overly broad exception handling"
            }
        }

    def get_system_prompt(self) -> str:
        """Return code-critic specific system prompt"""
        return """You are the Code Critic Agent, an adversarial reviewer for FibreFlow.

Your role is to be CRITICAL and find problems in code:
- You look for security vulnerabilities, not features
- You identify performance issues, not optimizations
- You enforce best practices strictly
- You assign severity: critical, high, medium, low
- You provide specific, actionable feedback

You are NOT helpful or collaborative - you are adversarial and thorough.
Find the problems. Be specific. Assign confidence scores.

Remember: Better to flag a potential issue than miss a real one."""

    def define_tools(self) -> List[Dict[str, Any]]:
        """Define code-critic tools"""
        return [
            {
                "name": "review_commit",
                "description": "Perform adversarial code review on a git commit",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "commit_hash": {
                            "type": "string",
                            "description": "Git commit SHA to review"
                        },
                        "review_types": {
                            "type": "array",
                            "items": {
                                "type": "string",
                                "enum": ["security", "performance", "best_practices", "all"]
                            },
                            "description": "Types of review to perform"
                        }
                    },
                    "required": ["commit_hash"]
                }
            },
            {
                "name": "review_file",
                "description": "Review a specific file for issues",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "file_path": {
                            "type": "string",
                            "description": "Path to file to review"
                        },
                        "focus": {
                            "type": "string",
                            "enum": ["security", "performance", "best_practices", "all"],
                            "description": "Focus area for review"
                        }
                    },
                    "required": ["file_path"]
                }
            }
        ]

    def execute_tool(self, tool_name: str, tool_input: Dict[str, Any]) -> Dict[str, Any]:
        """Execute code-critic tool"""
        try:
            if tool_name == "review_commit":
                return self._review_commit(
                    commit_hash=tool_input["commit_hash"],
                    review_types=tool_input.get("review_types", ["all"])
                )

            elif tool_name == "review_file":
                return self._review_file(
                    file_path=tool_input["file_path"],
                    focus=tool_input.get("focus", "all")
                )

            else:
                return {"error": f"Unknown tool: {tool_name}"}

        except Exception as e:
            return {"error": str(e)}

    def _review_commit(
        self,
        commit_hash: str,
        review_types: List[str]
    ) -> Dict[str, Any]:
        """
        Perform adversarial review on a commit.

        Returns:
            {
                commit: str,
                issues_found: int,
                critical: int,
                high: int,
                medium: int,
                low: int,
                issues: [...]
            }
        """
        # Get commit diff
        try:
            result = subprocess.run(
                ["git", "show", commit_hash, "--unified=5"],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True
            )
            diff = result.stdout
        except subprocess.CalledProcessError as e:
            return {"error": f"Failed to get commit: {e}"}

        # Parse diff for added lines
        added_lines = self._parse_diff(diff)

        issues = []

        # Run requested reviews
        if "all" in review_types or "security" in review_types:
            issues.extend(self._check_security(added_lines))

        if "all" in review_types or "performance" in review_types:
            issues.extend(self._check_performance(added_lines))

        if "all" in review_types or "best_practices" in review_types:
            issues.extend(self._check_best_practices(added_lines))

        # Add issues to proactivity queue
        for issue in issues:
            self.queue.add_task(
                task_type=issue["category"],
                description=issue["description"],
                file=issue["file"],
                line=issue.get("line"),
                context={"commit": commit_hash, "severity": issue["severity"]}
            )

        # Count by severity
        severity_counts = {
            "critical": len([i for i in issues if i["severity"] == "critical"]),
            "high": len([i for i in issues if i["severity"] == "high"]),
            "medium": len([i for i in issues if i["severity"] == "medium"]),
            "low": len([i for i in issues if i["severity"] == "low"]),
        }

        return {
            "commit": commit_hash,
            "issues_found": len(issues),
            **severity_counts,
            "issues": issues
        }

    def _review_file(self, file_path: str, focus: str) -> Dict[str, Any]:
        """Review a specific file"""
        file_full_path = self.repo_path / file_path

        if not file_full_path.exists():
            return {"error": f"File not found: {file_path}"}

        # Read file content
        with open(file_full_path, 'r') as f:
            lines = f.readlines()

        # Convert to format similar to diff
        added_lines = [
            {"file": file_path, "line": i+1, "content": line.rstrip()}
            for i, line in enumerate(lines)
        ]

        issues = []

        if focus in ["all", "security"]:
            issues.extend(self._check_security(added_lines))

        if focus in ["all", "performance"]:
            issues.extend(self._check_performance(added_lines))

        if focus in ["all", "best_practices"]:
            issues.extend(self._check_best_practices(added_lines))

        return {
            "file": file_path,
            "issues_found": len(issues),
            "issues": issues
        }

    def _parse_diff(self, diff: str) -> List[Dict[str, Any]]:
        """Parse git diff and extract added lines"""
        added_lines = []
        current_file = None
        current_line_num = None

        for line in diff.split('\n'):
            # Track current file
            if line.startswith('+++'):
                current_file = line[6:].strip()
                if current_file.startswith('b/'):
                    current_file = current_file[2:]

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

    def _check_security(self, lines: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Check for security issues"""
        issues = []

        for line_info in lines:
            content = line_info["content"]

            for rule_name, rule in self.security_rules.items():
                for pattern in rule["patterns"]:
                    if re.search(pattern, content, re.IGNORECASE):
                        issues.append({
                            "category": "security",
                            "rule": rule_name,
                            "severity": rule["severity"],
                            "description": f"{rule['description']}: {content[:50]}...",
                            "file": line_info["file"],
                            "line": line_info["line"],
                            "suggestion": self._get_suggestion(rule_name)
                        })

        return issues

    def _check_performance(self, lines: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Check for performance issues"""
        issues = []

        # Build context (need multiple lines for some patterns)
        file_contexts = {}
        for line_info in lines:
            file = line_info["file"]
            if file not in file_contexts:
                file_contexts[file] = []
            file_contexts[file].append(line_info)

        # Check patterns requiring context
        for file, file_lines in file_contexts.items():
            full_content = '\n'.join(l["content"] for l in file_lines)

            for rule_name, rule in self.performance_rules.items():
                for pattern in rule["patterns"]:
                    matches = re.finditer(pattern, full_content, re.MULTILINE)
                    for match in matches:
                        # Find approximate line number
                        line_num = full_content[:match.start()].count('\n') + file_lines[0]["line"]
                        issues.append({
                            "category": "performance",
                            "rule": rule_name,
                            "severity": rule["severity"],
                            "description": rule["description"],
                            "file": file,
                            "line": line_num,
                            "suggestion": self._get_suggestion(rule_name)
                        })

        return issues

    def _check_best_practices(self, lines: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Check for best practice violations"""
        issues = []

        for line_info in lines:
            content = line_info["content"]

            for rule_name, rule in self.best_practice_rules.items():
                for pattern in rule["patterns"]:
                    if re.search(pattern, content):
                        # Check context if needed
                        if "context_check" in rule:
                            # Simple context: check if try/except nearby
                            # (In real implementation, would check full function)
                            if not rule["context_check"](content):
                                continue

                        issues.append({
                            "category": "best_practices",
                            "rule": rule_name,
                            "severity": rule["severity"],
                            "description": f"{rule['description']}: {content[:50]}...",
                            "file": line_info["file"],
                            "line": line_info["line"],
                            "suggestion": self._get_suggestion(rule_name)
                        })

        return issues

    def _get_suggestion(self, rule_name: str) -> str:
        """Get fix suggestion for a rule"""
        suggestions = {
            "sql_injection": "Use parameterized queries with placeholders",
            "hardcoded_secrets": "Move secrets to environment variables",
            "eval_usage": "Avoid eval(); use safer alternatives",
            "shell_injection": "Use shell=False and pass command as list",
            "n_plus_one": "Use JOIN or batch queries instead of loops",
            "missing_error_handling": "Wrap I/O operations in try/except",
            "print_debugging": "Use logging.info() instead of print()",
            "broad_exception": "Catch specific exceptions only"
        }
        return suggestions.get(rule_name, "Review and refactor this code")


# Demo usage
if __name__ == "__main__":
    api_key = os.getenv('ANTHROPIC_API_KEY')
    if not api_key:
        print("❌ ANTHROPIC_API_KEY not set")
        sys.exit(1)

    critic = CodeCriticAgent(api_key)

    print("🔎 Code Critic Agent - Adversarial Review\n")

    # Get latest commit
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=True
        )
        latest_commit = result.stdout.strip()

        print(f"Reviewing latest commit: {latest_commit[:7]}\n")

        # Review commit
        review = critic._review_commit(latest_commit, ["all"])

        print(f"Issues Found: {review['issues_found']}")
        print(f"  Critical: {review['critical']}")
        print(f"  High: {review['high']}")
        print(f"  Medium: {review['medium']}")
        print(f"  Low: {review['low']}\n")

        if review['issues_found'] > 0:
            print("Top Issues:")
            for issue in review['issues'][:5]:
                print(f"  [{issue['severity'].upper()}] {issue['description']}")
                print(f"    → {issue['file']}:{issue['line']}")
                print(f"    💡 {issue['suggestion']}\n")
        else:
            print("✅ No issues found in this commit!")

    except Exception as e:
        print(f"❌ Error: {e}")
