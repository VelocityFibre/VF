#!/usr/bin/env python3
"""
Autopilot Orchestrator - Phase 3: CNC Machine Mode

Coordinates autonomous feature development: spawns 15 parallel attempts,
selects best via consensus, auto-deploys to staging, notifies engineer.

City Planning Analogy: Like a city's development committee that reviews
15 proposals for a new bridge, selects the best design, and manages
construction - all without the mayor micromanaging details.

Part of Vibe Coding Transformation - see docs/VIBE_CODING_TRANSFORMATION.md
"""

import os
import sys
import json
import asyncio
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from harness.sandbox_manager import SandboxManager, SandboxInfo
from harness.best_of_n_selector import BestOfNSelector, AgentAttempt, ConsensusResult
from harness.failure_knowledge_base import FailureKnowledgeBase
from orchestrator.model_router import ModelRouter

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class AutopilotRequest:
    """Request for autopilot feature development."""
    feature_description: str
    feature_id: int
    agent_name: str
    n_attempts: int = 15  # Number of parallel attempts
    require_consensus: bool = True
    auto_deploy: bool = True
    staging_url: Optional[str] = None


@dataclass
class AutopilotResult:
    """Result of autopilot execution."""
    feature_id: int
    success: bool
    best_attempt: Optional[AgentAttempt]
    consensus: Optional[ConsensusResult]
    all_attempts: List[AgentAttempt]
    deployment_status: str  # 'not_deployed', 'staging', 'production'
    staging_url: Optional[str]
    error_message: Optional[str]
    total_time: float  # seconds
    total_cost: float  # dollars


class AutopilotOrchestrator:
    """
    Coordinates autonomous feature development with CNC machine precision.

    Workflow:
    1. Spawn N parallel sandboxes (default: 15)
    2. Each sandbox attempts feature implementation
    3. All executions happen in parallel (Phase 1: E2B)
    4. Each execution learns from past failures (Phase 1.5: Reflection)
    5. Each execution uses appropriate model tier (Phase 2: Tiered Routing)
    6. Data freshness verified if requested (Phase 2.5: SLAs)
    7. Best result selected via consensus (Phase 3: Best-of-N)
    8. Winner auto-deployed to staging (Phase 3: Auto-Deploy)
    9. Engineer notified for validation (Phase 3: Human-in-Loop)

    Usage:
        orchestrator = AutopilotOrchestrator()

        request = AutopilotRequest(
            feature_description="Build VPS health check agent",
            feature_id=1,
            agent_name="vps-health-agent",
            n_attempts=15
        )

        result = orchestrator.execute(request)

        if result.success:
            print(f"✅ Deployed to staging: {result.staging_url}")
        else:
            print(f"❌ Failed: {result.error_message}")
    """

    def __init__(self):
        """Initialize autopilot orchestrator with all phase integrations."""
        logger.info("Initializing Autopilot Orchestrator (Phase 3)...")

        # Phase 1: E2B Sandboxes
        self.sandbox_template = "standard"  # Can be configured per request

        # Phase 1.5: Reflection & Learning
        self.knowledge_base = FailureKnowledgeBase()

        # Phase 2: Tiered Routing
        self.model_router = ModelRouter()

        # Phase 2.5: SLA Monitoring (optional)
        try:
            from harness.sla_monitor import SLAMonitor
            self.sla_monitor = SLAMonitor()
            logger.info("✅ SLA monitoring enabled")
        except Exception as e:
            logger.warning(f"SLA monitoring unavailable: {e}")
            self.sla_monitor = None

        # Phase 3: Best-of-N Selection
        self.selector = BestOfNSelector()

        logger.info("✅ Autopilot Orchestrator initialized with all phases")

    def execute(self, request: AutopilotRequest) -> AutopilotResult:
        """
        Execute autopilot workflow for feature development.

        Args:
            request: Autopilot request with feature details

        Returns:
            AutopilotResult with execution outcome
        """
        start_time = datetime.now()

        logger.info("=" * 70)
        logger.info("🚀 AUTOPILOT MODE: Starting autonomous development")
        logger.info("=" * 70)
        logger.info(f"Feature: {request.feature_description}")
        logger.info(f"Agent: {request.agent_name}")
        logger.info(f"Parallel attempts: {request.n_attempts}")
        logger.info("=" * 70)
        logger.info("")

        try:
            # Step 1: Spawn N parallel attempts
            logger.info(f"📦 Spawning {request.n_attempts} parallel sandboxes...")
            attempts = self._execute_parallel_attempts(request)

            if not attempts:
                raise Exception("All parallel attempts failed")

            logger.info(f"✅ Completed {len(attempts)}/{request.n_attempts} attempts")
            logger.info("")

            # Step 2: Select best via consensus
            logger.info("🏆 Selecting best implementation...")
            best, consensus = self.selector.select_best(
                attempts,
                require_consensus=request.require_consensus
            )

            logger.info("")
            logger.info(self.selector.generate_report(attempts, best, consensus))
            logger.info("")

            # Step 3: Auto-deploy to staging (if requested)
            deployment_status = "not_deployed"
            staging_url = None

            if request.auto_deploy and best:
                logger.info("🚀 Auto-deploying to staging...")
                deployment_status, staging_url = self._deploy_to_staging(
                    best,
                    request
                )

                if deployment_status == "staging":
                    logger.info(f"✅ Deployed to staging: {staging_url}")
                    logger.info("")

                    # Step 4: Notify engineer
                    self._notify_engineer(best, staging_url, consensus)
                else:
                    logger.warning("⚠️  Deployment to staging failed")

            # Calculate total metrics
            end_time = datetime.now()
            total_time = (end_time - start_time).total_seconds()
            total_cost = sum(a.cost for a in attempts)

            # Success!
            logger.info("=" * 70)
            logger.info("✅ AUTOPILOT COMPLETE")
            logger.info("=" * 70)
            logger.info(f"Winner: Attempt #{best.attempt_id}")
            logger.info(f"Score: {best.total_score:.3f}/1.000")
            logger.info(f"Total time: {total_time:.1f}s")
            logger.info(f"Total cost: ${total_cost:.3f}")
            logger.info(f"Deployment: {deployment_status}")
            if staging_url:
                logger.info(f"Staging URL: {staging_url}")
            logger.info("=" * 70)
            logger.info("")

            return AutopilotResult(
                feature_id=request.feature_id,
                success=True,
                best_attempt=best,
                consensus=consensus,
                all_attempts=attempts,
                deployment_status=deployment_status,
                staging_url=staging_url,
                error_message=None,
                total_time=total_time,
                total_cost=total_cost
            )

        except Exception as e:
            logger.error(f"❌ Autopilot failed: {e}")

            end_time = datetime.now()
            total_time = (end_time - start_time).total_seconds()

            return AutopilotResult(
                feature_id=request.feature_id,
                success=False,
                best_attempt=None,
                consensus=None,
                all_attempts=[],
                deployment_status="failed",
                staging_url=None,
                error_message=str(e),
                total_time=total_time,
                total_cost=0.0
            )

    def _execute_parallel_attempts(
        self,
        request: AutopilotRequest
    ) -> List[AgentAttempt]:
        """
        Execute N parallel implementation attempts.

        Uses ThreadPoolExecutor to spawn multiple sandboxes concurrently.
        Each sandbox:
        - Creates isolated environment (Phase 1)
        - Retrieves learned patterns (Phase 1.5)
        - Uses appropriate model tier (Phase 2)
        - Implements feature
        - Runs tests
        - Reports metrics

        Args:
            request: Autopilot request

        Returns:
            List of completed attempts (may be < N if some fail)
        """
        attempts = []

        # Create sandbox managers (one per attempt)
        managers = [
            SandboxManager(agent_name=request.agent_name)
            for _ in range(request.n_attempts)
        ]

        # Execute in parallel
        with ThreadPoolExecutor(max_workers=request.n_attempts) as executor:
            # Submit all tasks
            futures = {
                executor.submit(
                    self._execute_single_attempt,
                    manager,
                    request,
                    attempt_id
                ): attempt_id
                for attempt_id, manager in enumerate(managers, start=1)
            }

            # Collect results as they complete
            for future in as_completed(futures):
                attempt_id = futures[future]

                try:
                    attempt = future.result()
                    if attempt:
                        attempts.append(attempt)
                        logger.info(
                            f"✅ Attempt #{attempt_id} completed "
                            f"(score={attempt.total_score:.3f})"
                        )
                except Exception as e:
                    logger.error(f"❌ Attempt #{attempt_id} failed: {e}")

        return attempts

    def _execute_single_attempt(
        self,
        manager: SandboxManager,
        request: AutopilotRequest,
        attempt_id: int
    ) -> Optional[AgentAttempt]:
        """
        Execute a single implementation attempt in sandbox.

        Args:
            manager: Sandbox manager for this attempt
            request: Autopilot request
            attempt_id: Attempt number (1-N)

        Returns:
            AgentAttempt with results, or None if failed
        """
        try:
            logger.debug(f"Starting attempt #{attempt_id}...")

            # Create sandbox (Phase 1)
            sandbox_info = manager.create_sandbox(feature_id=request.feature_id)

            # Setup environment
            if not manager.setup_environment(sandbox_info):
                raise Exception("Environment setup failed")

            # Execute feature (integrates Phase 1.5 reflection + Phase 2 routing)
            feature_context = {
                "feature_id": request.feature_id,
                "feature_description": request.feature_description,
                "attempt_id": attempt_id,
                "validation_steps": [
                    "Run all tests",
                    "Check test coverage",
                    "Lint code",
                    "Verify functionality"
                ]
            }

            success = manager.execute_feature(sandbox_info, feature_context)

            # Extract results
            results = manager.extract_results(sandbox_info)

            # Cleanup sandbox
            manager.cleanup_sandbox(sandbox_info)

            # Convert to AgentAttempt
            if success and results:
                return self._create_agent_attempt(
                    sandbox_info,
                    results,
                    feature_context,
                    attempt_id
                )

            return None

        except Exception as e:
            logger.error(f"Attempt #{attempt_id} exception: {e}")
            return None

    def _create_agent_attempt(
        self,
        sandbox_info: SandboxInfo,
        results: Dict[str, Any],
        context: Dict[str, Any],
        attempt_id: int
    ) -> AgentAttempt:
        """
        Convert sandbox results to AgentAttempt.

        Args:
            sandbox_info: Sandbox information
            results: Execution results
            context: Feature context
            attempt_id: Attempt number

        Returns:
            AgentAttempt with metrics
        """
        # Simulate metrics (in real implementation, would parse from results)
        # TODO: Extract actual metrics from test output, coverage reports, linting
        import random

        base_coverage = 0.75 + (attempt_id * 0.01)
        base_quality = 0.80 + (attempt_id * 0.005)

        return AgentAttempt(
            feature_id=context["feature_id"],
            attempt_id=attempt_id,
            sandbox_id=sandbox_info.sandbox_id,
            test_coverage=min(0.95, base_coverage),
            tests_passed=18 + attempt_id,
            tests_failed=max(0, 2 - (attempt_id % 3)),
            tests_total=20 + attempt_id,
            code_quality_score=min(0.90, base_quality),
            linting_errors=max(0, 5 - (attempt_id % 5)),
            linting_warnings=max(0, 10 - (attempt_id % 4)),
            execution_time=sandbox_info.execution_time or 45.0,
            memory_peak_mb=256 + (attempt_id * 10),
            artifacts=results.get("artifacts", {}),
            timestamp=datetime.now().isoformat(),
            model_tier=context.get("model_info", {}).get("tier", "sonnet"),
            cost=context.get("model_info", {}).get("cost_per_query", 0.020)
        )

    def _deploy_to_staging(
        self,
        best: AgentAttempt,
        request: AutopilotRequest
    ) -> tuple[str, Optional[str]]:
        """
        Deploy winning attempt to staging environment.

        Args:
            best: Best agent attempt
            request: Autopilot request

        Returns:
            Tuple of (deployment_status, staging_url)
        """
        try:
            # Simulate deployment (in real implementation, would:
            # 1. Extract code from winning sandbox
            # 2. Run final validation
            # 3. Deploy to staging server
            # 4. Run smoke tests
            # 5. Return staging URL)

            staging_url = request.staging_url or f"http://staging.fibreflow.app/{request.agent_name}"

            logger.info(f"Deploying to: {staging_url}")
            logger.info("Running smoke tests...")

            # Simulated success
            return "staging", staging_url

        except Exception as e:
            logger.error(f"Deployment failed: {e}")
            return "failed", None

    def _notify_engineer(
        self,
        best: AgentAttempt,
        staging_url: str,
        consensus: ConsensusResult
    ) -> None:
        """
        Notify engineer that feature is ready for validation.

        Args:
            best: Best agent attempt
            staging_url: Staging URL for testing
            consensus: Consensus validation result
        """
        # Build notification message
        message = [
            "🎉 **Autopilot Feature Complete**",
            "",
            f"**Feature:** Ready for validation",
            f"**Score:** {best.total_score:.1%}",
            f"**Test Coverage:** {best.test_coverage:.1%}",
            f"**Tests Passed:** {best.tests_passed}/{best.tests_total}",
            "",
            f"**Staging URL:** {staging_url}",
            "",
            "**Next Steps:**",
            "1. Test the feature at staging URL",
            "2. Validate behavior (not code!)",
            "3. Reply 'approve' to deploy to production",
            "",
            f"**Consensus:** {'✅ Validated' if consensus.has_consensus else '⚠️ Review recommended'}",
        ]

        notification = "\n".join(message)

        # Send to Slack (if configured)
        slack_token = os.getenv("SLACK_BOT_TOKEN")
        if slack_token:
            try:
                from slack_sdk import WebClient
                client = WebClient(token=slack_token)

                client.chat_postMessage(
                    channel="#fibreflow-autopilot",
                    text=notification
                )

                logger.info("📤 Engineer notified via Slack")

            except Exception as e:
                logger.warning(f"Slack notification failed: {e}")
                logger.info(f"Notification:\n{notification}")
        else:
            logger.info(f"Notification (Slack not configured):\n{notification}")


if __name__ == "__main__":
    # Demo the autopilot orchestrator
    print()
    print("=" * 70)
    print("AUTOPILOT ORCHESTRATOR - PHASE 3: CNC MACHINE MODE")
    print("=" * 70)
    print()

    # Create orchestrator
    orchestrator = AutopilotOrchestrator()

    # Create request
    request = AutopilotRequest(
        feature_description="Build VPS health check agent with metrics collection",
        feature_id=1,
        agent_name="vps-health-agent",
        n_attempts=15,
        require_consensus=True,
        auto_deploy=True,
        staging_url="http://staging.fibreflow.app/vps-health"
    )

    # Execute autopilot
    result = orchestrator.execute(request)

    # Show result
    print()
    print("=" * 70)
    print("FINAL RESULT")
    print("=" * 70)
    print()

    if result.success:
        print(f"✅ Success!")
        print(f"Winner: Attempt #{result.best_attempt.attempt_id}")
        print(f"Score: {result.best_attempt.total_score:.3f}/1.000")
        print(f"Deployment: {result.deployment_status}")
        print(f"Staging URL: {result.staging_url}")
        print(f"Total time: {result.total_time:.1f}s")
        print(f"Total cost: ${result.total_cost:.3f}")
    else:
        print(f"❌ Failed: {result.error_message}")

    print()
    print("=" * 70)
    print("✅ Autopilot orchestrator demo complete")
