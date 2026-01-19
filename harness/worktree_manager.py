#!/usr/bin/env python3
"""
Git Worktree Manager for FibreFlow Agent Harness

Provides isolated development environments for agent builds using git worktrees.
Prevents production code breaks by isolating all commits until build is complete.

Usage:
    from harness.worktree_manager import WorktreeManager

    # Create isolated workspace
    manager = WorktreeManager(agent_name="sharepoint")
    workspace = manager.create_workspace()

    try:
        # ... build agent in worktree ...
        workspace.execute()
    finally:
        # Merge to main and cleanup
        workspace.merge_to_main()
        workspace.cleanup()

Architecture Pattern (from Auto-Claude):
    main branch (stable, production)
        ↓
    .worktrees/agent_name_timestamp/ (isolated development)
        ↓
    Merge only when validation passes
"""

import os
import subprocess
import shutil
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Tuple
from dataclasses import dataclass


@dataclass
class WorkspaceInfo:
    """Information about an isolated worktree workspace."""
    worktree_path: Path
    branch_name: str
    agent_name: str
    created_at: datetime
    original_cwd: Path


class WorktreeManager:
    """
    Manages git worktrees for isolated agent development.

    Git worktrees allow multiple working trees attached to the same repository.
    This enables safe parallel development without affecting the main branch.

    Benefits:
    - Zero risk to main branch during overnight builds
    - Easy rollback (just delete worktree)
    - Parallel agent development
    - Clean separation of concerns
    """

    def __init__(self, agent_name: str, base_dir: Optional[Path] = None):
        """
        Initialize worktree manager for an agent build.

        Args:
            agent_name: Name of agent being built (e.g., "sharepoint")
            base_dir: Base directory for worktrees (default: .worktrees/)
        """
        self.agent_name = agent_name
        self.base_dir = base_dir or Path(".worktrees")
        self.base_dir.mkdir(parents=True, exist_ok=True)

        # Find project root (where .git directory is)
        self.project_root = self._find_project_root()

    def _find_project_root(self) -> Path:
        """Find the git repository root."""
        current = Path.cwd().resolve()

        while current != current.parent:
            if (current / ".git").exists():
                return current
            current = current.parent

        raise RuntimeError("Not in a git repository! Run: git init")

    def _run_git_command(
        self,
        command: List[str],
        cwd: Optional[Path] = None,
        check: bool = True
    ) -> Tuple[int, str, str]:
        """
        Run a git command and return (returncode, stdout, stderr).

        Args:
            command: Git command as list (e.g., ["git", "status"])
            cwd: Working directory (default: project root)
            check: Raise exception on non-zero exit (default: True)

        Returns:
            Tuple of (returncode, stdout, stderr)
        """
        cwd = cwd or self.project_root

        result = subprocess.run(
            command,
            cwd=cwd,
            capture_output=True,
            text=True
        )

        if check and result.returncode != 0:
            raise subprocess.CalledProcessError(
                result.returncode,
                command,
                output=result.stdout,
                stderr=result.stderr
            )

        return result.returncode, result.stdout, result.stderr

    def create_workspace(self) -> WorkspaceInfo:
        """
        Create isolated git worktree for agent development.

        Returns:
            WorkspaceInfo with details about the created workspace

        Raises:
            RuntimeError: If worktree creation fails
        """
        # Generate unique workspace identifiers (with microseconds for uniqueness)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        worktree_name = f"{self.agent_name}_{timestamp}"
        worktree_path = self.project_root / self.base_dir / worktree_name
        branch_name = f"build/{self.agent_name}/{timestamp}"

        print(f"📁 Creating isolated workspace: {worktree_name}")
        print(f"   Branch: {branch_name}")
        print(f"   Path: {worktree_path}")

        try:
            # Create worktree with new branch
            self._run_git_command([
                "git", "worktree", "add",
                str(worktree_path),
                "-b", branch_name
            ])

            print(f"✅ Workspace created successfully")

            return WorkspaceInfo(
                worktree_path=worktree_path,
                branch_name=branch_name,
                agent_name=self.agent_name,
                created_at=datetime.now(),
                original_cwd=Path.cwd()
            )

        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to create worktree: {e.stderr}")
            raise RuntimeError(f"Worktree creation failed: {e.stderr}")

    def change_to_workspace(self, workspace: WorkspaceInfo):
        """
        Change working directory to the worktree.

        Args:
            workspace: WorkspaceInfo from create_workspace()
        """
        os.chdir(workspace.worktree_path)
        print(f"📂 Changed to workspace: {workspace.worktree_path}")

    def _get_default_branch(self) -> str:
        """Get the name of the default branch (main or master)."""
        # Try to get symbolic ref
        try:
            _, stdout, _ = self._run_git_command(
                ["git", "symbolic-ref", "refs/remotes/origin/HEAD"],
                check=False
            )
            if stdout:
                # Extract branch name from refs/remotes/origin/main
                return stdout.strip().split("/")[-1]
        except:
            pass

        # Fallback: check current branch
        try:
            _, stdout, _ = self._run_git_command(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                check=False
            )
            if stdout and stdout.strip():
                return stdout.strip()
        except:
            pass

        # Final fallback: try main, then master
        for branch in ["main", "master"]:
            returncode, _, _ = self._run_git_command(
                ["git", "rev-parse", "--verify", branch],
                check=False
            )
            if returncode == 0:
                return branch

        # Absolute fallback
        return "main"

    def merge_to_main(
        self,
        workspace: WorkspaceInfo,
        main_branch: Optional[str] = None,
        auto_resolve: bool = True
    ) -> bool:
        """
        Merge completed agent build back to main branch.

        Implements multi-tier merge strategy (inspired by Auto-Claude):
        1. Try standard git merge
        2. If conflicts, try AI-assisted resolution (if available)
        3. If still conflicts, fail with detailed report

        Args:
            workspace: WorkspaceInfo from create_workspace()
            main_branch: Name of main branch (default: auto-detect)
            auto_resolve: Attempt automatic conflict resolution (default: True)

        Returns:
            True if merge succeeded, False otherwise
        """
        # Auto-detect main branch if not specified
        if main_branch is None:
            main_branch = self._get_default_branch()

        print(f"🔀 Merging {workspace.branch_name} → {main_branch}")

        # Return to project root
        os.chdir(self.project_root)

        try:
            # Checkout main branch
            print(f"   Switching to {main_branch}...")
            self._run_git_command(["git", "checkout", main_branch])

            # Attempt merge
            print(f"   Merging branch...")
            returncode, stdout, stderr = self._run_git_command(
                ["git", "merge", workspace.branch_name, "--no-ff"],
                check=False
            )

            if returncode == 0:
                print(f"✅ Merge successful!")
                return True

            # Merge conflict detected
            print(f"⚠️  Merge conflicts detected")

            if auto_resolve:
                return self._resolve_conflicts(workspace, main_branch)
            else:
                print(f"❌ Auto-resolve disabled. Manual intervention required.")
                self._print_conflict_help(workspace)
                return False

        except subprocess.CalledProcessError as e:
            print(f"❌ Merge failed: {e.stderr}")
            return False

    def _resolve_conflicts(
        self,
        workspace: WorkspaceInfo,
        main_branch: str
    ) -> bool:
        """
        Multi-tier conflict resolution strategy.

        Tier 1: Standard git merge (already tried)
        Tier 2: Conflict-only AI resolution (TODO: implement)
        Tier 3: Full-file AI resolution (TODO: implement)

        Args:
            workspace: WorkspaceInfo from create_workspace()
            main_branch: Name of main branch

        Returns:
            True if conflicts resolved, False otherwise
        """
        # Get list of conflicted files
        _, stdout, _ = self._run_git_command(
            ["git", "diff", "--name-only", "--diff-filter=U"],
            check=False
        )

        conflict_files = [f.strip() for f in stdout.split("\n") if f.strip()]

        if not conflict_files:
            print("   No conflicts found (unexpected)")
            return True

        print(f"   Conflicts in {len(conflict_files)} file(s):")
        for f in conflict_files:
            print(f"     - {f}")

        # Tier 2: AI-assisted resolution
        # TODO: Integrate with Claude Code to resolve conflicts
        # For now, we abort and require manual intervention
        print(f"\n⚠️  Automatic conflict resolution not yet implemented")
        print(f"   This is a Phase 4 feature (Multi-Tier Merge Resolution)")

        self._print_conflict_help(workspace)

        # Abort merge
        self._run_git_command(["git", "merge", "--abort"], check=False)

        return False

    def _print_conflict_help(self, workspace: WorkspaceInfo):
        """Print helpful instructions for manual conflict resolution."""
        print(f"\n📋 Manual Conflict Resolution Steps:")
        print(f"")
        print(f"1. Review conflicts:")
        print(f"   git status")
        print(f"")
        print(f"2. Resolve each file manually or use:")
        print(f"   git mergetool")
        print(f"")
        print(f"3. After resolving, commit the merge:")
        print(f"   git add .")
        print(f"   git commit -m 'Merge {workspace.branch_name}'")
        print(f"")
        print(f"4. Clean up worktree:")
        print(f"   ./harness/worktree_manager.py --cleanup {workspace.agent_name}")
        print(f"")

    def cleanup_workspace(self, workspace: WorkspaceInfo, force: bool = False):
        """
        Remove worktree and clean up resources.

        Args:
            workspace: WorkspaceInfo from create_workspace()
            force: Force removal even if worktree has uncommitted changes
        """
        print(f"🧹 Cleaning up workspace: {workspace.worktree_path}")

        # Return to original directory if we're in the worktree
        if Path.cwd().is_relative_to(workspace.worktree_path):
            os.chdir(workspace.original_cwd)

        try:
            # Remove worktree
            force_flag = ["--force"] if force else []
            self._run_git_command(
                ["git", "worktree", "remove", str(workspace.worktree_path)] + force_flag
            )

            print(f"✅ Workspace removed")

            # Optionally delete branch (keep by default for history)
            # Uncomment to auto-delete:
            # self._run_git_command(["git", "branch", "-D", workspace.branch_name])
            # print(f"   Branch {workspace.branch_name} deleted")

        except subprocess.CalledProcessError as e:
            print(f"⚠️  Cleanup warning: {e.stderr}")
            print(f"   Manual cleanup may be required:")
            print(f"   rm -rf {workspace.worktree_path}")
            print(f"   git worktree prune")

    def list_workspaces(self) -> List[dict]:
        """
        List all active worktrees for this repository.

        Returns:
            List of dicts with worktree information
        """
        _, stdout, _ = self._run_git_command(["git", "worktree", "list", "--porcelain"])

        worktrees = []
        current = {}

        for line in stdout.split("\n"):
            if not line.strip():
                if current:
                    worktrees.append(current)
                    current = {}
                continue

            if line.startswith("worktree "):
                current["path"] = line.replace("worktree ", "")
            elif line.startswith("branch "):
                current["branch"] = line.replace("branch ", "").replace("refs/heads/", "")
            elif line.startswith("HEAD "):
                current["commit"] = line.replace("HEAD ", "")

        if current:
            worktrees.append(current)

        return worktrees

    def prune_old_workspaces(self, days: int = 30):
        """
        Clean up worktree metadata for removed directories.

        Git maintains worktree metadata even after directories are deleted.
        This removes stale references.

        Args:
            days: Remove metadata for worktrees older than this (default: 30)
        """
        print(f"🧹 Pruning worktree metadata (older than {days} days)...")

        try:
            self._run_git_command(["git", "worktree", "prune"])
            print(f"✅ Worktree metadata cleaned")
        except subprocess.CalledProcessError as e:
            print(f"⚠️  Prune warning: {e.stderr}")


# CLI interface for standalone usage
def main():
    """CLI interface for worktree management."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Git Worktree Manager for FibreFlow Agent Harness"
    )
    parser.add_argument("--agent", help="Agent name")
    parser.add_argument("--list", action="store_true", help="List all worktrees")
    parser.add_argument("--prune", action="store_true", help="Prune old worktrees")
    parser.add_argument("--cleanup", metavar="AGENT", help="Cleanup worktree for agent")

    args = parser.parse_args()

    manager = WorktreeManager(agent_name=args.agent or "unknown")

    if args.list:
        worktrees = manager.list_workspaces()
        print(f"\n📋 Active Worktrees ({len(worktrees)}):\n")
        for wt in worktrees:
            print(f"  Path:   {wt.get('path', 'N/A')}")
            print(f"  Branch: {wt.get('branch', 'N/A')}")
            print(f"  Commit: {wt.get('commit', 'N/A')[:8]}")
            print()

    elif args.prune:
        manager.prune_old_workspaces()

    elif args.cleanup:
        # Find worktree for agent
        worktrees = manager.list_workspaces()
        agent_worktrees = [
            wt for wt in worktrees
            if args.cleanup in wt.get("path", "")
        ]

        if not agent_worktrees:
            print(f"❌ No worktree found for agent: {args.cleanup}")
            return

        for wt in agent_worktrees:
            workspace = WorkspaceInfo(
                worktree_path=Path(wt["path"]),
                branch_name=wt.get("branch", "unknown"),
                agent_name=args.cleanup,
                created_at=datetime.now(),
                original_cwd=Path.cwd()
            )
            manager.cleanup_workspace(workspace, force=True)

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
