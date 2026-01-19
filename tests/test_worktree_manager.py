#!/usr/bin/env python3
"""
Tests for Git Worktree Manager

Phase 1: Auto-Claude Integration - Worktree Safety

Tests verify that:
1. Worktrees can be created
2. Changes in worktree don't affect main branch
3. Merges work correctly
4. Cleanup removes worktrees
"""

import pytest
import subprocess
import shutil
from pathlib import Path
import os
import sys

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from harness.worktree_manager import WorktreeManager, WorkspaceInfo


@pytest.fixture
def temp_git_repo(tmp_path):
    """Create a temporary git repository for testing."""
    repo_dir = tmp_path / "test_repo"
    repo_dir.mkdir()

    # Initialize git repo
    subprocess.run(["git", "init"], cwd=repo_dir, check=True, capture_output=True)
    subprocess.run(
        ["git", "config", "user.email", "test@fibreflow.local"],
        cwd=repo_dir,
        check=True,
        capture_output=True
    )
    subprocess.run(
        ["git", "config", "user.name", "Test User"],
        cwd=repo_dir,
        check=True,
        capture_output=True
    )

    # Create initial commit
    test_file = repo_dir / "README.md"
    test_file.write_text("# Test Repository\n")

    subprocess.run(["git", "add", "README.md"], cwd=repo_dir, check=True, capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", "Initial commit"],
        cwd=repo_dir,
        check=True,
        capture_output=True
    )

    # Save current directory
    original_cwd = os.getcwd()

    # Change to repo
    os.chdir(repo_dir)

    yield repo_dir

    # Restore directory
    os.chdir(original_cwd)


@pytest.mark.unit
@pytest.mark.harness
def test_worktree_creation(temp_git_repo):
    """Test that worktrees can be created."""
    manager = WorktreeManager(agent_name="test_agent")

    workspace = manager.create_workspace()

    assert workspace.worktree_path.exists()
    assert workspace.branch_name.startswith("build/test_agent/")
    assert workspace.agent_name == "test_agent"

    # Cleanup
    manager.cleanup_workspace(workspace, force=True)


@pytest.mark.unit
@pytest.mark.harness
def test_worktree_isolation(temp_git_repo):
    """Test that changes in worktree don't affect main branch."""
    manager = WorktreeManager(agent_name="test_agent")

    # Create worktree
    workspace = manager.create_workspace()

    # Get main branch file content
    main_readme = temp_git_repo / "README.md"
    original_content = main_readme.read_text()

    # Make change in worktree
    worktree_readme = workspace.worktree_path / "README.md"
    worktree_readme.write_text("# Modified in worktree\n")

    # Commit in worktree
    subprocess.run(
        ["git", "add", "README.md"],
        cwd=workspace.worktree_path,
        check=True,
        capture_output=True
    )
    subprocess.run(
        ["git", "commit", "-m", "Test change in worktree"],
        cwd=workspace.worktree_path,
        check=True,
        capture_output=True
    )

    # Verify main branch unchanged
    assert main_readme.read_text() == original_content

    # Cleanup
    manager.cleanup_workspace(workspace, force=True)


@pytest.mark.unit
@pytest.mark.harness
def test_worktree_merge(temp_git_repo):
    """Test that worktree changes can be merged to main."""
    manager = WorktreeManager(agent_name="test_agent")

    # Create worktree
    workspace = manager.create_workspace()

    # Make change in worktree
    worktree_readme = workspace.worktree_path / "README.md"
    new_content = "# Modified in worktree\n"
    worktree_readme.write_text(new_content)

    # Commit in worktree
    subprocess.run(
        ["git", "add", "README.md"],
        cwd=workspace.worktree_path,
        check=True,
        capture_output=True
    )
    subprocess.run(
        ["git", "commit", "-m", "Test change for merge"],
        cwd=workspace.worktree_path,
        check=True,
        capture_output=True
    )

    # Merge to main
    success = manager.merge_to_main(workspace)

    assert success == True

    # Verify main branch now has the change
    main_readme = temp_git_repo / "README.md"
    assert main_readme.read_text() == new_content

    # Cleanup
    manager.cleanup_workspace(workspace, force=True)


@pytest.mark.unit
@pytest.mark.harness
def test_worktree_cleanup(temp_git_repo):
    """Test that worktrees are properly removed."""
    manager = WorktreeManager(agent_name="test_agent")

    # Create worktree
    workspace = manager.create_workspace()
    worktree_path = workspace.worktree_path

    assert worktree_path.exists()

    # Cleanup
    manager.cleanup_workspace(workspace, force=True)

    # Verify removed
    assert not worktree_path.exists()


@pytest.mark.unit
@pytest.mark.harness
def test_worktree_list(temp_git_repo):
    """Test listing active worktrees."""
    manager = WorktreeManager(agent_name="test_agent")

    # Create two worktrees
    workspace1 = manager.create_workspace()
    workspace2 = manager.create_workspace()

    # List worktrees
    worktrees = manager.list_workspaces()

    # Should have at least 3 (main + 2 created)
    assert len(worktrees) >= 3

    # Cleanup
    manager.cleanup_workspace(workspace1, force=True)
    manager.cleanup_workspace(workspace2, force=True)


@pytest.mark.unit
@pytest.mark.harness
def test_multiple_worktrees_parallel(temp_git_repo):
    """Test that multiple worktrees can exist simultaneously (for Phase 3 parallelism)."""
    manager1 = WorktreeManager(agent_name="agent1")
    manager2 = WorktreeManager(agent_name="agent2")

    # Create multiple worktrees
    workspace1 = manager1.create_workspace()
    workspace2 = manager2.create_workspace()

    # Both should exist
    assert workspace1.worktree_path.exists()
    assert workspace2.worktree_path.exists()

    # Make changes in both
    (workspace1.worktree_path / "agent1.txt").write_text("Agent 1 work")
    (workspace2.worktree_path / "agent2.txt").write_text("Agent 2 work")

    # Cleanup
    manager1.cleanup_workspace(workspace1, force=True)
    manager2.cleanup_workspace(workspace2, force=True)


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "--tb=short"])
