"""
Conflict Predictor

Predicts merge conflicts before they happen by analyzing active branches.
This is the foundation of Phase 4's team alignment capabilities.

Architecture:
    Git Branches → Conflict Analysis (Textual + Semantic + Integration)
                → Conflict Probability → Merge Order Suggestion → Alerts

Conflict Types:
    1. Textual: Same lines modified (easy, high confidence)
    2. Semantic: Same functions modified differently (medium confidence)
    3. Integration: Incompatible changes in different parts (hard, lower confidence)

Usage:
    from shared.conflict_predictor import ConflictPredictor

    predictor = ConflictPredictor()

    # Predict conflicts between two branches
    result = predictor.predict_conflict("feature/branch-a", "feature/branch-b")
    print(f"Conflict Probability: {result['probability']:.0%}")
    print(f"Suggestion: {result['suggestion']}")

    # Check all active branches
    matrix = predictor.check_all_branches()
    print(f"High-risk pairs: {matrix['high_risk_count']}")
"""

import os
import subprocess
import ast
import re
from typing import Dict, Any, List, Set, Tuple, Optional
from pathlib import Path
from datetime import datetime


class ConflictPredictor:
    """Predicts merge conflicts between git branches."""

    # Alert thresholds
    THRESHOLDS = {
        "critical": 0.80,  # Block merge, immediate notification
        "high": 0.60,      # Warning, suggest coordination
        "medium": 0.40,    # Informational, monitor
        "low": 0.00        # Safe to merge
    }

    def __init__(self):
        """Initialize conflict predictor."""
        self.project_root = Path(os.getcwd())

    def predict_conflict(self, branch_a: str, branch_b: str, base_branch: str = "main") -> Dict[str, Any]:
        """Predict conflict probability between two branches.

        Args:
            branch_a: First branch name
            branch_b: Second branch name
            base_branch: Base branch for comparison (default: main)

        Returns:
            Dict with conflict prediction and details
        """
        try:
            # Get changed files in each branch
            files_a = self._get_changed_files(branch_a, base_branch)
            files_b = self._get_changed_files(branch_b, base_branch)

            if not files_a["success"] or not files_b["success"]:
                return {
                    "success": False,
                    "error": "Failed to get changed files"
                }

            # Find overlapping files
            overlap = set(files_a["files"]) & set(files_b["files"])

            if not overlap:
                return {
                    "success": True,
                    "probability": 0.0,
                    "level": "none",
                    "overlapping_files": 0,
                    "textual_conflicts": 0,
                    "semantic_conflicts": 0,
                    "integration_conflicts": 0,
                    "suggestion": "No overlapping files - safe to merge"
                }

            # Check for textual conflicts
            textual = self._check_textual_conflicts(overlap, branch_a, branch_b, base_branch)

            # Check for semantic conflicts
            semantic = self._check_semantic_conflicts(overlap, branch_a, branch_b)

            # Check for integration conflicts
            integration = self._check_integration_conflicts(branch_a, branch_b)

            # Calculate probability
            probability = self._calculate_probability(
                overlapping_files=len(overlap),
                textual=textual,
                semantic=semantic,
                integration=integration
            )

            # Determine level
            level = self._get_conflict_level(probability)

            # Generate suggestion
            suggestion = self._generate_suggestion(level, probability, branch_a, branch_b)

            return {
                "success": True,
                "branch_a": branch_a,
                "branch_b": branch_b,
                "probability": probability,
                "level": level,
                "overlapping_files": len(overlap),
                "textual_conflicts": len(textual),
                "semantic_conflicts": len(semantic),
                "integration_conflicts": len(integration),
                "details": {
                    "textual": textual[:5],  # First 5
                    "semantic": semantic[:5],
                    "integration": integration[:5]
                },
                "suggestion": suggestion
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Conflict prediction failed: {str(e)}"
            }

    def check_all_branches(self, base_branch: str = "main") -> Dict[str, Any]:
        """Check all active branches for potential conflicts.

        Args:
            base_branch: Base branch for comparison

        Returns:
            Conflict matrix for all branch pairs
        """
        try:
            # Get all branches
            branches = self._get_all_branches()

            if not branches["success"]:
                return {
                    "success": False,
                    "error": branches.get("error")
                }

            # Remove base branch
            active_branches = [b for b in branches["branches"] if b != base_branch]

            if len(active_branches) < 2:
                return {
                    "success": True,
                    "message": "Need at least 2 active branches for conflict checking",
                    "branches": active_branches
                }

            # Check all pairs
            conflicts = []

            for i, branch_a in enumerate(active_branches):
                for branch_b in active_branches[i+1:]:
                    result = self.predict_conflict(branch_a, branch_b, base_branch)

                    if result["success"] and result["probability"] > 0:
                        conflicts.append({
                            "branch_a": branch_a,
                            "branch_b": branch_b,
                            "probability": result["probability"],
                            "level": result["level"]
                        })

            # Sort by probability
            conflicts.sort(key=lambda x: x["probability"], reverse=True)

            # Count by level
            critical_count = len([c for c in conflicts if c["level"] == "critical"])
            high_count = len([c for c in conflicts if c["level"] == "high"])
            medium_count = len([c for c in conflicts if c["level"] == "medium"])

            return {
                "success": True,
                "total_branches": len(active_branches),
                "total_pairs_checked": len(active_branches) * (len(active_branches) - 1) // 2,
                "conflicts_detected": len(conflicts),
                "critical_count": critical_count,
                "high_count": high_count,
                "medium_count": medium_count,
                "conflicts": conflicts
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Branch conflict check failed: {str(e)}"
            }

    def _get_changed_files(self, branch: str, base_branch: str) -> Dict[str, Any]:
        """Get files changed in a branch relative to base.

        Args:
            branch: Branch to check
            base_branch: Base branch for comparison

        Returns:
            Dict with list of changed files
        """
        try:
            # Get diff
            result = subprocess.run(
                ["git", "diff", "--name-only", f"{base_branch}...{branch}"],
                capture_output=True,
                text=True,
                check=True
            )

            files = [f for f in result.stdout.strip().split('\n') if f]

            return {
                "success": True,
                "files": files
            }

        except subprocess.CalledProcessError as e:
            return {
                "success": False,
                "error": f"Git diff failed: {e.stderr}"
            }

    def _check_textual_conflicts(
        self,
        overlap: Set[str],
        branch_a: str,
        branch_b: str,
        base_branch: str
    ) -> List[Dict[str, Any]]:
        """Check for textual conflicts in overlapping files.

        Args:
            overlap: Set of overlapping files
            branch_a: First branch
            branch_b: Second branch
            base_branch: Base branch

        Returns:
            List of textual conflict details
        """
        conflicts = []

        for file_path in overlap:
            try:
                # Get diffs for each branch
                diff_a = subprocess.run(
                    ["git", "diff", f"{base_branch}...{branch_a}", "--", file_path],
                    capture_output=True,
                    text=True
                )

                diff_b = subprocess.run(
                    ["git", "diff", f"{base_branch}...{branch_b}", "--", file_path],
                    capture_output=True,
                    text=True
                )

                # Extract changed line ranges
                ranges_a = self._extract_line_ranges(diff_a.stdout)
                ranges_b = self._extract_line_ranges(diff_b.stdout)

                # Check for overlapping ranges
                for range_a in ranges_a:
                    for range_b in ranges_b:
                        if self._ranges_overlap(range_a, range_b):
                            conflicts.append({
                                "file": file_path,
                                "line_range": range_a,
                                "type": "textual"
                            })

            except Exception as e:
                # Skip files that can't be analyzed
                continue

        return conflicts

    def _check_semantic_conflicts(
        self,
        overlap: Set[str],
        branch_a: str,
        branch_b: str
    ) -> List[Dict[str, Any]]:
        """Check for semantic conflicts in overlapping files.

        Args:
            overlap: Set of overlapping files
            branch_a: First branch
            branch_b: Second branch

        Returns:
            List of semantic conflict details
        """
        conflicts = []

        # Only check Python files for semantic conflicts
        python_files = [f for f in overlap if f.endswith('.py')]

        for file_path in python_files:
            try:
                # Get file content from each branch
                content_a = self._get_file_content(branch_a, file_path)
                content_b = self._get_file_content(branch_b, file_path)

                if not content_a or not content_b:
                    continue

                # Parse AST
                tree_a = ast.parse(content_a)
                tree_b = ast.parse(content_b)

                # Get function signatures
                functions_a = self._extract_functions(tree_a)
                functions_b = self._extract_functions(tree_b)

                # Check for signature changes
                for func_name in set(functions_a.keys()) & set(functions_b.keys()):
                    sig_a = functions_a[func_name]
                    sig_b = functions_b[func_name]

                    if sig_a != sig_b:
                        conflicts.append({
                            "file": file_path,
                            "function": func_name,
                            "signature_a": sig_a,
                            "signature_b": sig_b,
                            "type": "semantic"
                        })

            except Exception as e:
                # Skip files that can't be parsed
                continue

        return conflicts

    def _check_integration_conflicts(self, branch_a: str, branch_b: str) -> List[Dict[str, Any]]:
        """Check for integration conflicts between branches.

        Args:
            branch_a: First branch
            branch_b: Second branch

        Returns:
            List of integration conflict details
        """
        conflicts = []

        # Check for API endpoint changes
        # (Simplified - would need more sophisticated analysis in production)

        try:
            # Get all files in each branch
            files_a = self._get_changed_files(branch_a, "main")
            files_b = self._get_changed_files(branch_b, "main")

            if not files_a["success"] or not files_b["success"]:
                return conflicts

            # Check if one branch modifies API definitions and other uses them
            api_files = ["api.py", "routes.py", "endpoints.py", "agent.py"]

            api_changes_a = [f for f in files_a["files"] if any(api in f for api in api_files)]
            api_changes_b = [f for f in files_b["files"] if any(api in f for api in api_files)]

            # If both branches modify APIs, potential integration conflict
            if api_changes_a and api_changes_b:
                conflicts.append({
                    "type": "integration",
                    "reason": "Both branches modify API-related files",
                    "files_a": api_changes_a,
                    "files_b": api_changes_b
                })

        except Exception as e:
            # Skip if analysis fails
            pass

        return conflicts

    def _calculate_probability(
        self,
        overlapping_files: int,
        textual: List[Dict],
        semantic: List[Dict],
        integration: List[Dict]
    ) -> float:
        """Calculate conflict probability.

        Args:
            overlapping_files: Number of overlapping files
            textual: Textual conflicts
            semantic: Semantic conflicts
            integration: Integration conflicts

        Returns:
            Probability (0.0-1.0)
        """
        # Base probability from file overlap
        base_prob = min(overlapping_files / 10.0, 0.3)

        # Textual conflicts (high confidence)
        textual_prob = min(len(textual) / 5.0, 0.4)

        # Semantic conflicts (medium confidence)
        semantic_prob = min(len(semantic) / 3.0, 0.2)

        # Integration conflicts (lower confidence)
        integration_prob = min(len(integration) / 2.0, 0.1)

        # Combined probability
        total = base_prob + textual_prob + semantic_prob + integration_prob

        return min(total, 1.0)

    def _get_conflict_level(self, probability: float) -> str:
        """Get conflict level from probability.

        Args:
            probability: Conflict probability

        Returns:
            Level (none/low/medium/high/critical)
        """
        if probability >= self.THRESHOLDS["critical"]:
            return "critical"
        elif probability >= self.THRESHOLDS["high"]:
            return "high"
        elif probability >= self.THRESHOLDS["medium"]:
            return "medium"
        elif probability > 0:
            return "low"
        else:
            return "none"

    def _generate_suggestion(self, level: str, probability: float, branch_a: str, branch_b: str) -> str:
        """Generate merge suggestion based on conflict level.

        Args:
            level: Conflict level
            probability: Probability value
            branch_a: First branch
            branch_b: Second branch

        Returns:
            Suggestion text
        """
        if level == "critical":
            return f"⚠️ CRITICAL: High conflict risk ({probability:.0%}). Coordinate with team before merging either branch."
        elif level == "high":
            return f"⚠️ WARNING: Significant conflict risk ({probability:.0%}). Merge {branch_a} first, then rebase {branch_b}."
        elif level == "medium":
            return f"ℹ️ CAUTION: Moderate conflict risk ({probability:.0%}). Monitor merge carefully."
        elif level == "low":
            return f"✓ Low conflict risk ({probability:.0%}). Safe to merge, but review changes."
        else:
            return "✓ No conflicts detected - safe to merge."

    def _extract_line_ranges(self, diff: str) -> List[Tuple[int, int]]:
        """Extract changed line ranges from diff.

        Args:
            diff: Git diff output

        Returns:
            List of (start, end) tuples
        """
        ranges = []

        # Parse diff headers like @@ -12,5 +14,7 @@
        pattern = r'@@\s+-\d+,?\d*\s+\+(\d+),?(\d*)\s+@@'

        for match in re.finditer(pattern, diff):
            start = int(match.group(1))
            count = int(match.group(2)) if match.group(2) else 1
            end = start + count

            ranges.append((start, end))

        return ranges

    def _ranges_overlap(self, range_a: Tuple[int, int], range_b: Tuple[int, int]) -> bool:
        """Check if two line ranges overlap.

        Args:
            range_a: First (start, end) tuple
            range_b: Second (start, end) tuple

        Returns:
            True if ranges overlap
        """
        return range_a[0] <= range_b[1] and range_b[0] <= range_a[1]

    def _get_file_content(self, branch: str, file_path: str) -> Optional[str]:
        """Get file content from a specific branch.

        Args:
            branch: Branch name
            file_path: File path

        Returns:
            File content or None if failed
        """
        try:
            result = subprocess.run(
                ["git", "show", f"{branch}:{file_path}"],
                capture_output=True,
                text=True,
                check=True
            )

            return result.stdout

        except Exception:
            return None

    def _extract_functions(self, tree: ast.AST) -> Dict[str, str]:
        """Extract function signatures from AST.

        Args:
            tree: AST tree

        Returns:
            Dict mapping function name to signature
        """
        functions = {}

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # Build signature
                args = [arg.arg for arg in node.args.args]
                signature = f"{node.name}({', '.join(args)})"

                functions[node.name] = signature

        return functions

    def _get_all_branches(self) -> Dict[str, Any]:
        """Get all git branches.

        Returns:
            Dict with list of branches
        """
        try:
            result = subprocess.run(
                ["git", "branch", "--format=%(refname:short)"],
                capture_output=True,
                text=True,
                check=True
            )

            branches = [b.strip() for b in result.stdout.split('\n') if b.strip()]

            return {
                "success": True,
                "branches": branches
            }

        except subprocess.CalledProcessError as e:
            return {
                "success": False,
                "error": f"Failed to get branches: {e.stderr}"
            }


if __name__ == "__main__":
    """Demo usage of Conflict Predictor."""
    print("=== Conflict Predictor Demo ===\n")

    predictor = ConflictPredictor()

    # Check all active branches
    print("Checking all active branches for conflicts...\n")

    matrix = predictor.check_all_branches()

    if matrix["success"]:
        print(f"✓ Conflict Analysis Complete\n")

        if "message" in matrix:
            # Not enough branches
            print(f"{matrix['message']}")
            if "branches" in matrix:
                print(f"Active branches: {', '.join(matrix['branches']) if matrix['branches'] else 'none'}")
        else:
            # Full analysis
            print(f"Total Branches: {matrix['total_branches']}")
            print(f"Pairs Checked: {matrix['total_pairs_checked']}")
            print(f"Conflicts Detected: {matrix['conflicts_detected']}")
            print()
            print("By Severity:")
            print(f"  Critical: {matrix['critical_count']}")
            print(f"  High: {matrix['high_count']}")
            print(f"  Medium: {matrix['medium_count']}")
            print()

            if matrix['conflicts']:
                print("Top Conflict Risks:")
                for conflict in matrix['conflicts'][:5]:
                    print(f"  [{conflict['level'].upper()}] {conflict['branch_a']} ↔ {conflict['branch_b']}")
                    print(f"    Probability: {conflict['probability']:.0%}")
            else:
                print("No conflicts detected - all branches safe to merge! ✓")
    else:
        print(f"✗ Analysis failed: {matrix.get('error')}")
