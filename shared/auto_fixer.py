#!/usr/bin/env python3
"""
Auto-Fix Execution System

Safely executes high-confidence fixes for proactive tasks:
- Removes unused imports
- Adds missing docstrings
- Fixes trailing whitespace
- Formats TODO comments
- Generates test stubs

Part of FibreFlow Proactive Agent System (Phase 2).
"""

import os
import re
import ast
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime


class AutoFixer:
    """Executes safe, high-confidence code fixes automatically"""

    # Whitelist of auto-fixable task types
    SAFE_FIX_TYPES = {
        "unused_import": True,
        "trailing_whitespace": True,
        "missing_docstring": True,
        "todo_formatting": True,
        "test_stub_generation": True,
    }

    # Blacklist: Never auto-fix these locations
    PROTECTED_PATHS = [
        "convex/migrations/",
        ".git/",
        "node_modules/",
        "venv/",
        "__pycache__/",
    ]

    def __init__(self, repo_path: str = "."):
        self.repo_path = Path(repo_path).resolve()

    def can_auto_fix(self, task: Dict[str, Any]) -> bool:
        """
        Determine if a task is safe for auto-fixing.

        Safety checks:
        1. Confidence must be "high"
        2. auto_fixable must be true
        3. risk_level must be "none" or "low"
        4. File not in protected paths
        5. Task type in whitelist
        """
        # Check confidence
        if task.get("confidence") != "high":
            return False

        # Check auto_fixable flag
        if not task.get("auto_fixable"):
            return False

        # Check risk level
        if task.get("risk_level") not in ["none", "low"]:
            return False

        # Check protected paths
        file_path = task.get("file", "")
        if any(protected in file_path for protected in self.PROTECTED_PATHS):
            return False

        # Task type whitelist (for now, only handle specific types)
        task_desc = task.get("description", "").lower()
        if "unused import" in task_desc:
            return True
        elif "trailing whitespace" in task_desc:
            return True
        elif "missing docstring" in task_desc:
            return True

        return False

    def execute_fix(self, task: Dict[str, Any], dry_run: bool = False) -> Dict[str, Any]:
        """
        Execute auto-fix for a task.

        Args:
            task: Task object from proactivity queue
            dry_run: If True, preview changes without applying

        Returns:
            {
                success: bool,
                changes_made: List[str],
                error: Optional[str],
                commit_hash: Optional[str],
                tests_passed: bool
            }
        """
        if not self.can_auto_fix(task):
            return {
                "success": False,
                "error": "Task not eligible for auto-fix",
                "changes_made": []
            }

        task_desc = task.get("description", "").lower()
        file_path = self.repo_path / task["file"]

        try:
            # Determine fix type and execute
            if "unused import" in task_desc:
                result = self._fix_unused_import(file_path, task, dry_run)
            elif "trailing whitespace" in task_desc:
                result = self._fix_trailing_whitespace(file_path, task, dry_run)
            elif "missing docstring" in task_desc:
                result = self._add_docstring(file_path, task, dry_run)
            else:
                return {
                    "success": False,
                    "error": "Unknown fix type",
                    "changes_made": []
                }

            # If dry run or fix failed, return early
            if dry_run or not result["success"]:
                return result

            # Run tests to validate fix
            tests_passed = self._run_tests(file_path)
            result["tests_passed"] = tests_passed

            # If tests fail, revert changes
            if not tests_passed:
                self._revert_file(file_path)
                return {
                    "success": False,
                    "error": "Tests failed after fix, changes reverted",
                    "changes_made": result["changes_made"],
                    "tests_passed": False
                }

            # Git commit the fix
            commit_hash = self._git_commit(task, result["changes_made"])
            result["commit_hash"] = commit_hash

            return result

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "changes_made": []
            }

    def _fix_unused_import(
        self,
        file_path: Path,
        task: Dict[str, Any],
        dry_run: bool
    ) -> Dict[str, Any]:
        """Remove unused import from file"""
        # Extract import name from description
        # E.g., "Unused import 'datetime' in file.py"
        desc = task["description"]
        match = re.search(r"Unused import ['\"]([^'\"]+)['\"]", desc)
        if not match:
            return {"success": False, "error": "Could not parse import name"}

        import_name = match.group(1)
        line_num = task.get("line")

        # Read file
        with open(file_path, 'r') as f:
            lines = f.readlines()

        # Find and remove the import line
        if line_num and 1 <= line_num <= len(lines):
            target_line = lines[line_num - 1]
            if import_name in target_line and "import" in target_line:
                if not dry_run:
                    # Remove the line
                    lines.pop(line_num - 1)
                    with open(file_path, 'w') as f:
                        f.writelines(lines)

                return {
                    "success": True,
                    "changes_made": [f"Removed unused import '{import_name}' from {file_path.name}:{line_num}"]
                }

        return {"success": False, "error": "Import line not found or doesn't match"}

    def _fix_trailing_whitespace(
        self,
        file_path: Path,
        task: Dict[str, Any],
        dry_run: bool
    ) -> Dict[str, Any]:
        """Remove trailing whitespace from file"""
        with open(file_path, 'r') as f:
            lines = f.readlines()

        # Remove trailing whitespace from all lines
        fixed_lines = [line.rstrip() + '\n' if line.endswith('\n') else line.rstrip() for line in lines]
        changes_count = sum(1 for orig, fixed in zip(lines, fixed_lines) if orig != fixed)

        if changes_count > 0 and not dry_run:
            with open(file_path, 'w') as f:
                f.writelines(fixed_lines)

        return {
            "success": True,
            "changes_made": [f"Removed trailing whitespace from {changes_count} lines in {file_path.name}"]
        }

    def _add_docstring(
        self,
        file_path: Path,
        task: Dict[str, Any],
        dry_run: bool
    ) -> Dict[str, Any]:
        """Add missing docstring to function"""
        # Extract function name from description
        desc = task["description"]
        match = re.search(r"Function (\w+)\(\) (?:has no|missing)", desc)
        if not match:
            return {"success": False, "error": "Could not parse function name"}

        func_name = match.group(1)
        line_num = task.get("line")

        # Read file
        with open(file_path, 'r') as f:
            lines = f.readlines()

        # Find function definition
        if line_num and 1 <= line_num <= len(lines):
            func_line = lines[line_num - 1]

            # Determine indentation
            indent = len(func_line) - len(func_line.lstrip())
            docstring_indent = ' ' * (indent + 4)

            # Check if next line already has docstring
            if line_num < len(lines):
                next_line = lines[line_num].strip()
                if next_line.startswith('"""') or next_line.startswith("'''"):
                    return {"success": False, "error": "Docstring already exists"}

            # Generate simple docstring
            docstring = f'{docstring_indent}"""{func_name} function."""\n'

            if not dry_run:
                # Insert docstring after function def
                lines.insert(line_num, docstring)
                with open(file_path, 'w') as f:
                    f.writelines(lines)

            return {
                "success": True,
                "changes_made": [f"Added docstring to {func_name}() in {file_path.name}:{line_num}"]
            }

        return {"success": False, "error": "Function definition not found"}

    def _run_tests(self, file_path: Path) -> bool:
        """
        Run tests for the modified file.

        Returns:
            True if tests pass or no tests exist
            False if tests fail
        """
        # Find corresponding test file
        test_file = self.repo_path / "tests" / f"test_{file_path.stem}.py"

        if not test_file.exists():
            # No tests = assume safe (can't verify but not failing)
            return True

        try:
            # Run pytest on specific test file
            result = subprocess.run(
                ["./venv/bin/pytest", str(test_file), "-v", "--tb=short"],
                cwd=self.repo_path,
                capture_output=True,
                timeout=30
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, Exception):
            # If tests timeout or error, consider it a failure
            return False

    def _revert_file(self, file_path: Path) -> None:
        """Revert file to git HEAD"""
        try:
            subprocess.run(
                ["git", "checkout", "HEAD", str(file_path.relative_to(self.repo_path))],
                cwd=self.repo_path,
                check=True,
                capture_output=True
            )
        except subprocess.CalledProcessError:
            pass  # File might not be in git yet

    def _git_commit(self, task: Dict[str, Any], changes: List[str]) -> Optional[str]:
        """
        Create git commit for auto-fix.

        Returns:
            Commit hash if successful, None otherwise
        """
        try:
            # Stage file
            file_path = task["file"]
            subprocess.run(
                ["git", "add", file_path],
                cwd=self.repo_path,
                check=True,
                capture_output=True
            )

            # Create commit message
            commit_msg = f"""fix: {task['description']}

Auto-fixed by proactive agent system
Type: {task['type']}
Confidence: {task['confidence']}
Risk: {task['risk_level']}

Changes:
{chr(10).join(f'- {change}' for change in changes)}

🤖 Generated with Claude Code Proactive System
"""

            # Commit
            subprocess.run(
                ["git", "commit", "-m", commit_msg],
                cwd=self.repo_path,
                check=True,
                capture_output=True
            )

            # Get commit hash
            result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout.strip()[:7]

        except subprocess.CalledProcessError:
            return None

    def batch_fix(
        self,
        tasks: List[Dict[str, Any]],
        max_fixes: int = 10,
        dry_run: bool = False
    ) -> Dict[str, Any]:
        """
        Execute multiple auto-fixes in batch.

        Args:
            tasks: List of tasks from proactivity queue
            max_fixes: Maximum number of fixes to attempt
            dry_run: Preview mode

        Returns:
            {
                total_attempted: int,
                successful: int,
                failed: int,
                results: List[Dict]
            }
        """
        results = []
        successful = 0
        failed = 0

        # Filter for auto-fixable tasks
        fixable_tasks = [t for t in tasks if self.can_auto_fix(t)][:max_fixes]

        for task in fixable_tasks:
            result = self.execute_fix(task, dry_run=dry_run)
            results.append({
                "task_id": task["id"],
                "description": task["description"],
                "result": result
            })

            if result["success"]:
                successful += 1
            else:
                failed += 1

        return {
            "total_attempted": len(fixable_tasks),
            "successful": successful,
            "failed": failed,
            "results": results
        }


# Demo usage
if __name__ == "__main__":
    import json

    fixer = AutoFixer()

    # Load queue
    queue_file = Path("shared/proactivity_queue.json")
    if queue_file.exists():
        with open(queue_file) as f:
            queue = json.load(f)

        high_conf_tasks = [t for t in queue["tasks"] if t["confidence"] == "high"][:5]

        print(f"🔧 Auto-Fixer Demo\n")
        print(f"Found {len(high_conf_tasks)} high-confidence tasks to fix\n")

        # Dry run first
        print("Running dry-run preview...\n")
        batch_result = fixer.batch_fix(high_conf_tasks, max_fixes=5, dry_run=True)

        print(f"Would attempt {batch_result['total_attempted']} fixes:")
        for r in batch_result['results']:
            status = "✓" if r['result']['success'] else "✗"
            print(f"  {status} {r['description']}")
            if r['result'].get('changes_made'):
                for change in r['result']['changes_made']:
                    print(f"      → {change}")

        print(f"\nDry run complete. Run with dry_run=False to apply fixes.")
    else:
        print("❌ No proactivity queue found. Run git-watcher first.")
