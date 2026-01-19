#!/usr/bin/env python3
"""
Sandbox Manager for Isolated Agent Execution (Phase 1 + 2)

Manages E2B sandboxes for parallel, isolated agent builds with tiered model routing.
Each sandbox:
- Clones FibreFlow repo
- Has isolated filesystem
- Executes feature development with appropriate Claude model (Haiku/Sonnet/Opus)
- Returns results/artifacts

Part of Vibe Coding Transformation - see docs/VIBE_CODING_TRANSFORMATION.md
"""

import os
import json
import time
import sys
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from datetime import datetime
import logging

# Configure logging FIRST
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from e2b_code_interpreter.code_interpreter_sync import Sandbox
except ImportError:
    raise ImportError(
        "E2B SDK not installed. Run: ./venv/bin/pip install e2b-code-interpreter"
    )

# Import failure knowledge base for Phase 1.5 (reflection)
try:
    from harness.failure_knowledge_base import FailureKnowledgeBase, FailurePattern
except ImportError:
    # If running as standalone, try relative import
    try:
        from failure_knowledge_base import FailureKnowledgeBase, FailurePattern
    except ImportError:
        logger.warning("FailureKnowledgeBase not available - reflection disabled")
        FailureKnowledgeBase = None
        FailurePattern = None

# Phase 2: Import model router for tiered routing
try:
    from orchestrator.model_router import ModelRouter, ModelTierEnum
except ImportError:
    logger.warning("ModelRouter not available - using default Sonnet model")
    ModelRouter = None
    ModelTierEnum = None


@dataclass
class SandboxInfo:
    """Information about a created sandbox."""
    sandbox_id: str
    feature_id: int
    created_at: str
    status: str  # 'created', 'running', 'completed', 'failed', 'terminated'
    repo_path: str
    logs_path: Optional[str] = None
    error: Optional[str] = None
    execution_time: Optional[float] = None


class SandboxManager:
    """
    Manages E2B sandboxes for isolated agent execution.

    City Planning Analogy: Like construction site manager that sets up
    isolated work zones for parallel teams to build different features.

    Usage:
        manager = SandboxManager()

        # Create sandbox
        sandbox_info = manager.create_sandbox(feature_id=1)

        # Execute feature in sandbox
        success = manager.execute_feature(
            sandbox_info=sandbox_info,
            feature_context={...}
        )

        # Extract results
        results = manager.extract_results(sandbox_info)

        # Cleanup
        manager.cleanup_sandbox(sandbox_info)
    """

    def __init__(
        self,
        agent_name: str = "default",
        repo_url: Optional[str] = None,
        working_dir: Path = Path("/tmp/fibreflow")
    ):
        """
        Initialize SandboxManager.

        Args:
            agent_name: Name of agent being built (for tracking)
            repo_url: Git repository URL (defaults to current repo)
            working_dir: Working directory in sandbox
        """
        self.agent_name = agent_name
        self.repo_url = repo_url or self._get_current_repo_url()
        self.working_dir = working_dir

        # Verify E2B API key
        self.api_key = os.getenv("E2B_API_KEY")
        if not self.api_key:
            raise ValueError(
                "E2B_API_KEY not found in environment. "
                "Get your key at https://e2b.dev/dashboard and add to .env"
            )

        # Track active sandboxes
        self.active_sandboxes: Dict[str, Sandbox] = {}
        self.sandbox_info: Dict[str, SandboxInfo] = {}

        # Initialize failure knowledge base for reflection (Phase 1.5)
        self.knowledge_base = None
        if FailureKnowledgeBase:
            try:
                self.knowledge_base = FailureKnowledgeBase()
                logger.info("Reflection enabled - learning from failures")
            except Exception as e:
                logger.warning(f"Failed to initialize knowledge base: {e}")

        # Initialize model router for tiered routing (Phase 2)
        self.model_router = None
        if ModelRouter:
            try:
                self.model_router = ModelRouter()
                logger.info("Tiered routing enabled - intelligent model selection")
            except Exception as e:
                logger.warning(f"Failed to initialize model router: {e}")

        logger.info(f"SandboxManager initialized for agent: {agent_name}")

    def create_sandbox(
        self,
        feature_id: int,
        timeout: int = 300  # 5 minutes default
    ) -> SandboxInfo:
        """
        Create isolated E2B sandbox for feature development.

        Args:
            feature_id: Feature ID being developed
            timeout: Sandbox timeout in seconds

        Returns:
            SandboxInfo with sandbox details

        Raises:
            Exception: If sandbox creation fails
        """
        start_time = time.time()

        logger.info(f"Creating sandbox for feature {feature_id}...")

        try:
            # Create E2B sandbox using class method
            sandbox = Sandbox.create(api_key=self.api_key)

            # Track sandbox
            sandbox_id = sandbox.sandbox_id
            self.active_sandboxes[sandbox_id] = sandbox

            # Create sandbox info
            info = SandboxInfo(
                sandbox_id=sandbox_id,
                feature_id=feature_id,
                created_at=datetime.now().isoformat(),
                status="created",
                repo_path=str(self.working_dir)
            )

            self.sandbox_info[sandbox_id] = info

            elapsed = time.time() - start_time
            logger.info(
                f"✅ Sandbox {sandbox_id[:8]} created for feature {feature_id} "
                f"({elapsed:.1f}s)"
            )

            return info

        except Exception as e:
            logger.error(f"❌ Failed to create sandbox for feature {feature_id}: {e}")
            raise

    def setup_environment(self, sandbox_info: SandboxInfo) -> bool:
        """
        Set up sandbox environment (clone repo, install dependencies).

        Args:
            sandbox_info: Sandbox to set up

        Returns:
            True if setup succeeded, False otherwise
        """
        sandbox = self.active_sandboxes.get(sandbox_info.sandbox_id)
        if not sandbox:
            logger.error(f"Sandbox {sandbox_info.sandbox_id} not found")
            return False

        logger.info(f"Setting up environment in sandbox {sandbox_info.sandbox_id[:8]}...")

        try:
            # Clone repository
            logger.info(f"Cloning repo: {self.repo_url}")

            # Use code interpreter to run setup commands
            result = sandbox.run_code(f"""
import subprocess
import os

# Clone repository
subprocess.run([
    'git', 'clone', '{self.repo_url}', '{self.working_dir}'
], check=True)

# Change to repo directory
os.chdir('{self.working_dir}')

# Install dependencies (if requirements.txt exists)
if os.path.exists('requirements/base.txt'):
    subprocess.run([
        'pip', 'install', '-r', 'requirements/base.txt'
    ], check=True)

print("Environment setup complete")
""")

            if result.error:
                logger.error(f"Setup failed: {result.error}")
                sandbox_info.status = "failed"
                sandbox_info.error = str(result.error)
                return False

            logger.info(f"✅ Environment setup complete")
            return True

        except Exception as e:
            logger.error(f"❌ Environment setup failed: {e}")
            sandbox_info.status = "failed"
            sandbox_info.error = str(e)
            return False

    def execute_feature(
        self,
        sandbox_info: SandboxInfo,
        feature_context: Dict[str, Any]
    ) -> bool:
        """
        Execute feature development in sandbox.

        Args:
            sandbox_info: Sandbox to execute in
            feature_context: Context for feature (description, validation, etc.)

        Returns:
            True if execution succeeded, False otherwise
        """
        sandbox = self.active_sandboxes.get(sandbox_info.sandbox_id)
        if not sandbox:
            logger.error(f"Sandbox {sandbox_info.sandbox_id} not found")
            return False

        feature_id = feature_context.get("feature_id", sandbox_info.feature_id)
        feature_desc = feature_context.get("feature_description", "")[:60]

        logger.info(
            f"Executing feature {feature_id} in sandbox {sandbox_info.sandbox_id[:8]}: "
            f"{feature_desc}..."
        )

        sandbox_info.status = "running"
        start_time = time.time()

        # Phase 2: Classify task and select appropriate model tier
        if self.model_router:
            feature_desc = feature_context.get("feature_description", "")
            model_tier = self.model_router.classify_request(
                task=feature_desc,
                agent=self.agent_name
            )
            model_id = self.model_router.get_model_id(model_tier)
            cost_per_query = self.model_router.get_cost_per_query(model_tier)

            feature_context["model_info"] = {
                "tier": model_tier.value,
                "model_id": model_id,
                "cost_per_query": cost_per_query
            }

            logger.info(
                f"🤖 Model selected: {model_tier.value.upper()} "
                f"({model_id}) - ${cost_per_query:.3f}/query"
            )

        # Phase 1.5: Retrieve relevant learnings BEFORE execution
        learned_patterns = []
        if self.knowledge_base:
            feature_desc = feature_context.get("feature_description", "")
            learned_patterns = self.knowledge_base.get_relevant_learnings(
                agent_name=self.agent_name,
                feature_desc=feature_desc
            )

            if learned_patterns:
                logger.info(
                    f"📚 Found {len(learned_patterns)} relevant patterns to avoid"
                )
                # Add to context
                feature_context["learned_patterns"] = [
                    {
                        "error_type": p.error_type,
                        "pattern": p.error_pattern,
                        "learnings": p.learnings,
                        "suggestions": p.suggestions
                    }
                    for p in learned_patterns
                ]

        try:
            # Build execution script with learned patterns
            exec_script = self._build_execution_script(feature_context)

            # Execute in sandbox
            result = sandbox.run_code(exec_script)

            elapsed = time.time() - start_time
            sandbox_info.execution_time = elapsed

            # Check result
            if result.error:
                logger.error(
                    f"❌ Feature {feature_id} execution failed: {result.error}"
                )
                sandbox_info.status = "failed"
                sandbox_info.error = str(result.error)

                # Phase 1.5: Analyze and store failure pattern
                if self.knowledge_base:
                    self._analyze_and_store_failure(
                        result=result,
                        feature_id=feature_id,
                        feature_context=feature_context
                    )

                return False

            # Validate output
            success = self._validate_execution(result, feature_context)

            if success:
                logger.info(
                    f"✅ Feature {feature_id} completed successfully ({elapsed:.1f}s)"
                )
                sandbox_info.status = "completed"
            else:
                logger.warning(
                    f"⚠️  Feature {feature_id} completed with validation errors"
                )
                sandbox_info.status = "failed"

            return success

        except Exception as e:
            elapsed = time.time() - start_time
            sandbox_info.execution_time = elapsed

            logger.error(f"❌ Feature {feature_id} execution error: {e}")
            sandbox_info.status = "failed"
            sandbox_info.error = str(e)
            return False

    def _build_execution_script(self, feature_context: Dict[str, Any]) -> str:
        """
        Build Python script to execute in sandbox.

        Args:
            feature_context: Feature context with description, validation steps

        Returns:
            Python script to execute
        """
        feature_desc = feature_context.get("feature_description", "")
        validation_steps = feature_context.get("validation_steps", [])
        learned_patterns = feature_context.get("learned_patterns", [])

        script = f"""
import os
import subprocess
import sys
from pathlib import Path

# Feature context
feature_description = '''{feature_desc}'''
validation_steps = {validation_steps}
learned_patterns = {learned_patterns}

# Change to repo directory
os.chdir('{self.working_dir}')

# Print context
print("=" * 70)
print("Feature Development Session")
print("=" * 70)
print(f"Feature: {{feature_description}}")
print(f"Validation steps: {{len(validation_steps)}}")
print(f"Learned patterns: {{len(learned_patterns)}}")
print("=" * 70)
print()

# TODO: Implement feature development logic
# This is a placeholder - actual implementation would:
# 1. Parse feature description
# 2. Generate code using Claude API
# 3. Write tests
# 4. Run validation steps
# 5. Return success/failure

# For now, just validate repo exists
if not Path('{self.working_dir}').exists():
    raise Exception("Repository not found")

print("✅ Feature development placeholder executed")
"""

        return script

    def _validate_execution(
        self,
        result: Any,
        feature_context: Dict[str, Any]
    ) -> bool:
        """
        Validate execution result.

        Args:
            result: Execution result from sandbox
            feature_context: Feature context

        Returns:
            True if validation passed, False otherwise
        """
        # Check for errors
        if result.error:
            return False

        # Check output from logs
        if hasattr(result, 'logs') and result.logs:
            stdout = "".join(result.logs.stdout)
            # Basic validation: check for success indicator
            if "✅" in stdout or "success" in stdout.lower():
                return True

        return False

    def _analyze_and_store_failure(
        self,
        result: Any,
        feature_id: int,
        feature_context: Dict[str, Any]
    ) -> None:
        """
        Analyze failure and store pattern in knowledge base.

        Args:
            result: Failed execution result
            feature_id: Feature that failed
            feature_context: Feature context
        """
        if not self.knowledge_base or not result.error:
            return

        # Extract error information
        error_info = self._extract_error_info(result)

        if not error_info:
            return

        # Store failure pattern
        try:
            pattern = self.knowledge_base.store_failure(
                feature_id=feature_id,
                agent_name=self.agent_name,
                error_type=error_info["error_type"],
                error_pattern=error_info["error_pattern"],
                affected_module=error_info["affected_module"],
                learnings=error_info["learnings"],
                suggestions=error_info["suggestions"],
                context={
                    "feature_desc": feature_context.get("feature_description", ""),
                    "validation_steps": feature_context.get("validation_steps", [])
                }
            )

            logger.info(
                f"💡 Stored failure pattern: {error_info['error_type']} "
                f"(frequency: {pattern.frequency})"
            )

        except Exception as e:
            logger.error(f"Failed to store failure pattern: {e}")

    def _extract_error_info(self, result: Any) -> Optional[Dict[str, Any]]:
        """
        Extract structured error information from result.

        Args:
            result: Execution result with error

        Returns:
            Dictionary with error info or None
        """
        if not result.error:
            return None

        error_str = str(result.error)

        # Pattern matching for common errors
        error_patterns = {
            "ImportError": {
                "regex": r"(?:ImportError|ModuleNotFoundError): No module named ['\"](\w+)['\"]",
                "learnings_template": lambda m: [f"Module '{m.group(1)}' must be installed"],
                "suggestions_template": lambda m: [f"Add '{m.group(1)}' to requirements.txt"]
            },
            "TestFailure": {
                "regex": r"FAILED (.*?) - (AssertionError|ValueError): (.*)",
                "learnings_template": lambda m: [f"Test failed: {m.group(3)[:100]}"],
                "suggestions_template": lambda m: ["Review test expectations", "Check test data setup"]
            },
            "TimeoutError": {
                "regex": r"TimeoutError: .* exceeded (\d+)s",
                "learnings_template": lambda m: [f"Operation needs more than {m.group(1)}s"],
                "suggestions_template": lambda m: [f"Increase timeout to {int(m.group(1)) * 2}s"]
            },
            "AttributeError": {
                "regex": r"AttributeError: .* has no attribute ['\"](\w+)['\"]",
                "learnings_template": lambda m: [f"Missing attribute: {m.group(1)}"],
                "suggestions_template": lambda m: [f"Check object initialization", f"Verify {m.group(1)} exists"]
            },
            "KeyError": {
                "regex": r"KeyError: ['\"](\w+)['\"]",
                "learnings_template": lambda m: [f"Missing key: {m.group(1)}"],
                "suggestions_template": lambda m: [f"Add default value for '{m.group(1)}'", "Use .get() method"]
            }
        }

        # Try to match error patterns
        for error_type, config in error_patterns.items():
            match = re.search(config["regex"], error_str)
            if match:
                return {
                    "error_type": error_type,
                    "error_pattern": match.group(0),
                    "affected_module": "unknown",  # Could be extracted from traceback
                    "learnings": config["learnings_template"](match),
                    "suggestions": config["suggestions_template"](match)
                }

        # Generic error if no pattern matched
        return {
            "error_type": "UnknownError",
            "error_pattern": error_str[:200],  # First 200 chars
            "affected_module": "unknown",
            "learnings": ["Unrecognized error pattern"],
            "suggestions": ["Review full error logs", "Add specific error handling"]
        }

    def extract_results(self, sandbox_info: SandboxInfo) -> Dict[str, Any]:
        """
        Extract results and artifacts from sandbox.

        Args:
            sandbox_info: Sandbox to extract from

        Returns:
            Dictionary with results, logs, artifacts
        """
        sandbox = self.active_sandboxes.get(sandbox_info.sandbox_id)
        if not sandbox:
            logger.error(f"Sandbox {sandbox_info.sandbox_id} not found")
            return {"error": "Sandbox not found"}

        logger.info(f"Extracting results from sandbox {sandbox_info.sandbox_id[:8]}...")

        try:
            results = {
                "sandbox_id": sandbox_info.sandbox_id,
                "feature_id": sandbox_info.feature_id,
                "status": sandbox_info.status,
                "execution_time": sandbox_info.execution_time,
                "error": sandbox_info.error,
                "artifacts": [],
                "logs": []
            }

            # TODO: Extract actual artifacts
            # - Generated code files
            # - Test results
            # - Coverage reports
            # - Logs

            logger.info(f"✅ Results extracted from sandbox {sandbox_info.sandbox_id[:8]}")

            return results

        except Exception as e:
            logger.error(f"❌ Failed to extract results: {e}")
            return {"error": str(e)}

    def cleanup_sandbox(self, sandbox_info: SandboxInfo) -> bool:
        """
        Terminate sandbox and cleanup resources.

        Args:
            sandbox_info: Sandbox to cleanup

        Returns:
            True if cleanup succeeded, False otherwise
        """
        sandbox = self.active_sandboxes.get(sandbox_info.sandbox_id)
        if not sandbox:
            logger.warning(f"Sandbox {sandbox_info.sandbox_id} already cleaned up")
            return True

        logger.info(f"Cleaning up sandbox {sandbox_info.sandbox_id[:8]}...")

        try:
            # Terminate sandbox
            sandbox.kill()

            # Remove from tracking
            del self.active_sandboxes[sandbox_info.sandbox_id]

            # Update status
            sandbox_info.status = "terminated"

            logger.info(f"✅ Sandbox {sandbox_info.sandbox_id[:8]} cleaned up")
            return True

        except Exception as e:
            logger.error(f"❌ Cleanup failed for {sandbox_info.sandbox_id[:8]}: {e}")
            return False

    def cleanup_all(self) -> None:
        """Cleanup all active sandboxes."""
        logger.info(f"Cleaning up {len(self.active_sandboxes)} active sandboxes...")

        for sandbox_id in list(self.active_sandboxes.keys()):
            info = self.sandbox_info.get(sandbox_id)
            if info:
                self.cleanup_sandbox(info)

        logger.info("✅ All sandboxes cleaned up")

    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about sandbox usage.

        Returns:
            Dictionary with usage statistics
        """
        total = len(self.sandbox_info)
        active = len(self.active_sandboxes)

        status_counts = {}
        for info in self.sandbox_info.values():
            status_counts[info.status] = status_counts.get(info.status, 0) + 1

        avg_exec_time = None
        exec_times = [
            info.execution_time
            for info in self.sandbox_info.values()
            if info.execution_time
        ]
        if exec_times:
            avg_exec_time = sum(exec_times) / len(exec_times)

        return {
            "total_sandboxes": total,
            "active_sandboxes": active,
            "status_counts": status_counts,
            "avg_execution_time": avg_exec_time
        }

    def get_routing_stats(self) -> Dict[str, Any]:
        """
        Get model routing statistics (Phase 2).

        Returns:
            Dictionary with routing stats including:
            - Distribution by tier (haiku/sonnet/opus)
            - Cost savings vs baseline
            - Average cost per query
        """
        if not self.model_router:
            return {
                "error": "Model router not available",
                "total_requests": 0
            }

        return self.model_router.get_routing_stats()

    def estimate_cost_savings(self, baseline_tier: str = "sonnet") -> Dict[str, float]:
        """
        Estimate cost savings from tiered routing (Phase 2).

        Args:
            baseline_tier: Baseline model to compare against ('haiku', 'sonnet', 'opus')

        Returns:
            Cost savings breakdown
        """
        if not self.model_router or not ModelTierEnum:
            return {
                "error": "Model router not available",
                "baseline_cost": 0.0,
                "actual_cost": 0.0,
                "savings": 0.0,
                "savings_percentage": 0.0
            }

        baseline_enum = ModelTierEnum(baseline_tier)
        return self.model_router.estimate_cost_savings(baseline_enum)

    def _get_current_repo_url(self) -> str:
        """Get current git repository URL."""
        try:
            import subprocess
            result = subprocess.run(
                ['git', 'config', '--get', 'remote.origin.url'],
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout.strip()
        except:
            # Default to local path if not a git repo
            return str(Path.cwd().absolute())


if __name__ == "__main__":
    # Example usage
    from dotenv import load_dotenv
    load_dotenv()

    print("SandboxManager - E2B Integration for Parallel Agent Builds")
    print("=" * 70)
    print()

    # Initialize manager
    manager = SandboxManager(agent_name="test_agent")

    try:
        # Create sandbox
        print("Creating sandbox...")
        sandbox_info = manager.create_sandbox(feature_id=1)
        print(f"Sandbox ID: {sandbox_info.sandbox_id}")
        print(f"Status: {sandbox_info.status}")
        print()

        # Setup environment
        print("Setting up environment...")
        if manager.setup_environment(sandbox_info):
            print("✅ Environment ready")
        else:
            print("❌ Environment setup failed")
            exit(1)
        print()

        # Execute feature
        print("Executing feature...")
        feature_context = {
            "feature_id": 1,
            "feature_description": "Test feature development",
            "validation_steps": ["Run tests", "Check coverage"],
            "learned_patterns": []
        }

        if manager.execute_feature(sandbox_info, feature_context):
            print("✅ Feature execution completed")
        else:
            print("❌ Feature execution failed")
        print()

        # Extract results
        print("Extracting results...")
        results = manager.extract_results(sandbox_info)
        print(f"Results: {json.dumps(results, indent=2)}")
        print()

        # Get stats
        print("Sandbox statistics:")
        stats = manager.get_stats()
        print(json.dumps(stats, indent=2))
        print()

        # Phase 2: Show routing statistics
        print("=" * 70)
        print("MODEL ROUTING STATISTICS (Phase 2)")
        print("=" * 70)
        routing_stats = manager.get_routing_stats()

        if "error" not in routing_stats and routing_stats.get('total_requests', 0) > 0:
            print(f"\nTotal requests: {routing_stats['total_requests']}")
            print("\nDistribution by tier:")
            for tier, percentage in routing_stats['tier_percentages'].items():
                count = routing_stats['by_tier'][tier]
                target = routing_stats['target_distribution'][tier]
                print(f"  {tier.upper():6} {count:2} requests ({percentage:5.1f}%) [target: {target}%]")

            print(f"\nAverage cost: ${routing_stats['average_cost']:.3f}/query")

            # Show cost savings
            savings = manager.estimate_cost_savings()
            if "error" not in savings and savings['savings'] > 0:
                print(f"\nCost savings vs all-Sonnet baseline:")
                print(f"  Baseline: ${savings['baseline_cost']:.2f}")
                print(f"  Actual:   ${savings['actual_cost']:.2f}")
                print(f"  Savings:  ${savings['savings']:.2f} ({savings['savings_percentage']:.1f}%)")
        else:
            print("\n(No routing data yet - run some tasks first)")
        print()

    finally:
        # Cleanup
        print("Cleaning up...")
        manager.cleanup_all()
        print("✅ Done")
