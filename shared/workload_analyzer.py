"""
Workload Analyzer

Tracks and balances developer workload across the team.
Identifies bottlenecks and suggests task redistribution.

Metrics Tracked:
    1. Active Tasks: Branches, uncommitted changes, open PRs
    2. Task Complexity: Lines changed, files touched, subsystems
    3. Time Metrics: Commit frequency, PR review time
    4. Cognitive Load: Context switches, dependency complexity

Workload Score:
    0.0-0.4: Light load (available for new tasks)
    0.4-0.6: Normal load (comfortable)
    0.6-0.8: Busy (close to capacity)
    0.8-1.0: Overloaded (need help)

Usage:
    from shared.workload_analyzer import WorkloadAnalyzer

    analyzer = WorkloadAnalyzer()

    # Get developer workload
    result = analyzer.analyze_developer("developer@example.com")
    print(f"Workload Score: {result['score']:.2f}")
    print(f"Level: {result['level']}")

    # Get team overview
    team = analyzer.analyze_team()
    print(f"Overloaded: {team['overloaded_count']}")
"""

import os
import subprocess
import sqlite3
from typing import Dict, Any, List, Set
from pathlib import Path
from datetime import datetime, timedelta
import re


class WorkloadAnalyzer:
    """Analyzes and balances developer workload."""

    # Workload level thresholds
    LEVELS = {
        "overloaded": 0.8,
        "busy": 0.6,
        "available": 0.4,
        "light": 0.0
    }

    # Weights for workload calculation
    WEIGHTS = {
        "active_branches": 0.15,
        "open_prs": 0.15,
        "lines_changed": 0.20,
        "files_changed": 0.15,
        "subsystems": 0.15,
        "context_switches": 0.20
    }

    def __init__(self, db_path: str = "memory/workload.db"):
        """Initialize workload analyzer.

        Args:
            db_path: Path to SQLite database for workload tracking
        """
        self.db_path = db_path
        self._ensure_database()

    def _ensure_database(self):
        """Create database tables if they don't exist."""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Developer workload table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS developer_workload (
                developer TEXT PRIMARY KEY,
                score REAL NOT NULL,
                level TEXT NOT NULL,
                active_branches INTEGER DEFAULT 0,
                open_prs INTEGER DEFAULT 0,
                uncommitted_lines INTEGER DEFAULT 0,
                total_lines_changed INTEGER DEFAULT 0,
                total_files_changed INTEGER DEFAULT 0,
                subsystems_touched INTEGER DEFAULT 0,
                context_switches_today INTEGER DEFAULT 0,
                last_commit TEXT,
                last_updated TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Context switch log
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS context_switches (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                developer TEXT NOT NULL,
                from_subsystem TEXT,
                to_subsystem TEXT,
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        conn.commit()
        conn.close()

    def analyze_developer(self, developer: str) -> Dict[str, Any]:
        """Analyze workload for a specific developer.

        Args:
            developer: Developer email or identifier

        Returns:
            Dict with workload analysis
        """
        try:
            # Get active branches
            branches = self._get_active_branches(developer)

            # Get open PRs (would integrate with GitHub API in production)
            open_prs = self._get_open_prs(developer)

            # Get uncommitted changes
            uncommitted = self._get_uncommitted_changes(developer)

            # Calculate complexity
            total_lines = sum(self._get_lines_changed(b) for b in branches)
            total_files = sum(self._get_files_changed(b) for b in branches)
            subsystems = len(self._get_subsystems_touched(branches))

            # Get cognitive load
            context_switches = self._get_context_switches_today(developer)

            # Calculate workload score
            score = self._calculate_score(
                active_branches=len(branches),
                open_prs=len(open_prs),
                lines_changed=total_lines,
                files_changed=total_files,
                subsystems=subsystems,
                context_switches=context_switches
            )

            # Determine level
            level = self._get_workload_level(score)

            # Get last commit time
            last_commit = self._get_last_commit_time(developer)

            # Update database
            self._update_database(
                developer=developer,
                score=score,
                level=level,
                active_branches=len(branches),
                open_prs=len(open_prs),
                uncommitted_lines=len(uncommitted),
                total_lines_changed=total_lines,
                total_files_changed=total_files,
                subsystems_touched=subsystems,
                context_switches_today=context_switches,
                last_commit=last_commit
            )

            return {
                "success": True,
                "developer": developer,
                "score": score,
                "level": level,
                "metrics": {
                    "active_branches": len(branches),
                    "open_prs": len(open_prs),
                    "uncommitted_lines": len(uncommitted),
                    "total_lines_changed": total_lines,
                    "total_files_changed": total_files,
                    "subsystems_touched": subsystems,
                    "context_switches_today": context_switches
                },
                "branches": branches[:5],  # First 5
                "last_commit": last_commit,
                "recommendation": self._generate_recommendation(level, score)
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Workload analysis failed: {str(e)}"
            }

    def analyze_team(self) -> Dict[str, Any]:
        """Analyze workload for entire team.

        Returns:
            Dict with team-wide workload analysis
        """
        try:
            # Get all developers who have committed recently
            developers = self._get_active_developers(days=30)

            # Analyze each developer
            results = []
            for dev in developers:
                analysis = self.analyze_developer(dev)
                if analysis["success"]:
                    results.append(analysis)

            # Sort by score
            results.sort(key=lambda x: x["score"], reverse=True)

            # Count by level
            overloaded = [r for r in results if r["level"] == "overloaded"]
            busy = [r for r in results if r["level"] == "busy"]
            available = [r for r in results if r["level"] == "available"]
            light = [r for r in results if r["level"] == "light"]

            # Calculate team average
            avg_score = sum(r["score"] for r in results) / len(results) if results else 0

            # Identify bottlenecks
            bottlenecks = self._identify_bottlenecks(results)

            return {
                "success": True,
                "total_developers": len(results),
                "average_score": avg_score,
                "overloaded_count": len(overloaded),
                "busy_count": len(busy),
                "available_count": len(available),
                "light_count": len(light),
                "developers": results,
                "bottlenecks": bottlenecks,
                "recommendations": self._generate_team_recommendations(results)
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Team analysis failed: {str(e)}"
            }

    def _calculate_score(
        self,
        active_branches: int,
        open_prs: int,
        lines_changed: int,
        files_changed: int,
        subsystems: int,
        context_switches: int
    ) -> float:
        """Calculate workload score (0.0-1.0).

        Args:
            active_branches: Number of active branches
            open_prs: Number of open PRs
            lines_changed: Total lines changed
            files_changed: Total files changed
            subsystems: Number of subsystems touched
            context_switches: Context switches today

        Returns:
            Workload score
        """
        score = (
            active_branches * self.WEIGHTS["active_branches"] +
            open_prs * self.WEIGHTS["open_prs"] +
            (lines_changed / 1000) * self.WEIGHTS["lines_changed"] +
            (files_changed / 50) * self.WEIGHTS["files_changed"] +
            subsystems * self.WEIGHTS["subsystems"] +
            (context_switches / 10) * self.WEIGHTS["context_switches"]
        )

        return min(score, 1.0)

    def _get_workload_level(self, score: float) -> str:
        """Get workload level from score.

        Args:
            score: Workload score

        Returns:
            Level (overloaded/busy/available/light)
        """
        if score >= self.LEVELS["overloaded"]:
            return "overloaded"
        elif score >= self.LEVELS["busy"]:
            return "busy"
        elif score >= self.LEVELS["available"]:
            return "available"
        else:
            return "light"

    def _get_active_branches(self, developer: str) -> List[str]:
        """Get active branches for a developer.

        Args:
            developer: Developer identifier

        Returns:
            List of branch names
        """
        try:
            # Get all branches
            result = subprocess.run(
                ["git", "branch", "--format=%(refname:short)"],
                capture_output=True,
                text=True,
                check=True
            )

            all_branches = [b.strip() for b in result.stdout.split('\n') if b.strip()]

            # Filter branches by author (last commit)
            developer_branches = []

            for branch in all_branches:
                if branch == "main" or branch.startswith("HEAD"):
                    continue

                try:
                    author_result = subprocess.run(
                        ["git", "log", "-1", "--format=%ae", branch],
                        capture_output=True,
                        text=True,
                        check=True
                    )

                    author = author_result.stdout.strip()

                    if developer.lower() in author.lower():
                        developer_branches.append(branch)

                except Exception:
                    continue

            return developer_branches

        except Exception:
            return []

    def _get_open_prs(self, developer: str) -> List[Dict[str, Any]]:
        """Get open PRs for a developer.

        Args:
            developer: Developer identifier

        Returns:
            List of PR details (simplified - would use GitHub API in production)
        """
        # Placeholder - would integrate with GitHub API
        # For demo, estimate from branches
        branches = self._get_active_branches(developer)
        return [{"branch": b, "status": "open"} for b in branches if "feature/" in b or "fix/" in b]

    def _get_uncommitted_changes(self, developer: str) -> List[str]:
        """Get uncommitted changes.

        Args:
            developer: Developer identifier

        Returns:
            List of uncommitted file paths
        """
        try:
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                capture_output=True,
                text=True
            )

            # Parse output
            uncommitted = []
            for line in result.stdout.split('\n'):
                if line.strip():
                    # Format: "M  file.py" or "?? file.py"
                    parts = line.strip().split(None, 1)
                    if len(parts) == 2:
                        uncommitted.append(parts[1])

            return uncommitted

        except Exception:
            return []

    def _get_lines_changed(self, branch: str) -> int:
        """Get lines changed in a branch.

        Args:
            branch: Branch name

        Returns:
            Number of lines changed
        """
        try:
            result = subprocess.run(
                ["git", "diff", "--shortstat", f"main...{branch}"],
                capture_output=True,
                text=True
            )

            # Parse output: "3 files changed, 150 insertions(+), 50 deletions(-)"
            match = re.search(r'(\d+) insertion', result.stdout)
            insertions = int(match.group(1)) if match else 0

            match = re.search(r'(\d+) deletion', result.stdout)
            deletions = int(match.group(1)) if match else 0

            return insertions + deletions

        except Exception:
            return 0

    def _get_files_changed(self, branch: str) -> int:
        """Get files changed in a branch.

        Args:
            branch: Branch name

        Returns:
            Number of files changed
        """
        try:
            result = subprocess.run(
                ["git", "diff", "--name-only", f"main...{branch}"],
                capture_output=True,
                text=True
            )

            files = [f for f in result.stdout.split('\n') if f.strip()]
            return len(files)

        except Exception:
            return 0

    def _get_subsystems_touched(self, branches: List[str]) -> Set[str]:
        """Get subsystems touched across branches.

        Args:
            branches: List of branch names

        Returns:
            Set of subsystem names
        """
        subsystems = set()

        for branch in branches:
            try:
                result = subprocess.run(
                    ["git", "diff", "--name-only", f"main...{branch}"],
                    capture_output=True,
                    text=True
                )

                for file_path in result.stdout.split('\n'):
                    if file_path.strip():
                        # Extract subsystem from path
                        parts = Path(file_path).parts
                        if len(parts) > 0:
                            subsystems.add(parts[0])

            except Exception:
                continue

        return subsystems

    def _get_context_switches_today(self, developer: str) -> int:
        """Get context switches for developer today.

        Args:
            developer: Developer identifier

        Returns:
            Number of context switches
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            today = datetime.utcnow().date().isoformat()

            cursor.execute("""
                SELECT COUNT(*)
                FROM context_switches
                WHERE developer = ? AND DATE(timestamp) = ?
            """, (developer, today))

            count = cursor.fetchone()[0]
            conn.close()

            return count

        except Exception:
            return 0

    def _get_last_commit_time(self, developer: str) -> str:
        """Get last commit time for developer.

        Args:
            developer: Developer identifier

        Returns:
            ISO timestamp or "Never"
        """
        try:
            result = subprocess.run(
                ["git", "log", "--author", developer, "-1", "--format=%aI"],
                capture_output=True,
                text=True
            )

            timestamp = result.stdout.strip()
            return timestamp if timestamp else "Never"

        except Exception:
            return "Never"

    def _get_active_developers(self, days: int = 30) -> List[str]:
        """Get developers who committed in the last N days.

        Args:
            days: Number of days to look back

        Returns:
            List of developer emails
        """
        try:
            cutoff = (datetime.utcnow() - timedelta(days=days)).isoformat()

            result = subprocess.run(
                ["git", "log", f"--since={cutoff}", "--format=%ae"],
                capture_output=True,
                text=True
            )

            developers = list(set([
                email.strip()
                for email in result.stdout.split('\n')
                if email.strip()
            ]))

            return developers

        except Exception:
            return []

    def _identify_bottlenecks(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Identify bottlenecks in team.

        Args:
            results: List of developer analyses

        Returns:
            List of bottleneck descriptions
        """
        bottlenecks = []

        # Overloaded developers
        overloaded = [r for r in results if r["level"] == "overloaded"]

        for dev in overloaded:
            bottlenecks.append({
                "type": "overloaded_developer",
                "developer": dev["developer"],
                "score": dev["score"],
                "suggestion": f"Reassign tasks from {dev['developer']} (score: {dev['score']:.2f})"
            })

        # Subsystem concentration would be tracked here
        # (requires additional branch analysis)

        return bottlenecks

    def _generate_recommendation(self, level: str, score: float) -> str:
        """Generate recommendation based on workload level.

        Args:
            level: Workload level
            score: Workload score

        Returns:
            Recommendation text
        """
        if level == "overloaded":
            return f"⚠️ OVERLOADED ({score:.2f}): Consider reassigning tasks or extending deadlines"
        elif level == "busy":
            return f"⚠️ BUSY ({score:.2f}): At capacity - avoid new tasks"
        elif level == "available":
            return f"✓ AVAILABLE ({score:.2f}): Can take new tasks"
        else:
            return f"✓ LIGHT ({score:.2f}): Actively looking for work"

    def _generate_team_recommendations(self, results: List[Dict[str, Any]]) -> List[str]:
        """Generate team-wide recommendations.

        Args:
            results: List of developer analyses

        Returns:
            List of recommendations
        """
        recommendations = []

        overloaded = [r for r in results if r["level"] == "overloaded"]
        available = [r for r in results if r["level"] in ["available", "light"]]

        if overloaded and available:
            for overloaded_dev in overloaded:
                for available_dev in available:
                    recommendations.append(
                        f"Consider reassigning tasks from {overloaded_dev['developer']} "
                        f"({overloaded_dev['score']:.2f}) to {available_dev['developer']} "
                        f"({available_dev['score']:.2f})"
                    )

        if not available:
            recommendations.append("⚠️ No developers available - team at capacity")

        if len(results) > 0:
            avg_score = sum(r["score"] for r in results) / len(results)
            if avg_score > 0.7:
                recommendations.append("⚠️ Team average workload high (0.7+) - consider hiring or reducing scope")

        return recommendations[:5]  # Top 5

    def _update_database(self, **kwargs):
        """Update database with developer workload."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("""
                INSERT OR REPLACE INTO developer_workload
                (developer, score, level, active_branches, open_prs, uncommitted_lines,
                 total_lines_changed, total_files_changed, subsystems_touched,
                 context_switches_today, last_commit, last_updated)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                kwargs["developer"],
                kwargs["score"],
                kwargs["level"],
                kwargs["active_branches"],
                kwargs["open_prs"],
                kwargs["uncommitted_lines"],
                kwargs["total_lines_changed"],
                kwargs["total_files_changed"],
                kwargs["subsystems_touched"],
                kwargs["context_switches_today"],
                kwargs["last_commit"],
                datetime.utcnow().isoformat()
            ))

            conn.commit()
            conn.close()

        except Exception as e:
            print(f"Warning: Failed to update database: {e}")


if __name__ == "__main__":
    """Demo usage of Workload Analyzer."""
    print("=== Workload Analyzer Demo ===\n")

    analyzer = WorkloadAnalyzer()

    # Analyze team
    print("Analyzing team workload...\n")

    team = analyzer.analyze_team()

    if team["success"]:
        print(f"✓ Team Analysis Complete\n")
        print(f"Total Developers: {team['total_developers']}")
        print(f"Average Workload: {team['average_score']:.2f}")
        print()
        print("By Level:")
        print(f"  Overloaded: {team['overloaded_count']}")
        print(f"  Busy: {team['busy_count']}")
        print(f"  Available: {team['available_count']}")
        print(f"  Light: {team['light_count']}")
        print()

        if team['developers']:
            print("Developer Workloads:")
            for dev in team['developers'][:5]:
                bar_length = int(dev['score'] * 10)
                bar = "█" * bar_length + "░" * (10 - bar_length)
                print(f"  {dev['developer']}: {bar} {dev['score']:.2f} ({dev['level'].upper()})")
            print()

        if team['recommendations']:
            print("Recommendations:")
            for rec in team['recommendations']:
                print(f"  • {rec}")
    else:
        print(f"✗ Analysis failed: {team.get('error')}")
