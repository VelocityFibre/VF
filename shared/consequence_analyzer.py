"""
Consequence Awareness Analyzer

Predicts real-world impact of code changes on users, APIs, databases, and performance.
This is the intelligence layer that answers "What happens if we deploy this?"

Architecture:
    Git Commit → Extract Changes → Analyze Impact → Calculate Blast Radius → Recommendations

Impact Categories:
    1. API Impact: Breaking changes, endpoint modifications
    2. Database Impact: Schema changes, migration risks
    3. Performance Impact: Expensive operations, N+1 queries
    4. User Impact: How many users affected, UX changes

Usage:
    from shared.consequence_analyzer import ConsequenceAnalyzer

    analyzer = ConsequenceAnalyzer()
    result = analyzer.analyze_commit(commit_hash="abc123")

    print(f"Overall Impact: {result['overall_impact']}")
    print(f"Blast Radius: {result['blast_radius']['affected_users']}")
    print(f"Recommendations: {result['recommendations']}")
"""

import os
import re
import ast
import subprocess
from typing import Dict, Any, List, Set
from pathlib import Path
from datetime import datetime


class ConsequenceAnalyzer:
    """Analyzes code changes to predict real-world consequences."""

    def __init__(self):
        """Initialize consequence analyzer."""
        self.project_root = Path(os.getcwd())

    def analyze_commit(self, commit_hash: str = "HEAD") -> Dict[str, Any]:
        """Analyze a commit for real-world impact.

        Args:
            commit_hash: Git commit hash to analyze (default: HEAD)

        Returns:
            Dict with impact analysis and recommendations
        """
        try:
            # Get commit details
            commit_info = self._get_commit_info(commit_hash)

            if not commit_info["success"]:
                return {
                    "success": False,
                    "error": commit_info.get("error")
                }

            # Analyze each impact category
            api_impact = self._analyze_api_impact(
                files_changed=commit_info["files_changed"],
                diff=commit_info["diff"]
            )

            db_impact = self._analyze_database_impact(
                files_changed=commit_info["files_changed"],
                diff=commit_info["diff"]
            )

            perf_impact = self._analyze_performance_impact(
                files_changed=commit_info["files_changed"],
                diff=commit_info["diff"]
            )

            user_impact = self._analyze_user_impact(
                files_changed=commit_info["files_changed"],
                diff=commit_info["diff"]
            )

            # Calculate overall impact
            overall_impact = self._calculate_overall_impact({
                "api": api_impact,
                "database": db_impact,
                "performance": perf_impact,
                "user": user_impact
            })

            # Calculate blast radius
            blast_radius = self._calculate_blast_radius(
                files_changed=commit_info["files_changed"],
                api_impact=api_impact,
                user_impact=user_impact
            )

            # Generate recommendations
            recommendations = self._generate_recommendations(
                overall_impact=overall_impact,
                categories={
                    "api": api_impact,
                    "database": db_impact,
                    "performance": perf_impact,
                    "user": user_impact
                }
            )

            return {
                "success": True,
                "commit_hash": commit_hash,
                "commit_message": commit_info["message"],
                "files_changed": len(commit_info["files_changed"]),
                "overall_impact": overall_impact,
                "categories": {
                    "api": api_impact,
                    "database": db_impact,
                    "performance": perf_impact,
                    "user": user_impact
                },
                "blast_radius": blast_radius,
                "recommendations": recommendations,
                "deployment_risk": self._assess_deployment_risk(overall_impact)
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Consequence analysis failed: {str(e)}"
            }

    def _analyze_api_impact(self, files_changed: List[str], diff: str) -> Dict[str, Any]:
        """Analyze impact on public APIs.

        Args:
            files_changed: List of modified files
            diff: Full git diff

        Returns:
            Dict with API impact analysis
        """
        impacts = []
        level = "none"

        # Check for API-related files
        api_files = [f for f in files_changed if any(
            pattern in f for pattern in [
                "api.py", "endpoints", "routes", "views",
                "agent.py", "tools", "orchestrator"
            ]
        )]

        if not api_files:
            return {
                "level": "none",
                "reason": "No API files modified",
                "impacts": []
            }

        # Analyze diff for API changes
        for file_path in api_files:
            # Check for removed endpoints
            removed_endpoints = re.findall(
                r'^-\s*(?:@app\.(?:get|post|put|delete)\(["\']([^"\']+))',
                diff,
                re.MULTILINE
            )

            if removed_endpoints:
                impacts.append({
                    "type": "endpoint_removed",
                    "file": file_path,
                    "endpoints": removed_endpoints,
                    "severity": "critical"
                })
                level = "critical"

            # Check for modified tool signatures (BaseAgent tools)
            if "agent.py" in file_path:
                # Look for define_tools() changes
                if "define_tools" in diff:
                    # Check if tool names or parameters changed
                    modified_tools = re.findall(
                        r'"name":\s*"([^"]+)"',
                        diff
                    )

                    if modified_tools:
                        impacts.append({
                            "type": "tool_signature_changed",
                            "file": file_path,
                            "tools": list(set(modified_tools)),
                            "severity": "high"
                        })

                        if level not in ["critical"]:
                            level = "high"

            # Check for added endpoints (positive change)
            added_endpoints = re.findall(
                r'^\+\s*(?:@app\.(?:get|post|put|delete)\(["\']([^"\']+))',
                diff,
                re.MULTILINE
            )

            if added_endpoints:
                impacts.append({
                    "type": "endpoint_added",
                    "file": file_path,
                    "endpoints": added_endpoints,
                    "severity": "low"
                })

                if level == "none":
                    level = "low"

        # Determine overall API impact level
        if not impacts:
            level = "none"
            reason = "API files modified but no breaking changes detected"
        elif level == "critical":
            reason = "Endpoints removed or breaking changes"
        elif level == "high":
            reason = "Tool signatures or parameters modified"
        elif level == "low":
            reason = "New endpoints or tools added"
        else:
            reason = "Minor API modifications"

        return {
            "level": level,
            "reason": reason,
            "impacts": impacts,
            "files_affected": len(api_files)
        }

    def _analyze_database_impact(self, files_changed: List[str], diff: str) -> Dict[str, Any]:
        """Analyze impact on database schema and queries.

        Args:
            files_changed: List of modified files
            diff: Full git diff

        Returns:
            Dict with database impact analysis
        """
        impacts = []
        level = "none"

        # Check for database-related files
        db_files = [f for f in files_changed if any(
            pattern in f for pattern in [
                "migration", "schema", "model", "database",
                "neon_agent", "convex", "postgres"
            ]
        )]

        if not db_files:
            return {
                "level": "none",
                "reason": "No database files modified",
                "impacts": []
            }

        # Check for schema changes
        schema_patterns = [
            r'CREATE TABLE',
            r'ALTER TABLE',
            r'DROP TABLE',
            r'ADD COLUMN',
            r'DROP COLUMN',
            r'RENAME COLUMN'
        ]

        for pattern in schema_patterns:
            matches = re.findall(
                f'^[+].*{pattern}',
                diff,
                re.MULTILINE | re.IGNORECASE
            )

            if matches:
                impacts.append({
                    "type": "schema_change",
                    "operation": pattern,
                    "severity": "high" if "DROP" in pattern else "medium",
                    "matches": len(matches)
                })

                if "DROP" in pattern:
                    level = "high"
                elif level not in ["high"]:
                    level = "medium"

        # Check for migration files
        migration_files = [f for f in files_changed if "migration" in f]

        if migration_files:
            impacts.append({
                "type": "migration_added",
                "files": migration_files,
                "severity": "medium"
            })

            if level == "none":
                level = "medium"

        # Check for connection string changes
        if "DATABASE_URL" in diff or "NEON_DATABASE_URL" in diff:
            impacts.append({
                "type": "connection_change",
                "severity": "critical"
            })
            level = "critical"

        # Determine reason
        if not impacts:
            reason = "Database files modified but no schema changes"
            level = "low"
        elif level == "critical":
            reason = "Database connection or critical schema changes"
        elif level == "high":
            reason = "Destructive schema operations detected"
        elif level == "medium":
            reason = "Schema modifications or migrations"
        else:
            reason = "Minor database updates"

        return {
            "level": level,
            "reason": reason,
            "impacts": impacts,
            "files_affected": len(db_files)
        }

    def _analyze_performance_impact(self, files_changed: List[str], diff: str) -> Dict[str, Any]:
        """Analyze performance impact of changes.

        Args:
            files_changed: List of modified files
            diff: Full git diff

        Returns:
            Dict with performance impact analysis
        """
        impacts = []
        level = "none"

        # Performance anti-patterns
        antipatterns = [
            {
                "name": "N+1 Query",
                "pattern": r'for .* in .*:\s+.*execute\(',
                "severity": "high"
            },
            {
                "name": "Missing Pagination",
                "pattern": r'SELECT \* FROM .* WHERE',
                "severity": "medium"
            },
            {
                "name": "Synchronous Sleep",
                "pattern": r'time\.sleep\(',
                "severity": "low"
            },
            {
                "name": "Large File Operations",
                "pattern": r'\.read\(\)|\.readlines\(\)',
                "severity": "medium"
            }
        ]

        for antipattern in antipatterns:
            matches = re.findall(
                f'^[+].*{antipattern["pattern"]}',
                diff,
                re.MULTILINE
            )

            if matches:
                impacts.append({
                    "type": "antipattern",
                    "name": antipattern["name"],
                    "severity": antipattern["severity"],
                    "occurrences": len(matches)
                })

                # Update level
                if antipattern["severity"] == "high" and level not in ["critical"]:
                    level = "high"
                elif antipattern["severity"] == "medium" and level not in ["critical", "high"]:
                    level = "medium"
                elif antipattern["severity"] == "low" and level == "none":
                    level = "low"

        # Check for expensive operations
        expensive_ops = [
            r'\.sort\(',
            r'json\.loads\(',
            r'pickle\.loads\(',
            r'hashlib\.',
        ]

        expensive_count = 0

        for op in expensive_ops:
            matches = re.findall(f'^[+].*{op}', diff, re.MULTILINE)
            expensive_count += len(matches)

        if expensive_count > 10:
            impacts.append({
                "type": "expensive_operations",
                "count": expensive_count,
                "severity": "medium"
            })

            if level not in ["critical", "high"]:
                level = "medium"

        # Check for added async operations (positive)
        async_patterns = [
            r'async def',
            r'await ',
            r'asyncio\.'
        ]

        async_count = 0

        for pattern in async_patterns:
            matches = re.findall(f'^[+].*{pattern}', diff, re.MULTILINE)
            async_count += len(matches)

        if async_count > 0:
            impacts.append({
                "type": "async_operations_added",
                "count": async_count,
                "severity": "none",  # Positive change
                "note": "Async operations improve performance"
            })

        # Determine reason
        if not impacts:
            reason = "No significant performance impact detected"
        elif level == "high":
            reason = "Performance anti-patterns detected (N+1 queries, etc.)"
        elif level == "medium":
            reason = "Potentially expensive operations added"
        elif level == "low":
            reason = "Minor performance considerations"
        else:
            reason = "Performance-neutral changes"

        return {
            "level": level,
            "reason": reason,
            "impacts": impacts,
            "async_operations": async_count
        }

    def _analyze_user_impact(self, files_changed: List[str], diff: str) -> Dict[str, Any]:
        """Analyze impact on end users.

        Args:
            files_changed: List of modified files
            diff: Full git diff

        Returns:
            Dict with user impact analysis
        """
        impacts = []
        level = "none"

        # Check for UI/UX files
        ui_files = [f for f in files_changed if any(
            pattern in f for pattern in [
                ".html", ".css", ".js", "ui-module",
                "chat", "interface"
            ]
        )]

        if ui_files:
            impacts.append({
                "type": "ui_change",
                "files": ui_files,
                "severity": "medium"
            })
            level = "medium"

        # Check for error message changes
        error_changes = re.findall(
            r'^[-+].*(?:raise |error|Error\(|Exception\()',
            diff,
            re.MULTILINE
        )

        if error_changes:
            impacts.append({
                "type": "error_handling_changed",
                "changes": len(error_changes),
                "severity": "low"
            })

            if level == "none":
                level = "low"

        # Check for configuration changes
        config_files = [f for f in files_changed if any(
            pattern in f for pattern in [
                ".env", "config", "settings"
            ]
        )]

        if config_files:
            impacts.append({
                "type": "configuration_change",
                "files": config_files,
                "severity": "high"
            })

            if level not in ["critical"]:
                level = "high"

        # Estimate affected users
        affected_users = "unknown"

        if level == "critical":
            affected_users = "100% (all users)"
        elif level == "high":
            affected_users = "~75% (most users)"
        elif level == "medium":
            affected_users = "~50% (some users)"
        elif level == "low":
            affected_users = "~25% (few users)"
        else:
            affected_users = "0% (no user-facing changes)"

        # Determine reason
        if not impacts:
            reason = "No user-facing changes"
        elif level == "high":
            reason = "Configuration or critical UI changes"
        elif level == "medium":
            reason = "UI/UX modifications"
        elif level == "low":
            reason = "Minor user-visible changes"
        else:
            reason = "Internal changes only"

        return {
            "level": level,
            "reason": reason,
            "impacts": impacts,
            "affected_users": affected_users
        }

    def _calculate_overall_impact(self, categories: Dict[str, Dict[str, Any]]) -> str:
        """Calculate overall impact level from category analysis.

        Args:
            categories: Dict of category analyses

        Returns:
            Overall impact level (none/low/medium/high/critical)
        """
        levels = [cat["level"] for cat in categories.values()]

        # Priority order
        if "critical" in levels:
            return "critical"
        elif "high" in levels:
            return "high"
        elif "medium" in levels:
            return "medium"
        elif "low" in levels:
            return "low"
        else:
            return "none"

    def _calculate_blast_radius(
        self,
        files_changed: List[str],
        api_impact: Dict[str, Any],
        user_impact: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Calculate blast radius of changes.

        Args:
            files_changed: List of modified files
            api_impact: API impact analysis
            user_impact: User impact analysis

        Returns:
            Dict with blast radius metrics
        """
        # Count affected components
        affected_agents = len([f for f in files_changed if "agents/" in f])
        affected_shared = len([f for f in files_changed if "shared/" in f])
        affected_orchestrator = len([f for f in files_changed if "orchestrator/" in f])

        # Estimate endpoints affected
        endpoints_affected = 0

        for impact in api_impact.get("impacts", []):
            if impact["type"] in ["endpoint_removed", "endpoint_added", "tool_signature_changed"]:
                endpoints_affected += len(impact.get("endpoints", impact.get("tools", [])))

        return {
            "affected_files": len(files_changed),
            "affected_agents": affected_agents,
            "affected_shared_modules": affected_shared,
            "affected_orchestrator": affected_orchestrator > 0,
            "affected_endpoints": endpoints_affected,
            "affected_users": user_impact["affected_users"],
            "blast_radius_score": self._calculate_blast_radius_score(
                files=len(files_changed),
                agents=affected_agents,
                endpoints=endpoints_affected
            )
        }

    def _calculate_blast_radius_score(self, files: int, agents: int, endpoints: int) -> str:
        """Calculate blast radius score.

        Args:
            files: Number of files changed
            agents: Number of agents affected
            endpoints: Number of endpoints affected

        Returns:
            Blast radius category (small/medium/large/critical)
        """
        score = files + (agents * 3) + (endpoints * 5)

        if score < 5:
            return "small"
        elif score < 15:
            return "medium"
        elif score < 30:
            return "large"
        else:
            return "critical"

    def _generate_recommendations(
        self,
        overall_impact: str,
        categories: Dict[str, Dict[str, Any]]
    ) -> List[str]:
        """Generate deployment recommendations.

        Args:
            overall_impact: Overall impact level
            categories: Category analyses

        Returns:
            List of recommendations
        """
        recommendations = []

        # Impact-based recommendations
        if overall_impact == "critical":
            recommendations.append("⚠️ CRITICAL: Coordinate deployment with team lead")
            recommendations.append("Schedule deployment during maintenance window")
            recommendations.append("Prepare rollback plan before deployment")

        elif overall_impact == "high":
            recommendations.append("Deploy during low-traffic period")
            recommendations.append("Monitor error rates for 24h post-deployment")

        elif overall_impact == "medium":
            recommendations.append("Standard deployment process")
            recommendations.append("Monitor metrics for 1-2 hours post-deployment")

        # Category-specific recommendations
        if categories["api"]["level"] in ["high", "critical"]:
            recommendations.append("Notify API consumers of breaking changes")
            recommendations.append("Update API documentation")

        if categories["database"]["level"] in ["high", "critical"]:
            recommendations.append("Test migrations on staging environment first")
            recommendations.append("Backup database before deployment")

        if categories["performance"]["level"] in ["high", "critical"]:
            recommendations.append("Run performance benchmarks before deployment")
            recommendations.append("Monitor response times closely")

        if categories["user"]["level"] in ["high", "critical"]:
            recommendations.append("Notify users of upcoming changes")
            recommendations.append("Prepare user communication/documentation")

        # Default recommendation
        if not recommendations:
            recommendations.append("Standard deployment - no special precautions needed")

        return recommendations

    def _assess_deployment_risk(self, overall_impact: str) -> str:
        """Assess deployment risk level.

        Args:
            overall_impact: Overall impact level

        Returns:
            Risk assessment (very_low/low/medium/high/very_high)
        """
        risk_mapping = {
            "none": "very_low",
            "low": "low",
            "medium": "medium",
            "high": "high",
            "critical": "very_high"
        }

        return risk_mapping.get(overall_impact, "medium")

    def _get_commit_info(self, commit_hash: str) -> Dict[str, Any]:
        """Get commit information including diff.

        Args:
            commit_hash: Git commit hash

        Returns:
            Dict with commit details
        """
        try:
            # Get commit message
            message = subprocess.check_output(
                ["git", "log", "-1", "--pretty=%B", commit_hash],
                text=True
            ).strip()

            # Get files changed
            files = subprocess.check_output(
                ["git", "diff-tree", "--no-commit-id", "--name-only", "-r", commit_hash],
                text=True
            ).strip().split('\n')

            # Get full diff
            diff = subprocess.check_output(
                ["git", "show", commit_hash],
                text=True
            )

            return {
                "success": True,
                "hash": commit_hash,
                "message": message,
                "files_changed": [f for f in files if f],
                "diff": diff
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to get commit info: {str(e)}"
            }


if __name__ == "__main__":
    """Demo usage of Consequence Analyzer."""
    print("=== Consequence Awareness Analyzer Demo ===\n")

    analyzer = ConsequenceAnalyzer()

    # Analyze latest commit
    print("Analyzing latest commit for real-world impact...\n")

    result = analyzer.analyze_commit()

    if result["success"]:
        print(f"✓ Consequence Analysis Complete\n")
        print(f"Commit: {result['commit_hash'][:7]}")
        print(f"Message: {result['commit_message'][:60]}...")
        print(f"Files Changed: {result['files_changed']}")
        print()
        print(f"Overall Impact: {result['overall_impact'].upper()}")
        print(f"Deployment Risk: {result['deployment_risk'].upper()}")
        print()
        print("Impact by Category:")
        for category, analysis in result["categories"].items():
            print(f"  {category.capitalize()}: {analysis['level'].upper()}")
            print(f"    {analysis['reason']}")
        print()
        print("Blast Radius:")
        blast = result["blast_radius"]
        print(f"  Files: {blast['affected_files']}")
        print(f"  Agents: {blast['affected_agents']}")
        print(f"  Endpoints: {blast['affected_endpoints']}")
        print(f"  Users: {blast['affected_users']}")
        print(f"  Score: {blast['blast_radius_score']}")
        print()
        print("Recommendations:")
        for i, rec in enumerate(result["recommendations"], 1):
            print(f"  {i}. {rec}")
    else:
        print(f"✗ Analysis failed: {result['error']}")
