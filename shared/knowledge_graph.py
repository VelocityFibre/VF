"""
Knowledge Graph

Maps developer expertise across the codebase to optimize code reviews and identify knowledge silos.

Graph Structure:
    Developer → (commits, lines) → File → (part_of) → Subsystem → Expertise Score

Capabilities:
    1. Track which developers modified which files
    2. Calculate expertise scores (0.0-1.0) per subsystem
    3. Suggest optimal reviewers based on expertise + availability
    4. Identify knowledge silos (single expert risk)
    5. Suggest pairing opportunities for knowledge transfer

Usage:
    from shared.knowledge_graph import KnowledgeGraph

    graph = KnowledgeGraph()

    # Calculate expertise
    expertise = graph.calculate_expertise("dev@example.com", "agents/neon-database")
    print(f"Expertise: {expertise:.2f}")

    # Suggest reviewers
    reviewers = graph.suggest_reviewers(["agents/neon-database/agent.py"])
    print(f"Best reviewers: {[r['developer'] for r in reviewers]}")

    # Detect knowledge silos
    silos = graph.detect_knowledge_silos()
    print(f"High-risk silos: {len(silos)}")
"""

import os
import subprocess
import sqlite3
from typing import Dict, Any, List, Set, Tuple
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict


class KnowledgeGraph:
    """Maps developer expertise across the codebase."""

    # Expertise score weights
    WEIGHTS = {
        "contribution": 0.5,  # Commit percentage
        "recency": 0.3,       # Recent activity
        "diversity": 0.2      # Files touched
    }

    # Knowledge silo risk thresholds
    SILO_THRESHOLDS = {
        "critical": 0.9,  # Single expert >90%
        "high": 0.8,      # Single expert >80%
        "medium": 0.6     # Single expert >60%
    }

    def __init__(self, db_path: str = "memory/knowledge_graph.db"):
        """Initialize knowledge graph.

        Args:
            db_path: Path to SQLite database
        """
        self.db_path = db_path
        self._ensure_database()
        self._refresh_graph()

    def _ensure_database(self):
        """Create database tables if they don't exist."""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Developer expertise table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS developer_expertise (
                developer TEXT NOT NULL,
                subsystem TEXT NOT NULL,
                expertise_score REAL NOT NULL,
                total_commits INTEGER DEFAULT 0,
                recent_commits INTEGER DEFAULT 0,
                files_touched INTEGER DEFAULT 0,
                last_contribution TEXT,
                PRIMARY KEY (developer, subsystem)
            )
        """)

        # Knowledge silos table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS knowledge_silos (
                subsystem TEXT PRIMARY KEY,
                primary_expert TEXT NOT NULL,
                primary_expertise REAL NOT NULL,
                secondary_expert TEXT,
                secondary_expertise REAL,
                risk_level TEXT NOT NULL,
                detected_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # File contributions table (for detailed tracking)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS file_contributions (
                file_path TEXT NOT NULL,
                developer TEXT NOT NULL,
                commit_count INTEGER DEFAULT 0,
                lines_changed INTEGER DEFAULT 0,
                last_commit TEXT,
                PRIMARY KEY (file_path, developer)
            )
        """)

        conn.commit()
        conn.close()

    def _refresh_graph(self, days: int = 180):
        """Refresh knowledge graph from git history.

        Args:
            days: Number of days to analyze
        """
        try:
            # Get all subsystems
            subsystems = self._get_subsystems()

            # For each subsystem, calculate expertise for all developers
            for subsystem in subsystems:
                files = self._get_subsystem_files(subsystem)

                # Get all contributors
                contributors = self._get_contributors(files)

                for developer in contributors:
                    expertise = self.calculate_expertise(developer, subsystem)

                    # Get contribution stats
                    total_commits = self._count_commits(developer, files, days=None)
                    recent_commits = self._count_commits(developer, files, days=90)
                    files_touched = self._count_files_touched(developer, files)
                    last_contrib = self._get_last_contribution(developer, files)

                    # Update database
                    self._update_expertise(
                        developer=developer,
                        subsystem=subsystem,
                        expertise=expertise,
                        total_commits=total_commits,
                        recent_commits=recent_commits,
                        files_touched=files_touched,
                        last_contribution=last_contrib
                    )

            # Detect knowledge silos
            self._update_silos()

        except Exception as e:
            print(f"Warning: Failed to refresh graph: {e}")

    def calculate_expertise(self, developer: str, subsystem: str) -> float:
        """Calculate developer expertise in subsystem (0.0-1.0).

        Args:
            developer: Developer email
            subsystem: Subsystem path (e.g., "agents/neon-database")

        Returns:
            Expertise score
        """
        try:
            # Get subsystem files
            files = self._get_subsystem_files(subsystem)

            if not files:
                return 0.0

            # Calculate contribution score
            total_commits = 0
            developer_commits = 0

            for file_path in files:
                commits = self._count_file_commits(file_path)
                dev_commits = self._count_file_commits_by_dev(file_path, developer)

                total_commits += commits
                developer_commits += dev_commits

            contribution_score = developer_commits / max(total_commits, 1)

            # Calculate recency weight
            recent_commits = self._count_commits(developer, files, days=90)
            recency_weight = recent_commits / max(developer_commits, 1)

            # Calculate diversity (how many files touched)
            files_touched = self._count_files_touched(developer, files)
            diversity = files_touched / len(files)

            # Weighted score
            expertise = (
                contribution_score * self.WEIGHTS["contribution"] +
                recency_weight * self.WEIGHTS["recency"] +
                diversity * self.WEIGHTS["diversity"]
            )

            return min(expertise, 1.0)

        except Exception as e:
            print(f"Warning: Failed to calculate expertise: {e}")
            return 0.0

    def suggest_reviewers(self, files: List[str], num: int = 2, exclude: List[str] = None) -> List[Dict[str, Any]]:
        """Suggest best reviewers for files.

        Args:
            files: List of file paths
            num: Number of reviewers to suggest
            exclude: Developers to exclude (e.g., PR author)

        Returns:
            List of reviewer suggestions
        """
        try:
            # Get subsystems from files
            subsystems = set()
            for file_path in files:
                parts = Path(file_path).parts
                if len(parts) > 0:
                    subsystems.add(parts[0])

            # Get all developers
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("""
                SELECT DISTINCT developer
                FROM developer_expertise
            """)

            developers = [row[0] for row in cursor.fetchall()]
            conn.close()

            # Calculate scores for each developer
            candidates = []

            for dev in developers:
                if exclude and dev in exclude:
                    continue

                # Average expertise across subsystems
                if subsystems:
                    avg_expertise = sum(
                        self.calculate_expertise(dev, sub) for sub in subsystems
                    ) / len(subsystems)
                else:
                    avg_expertise = 0.0

                # Get availability (from workload analyzer if available)
                try:
                    from shared.workload_analyzer import WorkloadAnalyzer
                    analyzer = WorkloadAnalyzer()
                    workload_result = analyzer.analyze_developer(dev)
                    availability = 1.0 - workload_result.get("score", 0.5)
                except Exception:
                    availability = 0.5  # Default

                # Combined score
                score = avg_expertise * 0.7 + availability * 0.3

                candidates.append({
                    "developer": dev,
                    "score": score,
                    "expertise": avg_expertise,
                    "availability": availability
                })

            # Sort by score
            candidates.sort(key=lambda x: x["score"], reverse=True)

            return candidates[:num]

        except Exception as e:
            print(f"Warning: Failed to suggest reviewers: {e}")
            return []

    def detect_knowledge_silos(self) -> List[Dict[str, Any]]:
        """Detect knowledge silos in codebase.

        Returns:
            List of knowledge silo warnings
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            silos = []

            # Get all subsystems
            cursor.execute("""
                SELECT DISTINCT subsystem
                FROM developer_expertise
            """)

            subsystems = [row[0] for row in cursor.fetchall()]

            for subsystem in subsystems:
                # Get top 2 experts
                cursor.execute("""
                    SELECT developer, expertise_score
                    FROM developer_expertise
                    WHERE subsystem = ?
                    ORDER BY expertise_score DESC
                    LIMIT 2
                """, (subsystem,))

                experts = cursor.fetchall()

                if not experts:
                    continue

                primary_expert, primary_score = experts[0]
                secondary_expert = experts[1][0] if len(experts) > 1 else None
                secondary_score = experts[1][1] if len(experts) > 1 else 0.0

                # Determine risk level
                risk_level = "low"
                if primary_score >= self.SILO_THRESHOLDS["critical"]:
                    risk_level = "critical"
                elif primary_score >= self.SILO_THRESHOLDS["high"]:
                    risk_level = "high"
                elif primary_score >= self.SILO_THRESHOLDS["medium"]:
                    risk_level = "medium"

                if risk_level != "low":
                    silos.append({
                        "subsystem": subsystem,
                        "primary_expert": primary_expert,
                        "primary_expertise": primary_score,
                        "secondary_expert": secondary_expert,
                        "secondary_expertise": secondary_score,
                        "risk_level": risk_level,
                        "gap": primary_score - secondary_score
                    })

            conn.close()

            # Sort by risk
            risk_order = {"critical": 3, "high": 2, "medium": 1}
            silos.sort(key=lambda x: (risk_order[x["risk_level"]], x["gap"]), reverse=True)

            return silos

        except Exception as e:
            print(f"Warning: Failed to detect silos: {e}")
            return []

    def suggest_pairing(self, subsystem: str) -> Dict[str, Any]:
        """Suggest pairing for knowledge transfer.

        Args:
            subsystem: Subsystem to analyze

        Returns:
            Pairing suggestion
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Get experts sorted by expertise
            cursor.execute("""
                SELECT developer, expertise_score
                FROM developer_expertise
                WHERE subsystem = ?
                ORDER BY expertise_score DESC
            """, (subsystem,))

            experts = cursor.fetchall()
            conn.close()

            if len(experts) < 2:
                return {
                    "success": False,
                    "message": "Not enough experts for pairing"
                }

            # Pair highest expert with lowest
            mentor = experts[0]
            mentee = experts[-1]

            return {
                "success": True,
                "subsystem": subsystem,
                "mentor": {
                    "developer": mentor[0],
                    "expertise": mentor[1]
                },
                "mentee": {
                    "developer": mentee[0],
                    "expertise": mentee[1]
                },
                "gap": mentor[1] - mentee[1],
                "suggestion": f"Pair {mentor[0]} (expert) with {mentee[0]} (learner) on {subsystem} tasks"
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def _get_subsystems(self) -> List[str]:
        """Get all subsystems in repository.

        Returns:
            List of subsystem paths
        """
        try:
            # Get all tracked files
            result = subprocess.run(
                ["git", "ls-files"],
                capture_output=True,
                text=True,
                check=True
            )

            subsystems = set()

            for file_path in result.stdout.split('\n'):
                if file_path.strip():
                    parts = Path(file_path).parts
                    if len(parts) > 0:
                        subsystems.add(parts[0])

            return list(subsystems)

        except Exception:
            return []

    def _get_subsystem_files(self, subsystem: str) -> List[str]:
        """Get all files in a subsystem.

        Args:
            subsystem: Subsystem path

        Returns:
            List of file paths
        """
        try:
            result = subprocess.run(
                ["git", "ls-files", f"{subsystem}/*"],
                capture_output=True,
                text=True
            )

            return [f.strip() for f in result.stdout.split('\n') if f.strip()]

        except Exception:
            return []

    def _get_contributors(self, files: List[str]) -> Set[str]:
        """Get all contributors to files.

        Args:
            files: List of file paths

        Returns:
            Set of developer emails
        """
        contributors = set()

        for file_path in files:
            try:
                result = subprocess.run(
                    ["git", "log", "--format=%ae", "--", file_path],
                    capture_output=True,
                    text=True
                )

                for email in result.stdout.split('\n'):
                    if email.strip():
                        contributors.add(email.strip())

            except Exception:
                continue

        return contributors

    def _count_commits(self, developer: str, files: List[str], days: int = None) -> int:
        """Count commits by developer in files.

        Args:
            developer: Developer email
            files: List of file paths
            days: Number of days to look back (None = all time)

        Returns:
            Commit count
        """
        count = 0

        for file_path in files:
            try:
                cmd = ["git", "log", "--author", developer, "--oneline", "--", file_path]

                if days:
                    cutoff = (datetime.utcnow() - timedelta(days=days)).isoformat()
                    cmd.insert(3, f"--since={cutoff}")

                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True
                )

                count += len([line for line in result.stdout.split('\n') if line.strip()])

            except Exception:
                continue

        return count

    def _count_file_commits(self, file_path: str) -> int:
        """Count total commits for a file.

        Args:
            file_path: File path

        Returns:
            Commit count
        """
        try:
            result = subprocess.run(
                ["git", "log", "--oneline", "--", file_path],
                capture_output=True,
                text=True
            )

            return len([line for line in result.stdout.split('\n') if line.strip()])

        except Exception:
            return 0

    def _count_file_commits_by_dev(self, file_path: str, developer: str) -> int:
        """Count commits by developer for a file.

        Args:
            file_path: File path
            developer: Developer email

        Returns:
            Commit count
        """
        try:
            result = subprocess.run(
                ["git", "log", "--author", developer, "--oneline", "--", file_path],
                capture_output=True,
                text=True
            )

            return len([line for line in result.stdout.split('\n') if line.strip()])

        except Exception:
            return 0

    def _count_files_touched(self, developer: str, files: List[str]) -> int:
        """Count files touched by developer.

        Args:
            developer: Developer email
            files: List of file paths

        Returns:
            File count
        """
        count = 0

        for file_path in files:
            if self._count_file_commits_by_dev(file_path, developer) > 0:
                count += 1

        return count

    def _get_last_contribution(self, developer: str, files: List[str]) -> str:
        """Get last contribution time by developer to files.

        Args:
            developer: Developer email
            files: List of file paths

        Returns:
            ISO timestamp or "Never"
        """
        timestamps = []

        for file_path in files:
            try:
                result = subprocess.run(
                    ["git", "log", "--author", developer, "-1", "--format=%aI", "--", file_path],
                    capture_output=True,
                    text=True
                )

                timestamp = result.stdout.strip()
                if timestamp:
                    timestamps.append(timestamp)

            except Exception:
                continue

        return max(timestamps) if timestamps else "Never"

    def _update_expertise(self, **kwargs):
        """Update expertise in database."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("""
                INSERT OR REPLACE INTO developer_expertise
                (developer, subsystem, expertise_score, total_commits, recent_commits,
                 files_touched, last_contribution)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                kwargs["developer"],
                kwargs["subsystem"],
                kwargs["expertise"],
                kwargs["total_commits"],
                kwargs["recent_commits"],
                kwargs["files_touched"],
                kwargs["last_contribution"]
            ))

            conn.commit()
            conn.close()

        except Exception as e:
            print(f"Warning: Failed to update expertise: {e}")

    def _update_silos(self):
        """Update knowledge silos in database."""
        try:
            silos = self.detect_knowledge_silos()

            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Clear old silos
            cursor.execute("DELETE FROM knowledge_silos")

            # Insert new silos
            for silo in silos:
                cursor.execute("""
                    INSERT INTO knowledge_silos
                    (subsystem, primary_expert, primary_expertise, secondary_expert,
                     secondary_expertise, risk_level)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    silo["subsystem"],
                    silo["primary_expert"],
                    silo["primary_expertise"],
                    silo.get("secondary_expert"),
                    silo.get("secondary_expertise", 0.0),
                    silo["risk_level"]
                ))

            conn.commit()
            conn.close()

        except Exception as e:
            print(f"Warning: Failed to update silos: {e}")


if __name__ == "__main__":
    """Demo usage of Knowledge Graph."""
    print("=== Knowledge Graph Demo ===\n")

    print("Building knowledge graph from git history...\n")

    graph = KnowledgeGraph()

    # Detect knowledge silos
    print("Detecting knowledge silos...\n")

    silos = graph.detect_knowledge_silos()

    if silos:
        print(f"⚠️ Found {len(silos)} knowledge silos:\n")

        for silo in silos[:5]:
            print(f"[{silo['risk_level'].upper()}] {silo['subsystem']}")
            print(f"  Primary Expert: {silo['primary_expert']} ({silo['primary_expertise']:.2f})")
            if silo['secondary_expert']:
                print(f"  Secondary: {silo['secondary_expert']} ({silo['secondary_expertise']:.2f})")
            print(f"  Expertise Gap: {silo['gap']:.2f}")
            print()
    else:
        print("✓ No knowledge silos detected - expertise well distributed\n")

    # Suggest reviewers for a file
    print("Suggesting reviewers for 'shared/confidence.py'...\n")

    reviewers = graph.suggest_reviewers(["shared/confidence.py"], num=2)

    if reviewers:
        print("Recommended Reviewers:")
        for i, reviewer in enumerate(reviewers, 1):
            print(f"  {i}. {reviewer['developer']}")
            print(f"     Expertise: {reviewer['expertise']:.2f}")
            print(f"     Availability: {reviewer['availability']:.2f}")
            print(f"     Combined Score: {reviewer['score']:.2f}")
        print()
    else:
        print("No reviewers available\n")
