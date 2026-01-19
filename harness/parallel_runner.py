#!/usr/bin/env python3
"""
Parallel Harness Runner for Agent Development

Executes features in parallel while respecting dependencies, integrating with
Phase 1 (worktrees) and Phase 2 (self-healing validation).

Phase 3: Auto-Claude Integration - Parallel Execution
"""

import json
import time
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
import sys

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from harness.dependency_graph import DependencyGraph
from harness.rate_limit_handler import RateLimitHandler
from harness.worktree_manager import WorktreeManager, WorkspaceInfo


class ParallelHarness:
    """
    Orchestrates parallel execution of agent features with dependency awareness.

    Integrates:
    - Phase 1: Git worktrees for isolation
    - Phase 2: Self-healing validation
    - Phase 3: Parallel execution with dependency scheduling

    Example:
        harness = ParallelHarness(
            agent_name="sharepoint",
            run_dir=Path("harness/runs/latest"),
            max_workers=6
        )

        results = harness.run()
        print(f"Completed {results['completed']}/{results['total']} features")
        print(f"Speedup: {results['speedup']:.1f}x")
    """

    def __init__(
        self,
        agent_name: str,
        run_dir: Path,
        max_workers: int = 6,
        enable_rate_limit_handling: bool = True
    ):
        """
        Initialize parallel harness.

        Args:
            agent_name: Name of agent being built
            run_dir: Run directory containing feature_list.json
            max_workers: Maximum parallel workers (default: 6)
            enable_rate_limit_handling: Enable rate limit backoff (default: True)
        """
        self.agent_name = agent_name
        self.run_dir = Path(run_dir)
        self.max_workers = max_workers
        self.enable_rate_limit_handling = enable_rate_limit_handling

        # Load feature list
        self.feature_list_path = self.run_dir / "feature_list.json"
        self.features = self._load_features()

        # Initialize components
        self.dependency_graph = DependencyGraph(self.features)
        self.rate_limit_handler = RateLimitHandler() if enable_rate_limit_handling else None
        self.worktree_manager = WorktreeManager(agent_name=agent_name)

        # Tracking
        self.start_time = None
        self.end_time = None
        self.level_results = []  # Results per level
        self.feature_workspaces = {}  # feature_id -> WorkspaceInfo
        self.feature_results = {}  # feature_id -> success/failure

    def _load_features(self) -> List[Dict[str, Any]]:
        """Load features from feature_list.json."""
        if not self.feature_list_path.exists():
            raise FileNotFoundError(f"Feature list not found: {self.feature_list_path}")

        with open(self.feature_list_path) as f:
            data = json.load(f)

        return data.get('features', [])

    def _save_features(self) -> None:
        """Save updated features to feature_list.json."""
        with open(self.feature_list_path) as f:
            data = json.load(f)

        data['features'] = self.features

        # Update completed count
        completed = sum(1 for f in self.features if f.get('passes', False))
        data['completed'] = completed

        # Add Phase 3 metrics if not present
        if 'metrics' not in data:
            data['metrics'] = {}

        data['metrics']['phase3_enabled'] = True
        data['metrics']['parallel_workers'] = self.max_workers

        with open(self.feature_list_path, 'w') as f:
            json.dump(data, f, indent=2)

    def run(self) -> Dict[str, Any]:
        """
        Run parallel harness execution.

        Returns:
            Dictionary with execution summary including:
            - total: Total features
            - completed: Features completed
            - failed: Features failed
            - speedup: Speedup factor vs sequential
            - duration: Total execution time
            - levels: Level-by-level results
        """
        print("=" * 70)
        print("FibreFlow Parallel Harness - Phase 3")
        print("=" * 70)
        print(f"Agent: {self.agent_name}")
        print(f"Features: {len(self.features)}")
        print(f"Workers: {self.max_workers}")
        print("=" * 70)
        print()

        self.start_time = datetime.now()

        try:
            # Compute dependency levels
            print("📊 Analyzing dependencies...")
            levels = self.dependency_graph.compute_levels()
            stats = self.dependency_graph.get_level_stats()

            print(f"✅ Dependency analysis complete")
            print(f"   Levels: {stats['total_levels']}")
            print(f"   Max parallelism: {stats['max_parallelism']} features")
            print(f"   Avg parallelism: {stats['avg_parallelism']:.1f} features/level")
            print()

            # Show visualization
            print(self.dependency_graph.visualize_levels())
            print()

            # Execute level-by-level
            print("🚀 Starting parallel execution...")
            print()

            for level_num, level_feature_ids in enumerate(levels):
                level_result = self._run_level(level_num, level_feature_ids)
                self.level_results.append(level_result)

                # Check for rate limit recommendation
                if self.rate_limit_handler and self.rate_limit_handler.should_reduce_workers():
                    recommended = self.rate_limit_handler.get_recommendation(self.max_workers)
                    if recommended and recommended < self.max_workers:
                        print(f"⚠️  Reducing workers from {self.max_workers} to {recommended} (rate limits)")
                        self.max_workers = recommended

            self.end_time = datetime.now()

            # Generate summary
            return self._generate_summary()

        except Exception as e:
            print(f"❌ Parallel harness failed: {e}")
            raise

    def _run_level(self, level_num: int, feature_ids: List[int]) -> Dict[str, Any]:
        """
        Execute all features in a dependency level in parallel.

        Args:
            level_num: Level number
            feature_ids: List of feature IDs to execute

        Returns:
            Dictionary with level execution results
        """
        level_start = datetime.now()

        print(f"📦 Level {level_num} ({len(feature_ids)} features)")
        print(f"   Features: {feature_ids}")
        print()

        # Determine actual worker count (min of max_workers and features in level)
        actual_workers = min(self.max_workers, len(feature_ids))

        # Execute features in parallel
        with ThreadPoolExecutor(max_workers=actual_workers) as executor:
            # Submit all features in level
            future_to_feature = {
                executor.submit(self._run_feature, feature_id): feature_id
                for feature_id in feature_ids
            }

            # Collect results as they complete
            completed_count = 0
            failed_count = 0

            for future in as_completed(future_to_feature):
                feature_id = future_to_feature[future]

                try:
                    success = future.result()
                    self.feature_results[feature_id] = success

                    if success:
                        completed_count += 1
                        print(f"   ✅ Feature {feature_id} completed")
                    else:
                        failed_count += 1
                        print(f"   ⚠️  Feature {feature_id} failed (see logs)")

                except Exception as e:
                    failed_count += 1
                    self.feature_results[feature_id] = False
                    print(f"   ❌ Feature {feature_id} error: {e}")

        level_end = datetime.now()
        level_duration = (level_end - level_start).total_seconds()

        print()
        print(f"   Level {level_num} complete: {completed_count}/{len(feature_ids)} succeeded")
        print(f"   Duration: {level_duration:.1f}s")
        print()

        return {
            'level': level_num,
            'features': feature_ids,
            'completed': completed_count,
            'failed': failed_count,
            'duration': level_duration
        }

    def _run_feature(self, feature_id: int) -> bool:
        """
        Execute a single feature in isolated worktree (Production Implementation).

        Integrates all three phases:
        - Phase 1: Creates isolated git worktree
        - Phase 2: Uses self-healing coding_agent prompt
        - Phase 3: Runs in parallel with other features

        Args:
            feature_id: Feature ID to execute

        Returns:
            True if feature completed successfully, False otherwise
        """
        from harness.worktree_manager import WorktreeManager
        from harness.session_executor import SessionExecutor
        from pathlib import Path
        import json

        feature = self.dependency_graph.get_feature(feature_id)
        feature_desc = feature.get('description', 'No description')[:60]

        print(f"   🔨 Feature {feature_id}: {feature_desc}...")

        # Phase 1: Create isolated worktree for this feature
        manager = WorktreeManager(agent_name=f"{self.agent_name}_feature{feature_id}")
        workspace = None

        try:
            # Create workspace
            workspace = manager.create_workspace()
            original_cwd = Path.cwd()

            # Change to workspace
            manager.change_to_workspace(workspace)

            # Phase 2: Execute coding session with self-healing prompt
            # Create feature-specific context
            feature_context = {
                "agent_name": self.agent_name,
                "run_dir": str(self.run_dir),
                "feature_id": feature_id,
                "feature_description": feature.get('description', ''),
                "validation_steps": json.dumps(feature.get('validation_steps', [])),
                "session_number": feature_id,
                "spec_file": str(self.run_dir.parent.parent / "specs" / f"{self.agent_name}_spec.md"),
                "feature_list": str(self.run_dir / "feature_list.json"),
                "progress_file": str(self.run_dir / "claude_progress.md"),
            }

            # Load coding agent prompt (with self-healing)
            prompt_file = self.run_dir.parent.parent / "prompts" / "coding_agent.md"
            with open(prompt_file) as f:
                prompt = f.read()

            # Create feature-specific session log
            session_log = self.run_dir / "sessions" / f"feature_{feature_id:03d}.log"
            session_log.parent.mkdir(parents=True, exist_ok=True)

            # Execute session
            executor = SessionExecutor(model=self.model, timeout_minutes=30)
            success = executor.execute_session(
                prompt=prompt,
                context=feature_context,
                session_log=session_log,
                working_dir=workspace.worktree_path
            )

            # Return to original directory
            os.chdir(original_cwd)

            if success:
                # Merge worktree to main
                merge_success = manager.merge_to_main(workspace)

                if merge_success:
                    # Update feature in list
                    for f in self.features:
                        if f['id'] == feature_id:
                            f['passes'] = True
                            f['completed_at'] = datetime.now().isoformat()
                            break

                    # Cleanup worktree
                    manager.cleanup_workspace(workspace)
                    return True
                else:
                    print(f"      ⚠️  Merge failed for feature {feature_id}")
                    # Keep worktree for manual merge
                    return False
            else:
                # Return to original directory
                os.chdir(original_cwd)

                # Update feature in list
                for f in self.features:
                    if f['id'] == feature_id:
                        f['passes'] = False
                        f['manual_review_needed'] = True
                        break

                return False

        except Exception as e:
            print(f"      ❌ Error in feature {feature_id}: {e}")

            # Ensure we're back in original directory
            if workspace:
                try:
                    os.chdir(workspace.original_cwd)
                except:
                    pass

            # Update feature as failed
            for f in self.features:
                if f['id'] == feature_id:
                    f['passes'] = False
                    f['error'] = str(e)
                    f['manual_review_needed'] = True
                    break

            return False

    def _generate_summary(self) -> Dict[str, Any]:
        """Generate execution summary with metrics."""
        duration = (self.end_time - self.start_time).total_seconds()

        completed = sum(1 for success in self.feature_results.values() if success)
        failed = len(self.feature_results) - completed

        # Calculate speedup
        # Sequential estimate: total features × 20 min per feature
        sequential_estimate_min = len(self.features) * 20
        parallel_actual_min = duration / 60
        speedup = sequential_estimate_min / parallel_actual_min if parallel_actual_min > 0 else 0

        summary = {
            'total': len(self.features),
            'completed': completed,
            'failed': failed,
            'completion_rate': completed / len(self.features) if self.features else 0,
            'duration_seconds': duration,
            'duration_minutes': duration / 60,
            'sequential_estimate_minutes': sequential_estimate_min,
            'speedup': speedup,
            'levels': self.level_results,
            'max_workers': self.max_workers,
        }

        # Add rate limit stats if available
        if self.rate_limit_handler:
            summary['rate_limit_stats'] = self.rate_limit_handler.get_stats()

        # Save updated features
        self._save_features()

        # Print summary
        print("=" * 70)
        print("Parallel Harness Execution Complete")
        print("=" * 70)
        print(f"Total Features: {summary['total']}")
        print(f"Completed: {summary['completed']} ({summary['completion_rate']*100:.1f}%)")
        print(f"Failed: {summary['failed']}")
        print(f"Duration: {summary['duration_minutes']:.1f} minutes")
        print(f"Sequential Estimate: {summary['sequential_estimate_minutes']:.0f} minutes")
        print(f"Speedup: {summary['speedup']:.1f}x")
        print("=" * 70)

        return summary


if __name__ == "__main__":
    # Example/test usage
    import argparse

    parser = argparse.ArgumentParser(description="Parallel Harness Runner")
    parser.add_argument("--agent", required=True, help="Agent name")
    parser.add_argument("--run-dir", help="Run directory (default: harness/runs/latest)")
    parser.add_argument("--workers", type=int, default=6, help="Max workers (default: 6)")
    parser.add_argument("--no-rate-limit-handling", action="store_true",
                       help="Disable rate limit handling")

    args = parser.parse_args()

    # Determine run directory
    if args.run_dir:
        run_dir = Path(args.run_dir)
    else:
        run_dir = Path("harness/runs/latest")

    # Run parallel harness
    harness = ParallelHarness(
        agent_name=args.agent,
        run_dir=run_dir,
        max_workers=args.workers,
        enable_rate_limit_handling=not args.no_rate_limit_handling
    )

    results = harness.run()

    # Exit with appropriate code
    sys.exit(0 if results['failed'] == 0 else 1)
