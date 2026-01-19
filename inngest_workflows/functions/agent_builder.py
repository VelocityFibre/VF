"""
Agent Harness integration with Inngest for durable agent building

This module wraps the Agent Harness in Inngest functions to provide:
- Pause/resume capability for overnight builds
- Automatic retry on failures
- Progress tracking and monitoring
- Checkpoint recovery
"""

import os
import sys
import json
import subprocess
from datetime import datetime
from typing import Dict, Any, Optional, List
from pathlib import Path

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from inngest import Inngest, Function, TriggerEvent
from client import inngest_client, Events, InngestConfig

# Harness configuration
HARNESS_DIR = Path("harness")
SPECS_DIR = HARNESS_DIR / "specs"
RUNS_DIR = HARNESS_DIR / "runs"

@inngest_client.create_function(
    fn_id="build-agent",
    trigger=TriggerEvent(event=Events.AGENT_BUILD_REQUESTED),
    concurrency=[{
        "limit": InngestConfig.AGENT_BUILD_CONCURRENCY,
        "key": "event.data.agent_name"  # One build per agent
    }],
    # timeout="24h"  # TODO: Configure timeouts properly
)
async def build_agent_with_harness(ctx, step):
    """
    Build a complete agent using the Agent Harness with durability.

    This function orchestrates 50-100 Claude sessions to build
    an agent overnight, with full pause/resume capability.

    Event data should contain:
        - agent_name: Name of the agent to build
        - spec_path: Optional path to spec file (defaults to specs/[agent_name]_spec.md)
        - model: Optional model to use (defaults to haiku)
        - resume: Optional flag to resume from existing run
    """

    agent_name = ctx.event.data.get("agent_name")
    spec_path = ctx.event.data.get("spec_path")
    model = ctx.event.data.get("model", "haiku")
    resume = ctx.event.data.get("resume", False)

    if not agent_name:
        raise ValueError("agent_name is required")

    # Step 1: Validate spec exists
    spec_file = await step.run(
        "validate-spec",
        lambda: _validate_spec(agent_name, spec_path)
    )

    if not spec_file:
        raise Exception(f"No spec found for agent {agent_name}")

    # Step 2: Initialize or resume run
    run_data = await step.run(
        "initialize-run",
        lambda: _initialize_harness_run(agent_name, spec_file, resume)
    )

    # Step 3: Run initializer agent (if new build)
    if not resume:
        init_result = await step.run(
            "run-initializer",
            lambda: _run_initializer_agent(agent_name, spec_file, run_data["run_dir"]),
            timeout="30m",
            retry={"attempts": 2, "delay": "2m"}
        )

        # Send progress event
        await step.send_event(
            "notify-init-complete",
            {
                "name": Events.AGENT_BUILD_STARTED,
                "data": {
                    "agent_name": agent_name,
                    "features_total": init_result.get("total_features", 0),
                    "run_id": run_data["run_id"]
                }
            }
        )

    # Step 4: Load feature list
    features = await step.run(
        "load-features",
        lambda: _load_feature_list(run_data["run_dir"])
    )

    if not features:
        raise Exception("No features found in feature_list.json")

    # Step 5: Run coding sessions for each incomplete feature
    completed_features = 0
    total_features = len(features)

    for i, feature in enumerate(features):
        if feature.get("passes", False):
            completed_features += 1
            continue  # Skip completed features

        # Run coding session for this feature
        session_result = await step.run(
            f"coding-session-{feature['id']}",
            lambda: _run_coding_session(
                agent_name,
                run_data["run_dir"],
                feature,
                i + 1
            ),
            timeout="45m",
            retry={"attempts": 2, "delay": "5m"}
        )

        if session_result.get("success"):
            completed_features += 1

            # Send progress event
            await step.send_event(
                f"notify-feature-{feature['id']}",
                {
                    "name": Events.AGENT_FEATURE_COMPLETED,
                    "data": {
                        "agent_name": agent_name,
                        "feature_id": feature["id"],
                        "feature_description": feature["description"],
                        "progress": f"{completed_features}/{total_features}",
                        "percentage": int((completed_features / total_features) * 100)
                    }
                }
            )

        # Add delay between sessions to avoid rate limits
        if completed_features < total_features:
            await step.sleep(f"session-delay-{i}", "30s")

        # Checkpoint every 10 features
        if completed_features % 10 == 0:
            await step.run(
                f"checkpoint-{completed_features}",
                lambda: _create_checkpoint(agent_name, run_data["run_dir"], completed_features)
            )

    # Step 6: Finalize build
    final_result = await step.run(
        "finalize-build",
        lambda: _finalize_agent_build(agent_name, run_data["run_dir"])
    )

    # Step 7: Run tests
    test_results = await step.run(
        "run-tests",
        lambda: _run_agent_tests(agent_name),
        retry={"attempts": 2}
    )

    # Step 8: Register with orchestrator
    registration = await step.run(
        "register-agent",
        lambda: _register_with_orchestrator(agent_name, final_result)
    )

    # Step 9: Send completion event
    await step.send_event(
        "notify-complete",
        {
            "name": Events.AGENT_BUILD_COMPLETED,
            "data": {
                "agent_name": agent_name,
                "total_features": total_features,
                "completed_features": completed_features,
                "tests_passed": test_results.get("passed", False),
                "registered": registration.get("success", False),
                "run_id": run_data["run_id"],
                "duration_hours": run_data.get("duration_hours", 0)
            }
        }
    )

    return {
        "agent_name": agent_name,
        "status": "completed",
        "features_built": completed_features,
        "tests_passed": test_results.get("passed", False),
        "registered": registration.get("success", False)
    }

@inngest_client.create_function(
    fn_id="resume-agent-build",
    trigger=TriggerEvent(event="agent/build.resume"),
    concurrency=[{"limit": 1}]
)
async def resume_agent_build(ctx, step):
    """Resume a failed or paused agent build from checkpoint."""

    agent_name = ctx.event.data.get("agent_name")
    run_id = ctx.event.data.get("run_id")

    if not agent_name:
        raise ValueError("agent_name is required")

    # Find the run directory
    run_dir = await step.run(
        "find-run",
        lambda: _find_run_directory(agent_name, run_id)
    )

    if not run_dir:
        raise Exception(f"No run found for {agent_name}")

    # Trigger the main build with resume flag
    await step.send_event(
        "trigger-resume",
        {
            "name": Events.AGENT_BUILD_REQUESTED,
            "data": {
                "agent_name": agent_name,
                "resume": True,
                "run_id": run_id
            }
        }
    )

    return {"status": "resumed", "agent_name": agent_name}

# Helper functions
def _validate_spec(agent_name: str, spec_path: Optional[str]) -> Optional[str]:
    """Validate that a spec file exists for the agent."""
    if spec_path:
        spec_file = Path(spec_path)
    else:
        spec_file = SPECS_DIR / f"{agent_name}_spec.md"

    if spec_file.exists():
        return str(spec_file)

    # Also check .claude/specs directory
    alt_spec = Path(f".claude/specs/{agent_name}_spec.md")
    if alt_spec.exists():
        return str(alt_spec)

    return None

def _initialize_harness_run(agent_name: str, spec_file: str, resume: bool) -> Dict[str, Any]:
    """Initialize or resume a harness run."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_id = f"{agent_name}_{timestamp}"

    if resume:
        # Find existing run
        latest_run = RUNS_DIR / "latest"
        if latest_run.exists() and latest_run.is_symlink():
            run_dir = latest_run.resolve()
            run_id = run_dir.name
        else:
            # Find most recent run for this agent
            runs = list(RUNS_DIR.glob(f"{agent_name}_*"))
            if runs:
                run_dir = sorted(runs)[-1]
                run_id = run_dir.name
            else:
                raise Exception(f"No existing run found for {agent_name}")
    else:
        # Create new run directory
        run_dir = RUNS_DIR / run_id
        run_dir.mkdir(parents=True, exist_ok=True)

        # Copy spec to run directory
        import shutil
        shutil.copy(spec_file, run_dir / "spec.md")

        # Create latest symlink
        latest = RUNS_DIR / "latest"
        if latest.exists():
            latest.unlink()
        latest.symlink_to(run_dir)

    return {
        "run_id": run_id,
        "run_dir": str(run_dir),
        "resumed": resume,
        "started": datetime.now().isoformat()
    }

def _run_initializer_agent(agent_name: str, spec_file: str, run_dir: str) -> Dict[str, Any]:
    """Run the initializer agent to generate feature list."""
    try:
        # This would normally invoke Claude Code to generate the feature list
        # For now, we'll create a mock implementation
        feature_list = {
            "agent_name": agent_name,
            "total_features": 50,  # Mock value
            "completed": 0,
            "features": []
        }

        # Generate mock features
        for i in range(50):
            feature_list["features"].append({
                "id": i + 1,
                "category": f"category_{(i // 10) + 1}",
                "description": f"Implement feature {i + 1} for {agent_name}",
                "validation_steps": ["Step 1", "Step 2", "Step 3"],
                "passes": False,
                "dependencies": []
            })

        # Save feature list
        feature_file = Path(run_dir) / "feature_list.json"
        with open(feature_file, "w") as f:
            json.dump(feature_list, f, indent=2)

        return {
            "success": True,
            "total_features": len(feature_list["features"]),
            "feature_file": str(feature_file)
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

def _load_feature_list(run_dir: str) -> List[Dict[str, Any]]:
    """Load the feature list from the run directory."""
    feature_file = Path(run_dir) / "feature_list.json"

    if not feature_file.exists():
        return []

    with open(feature_file, "r") as f:
        data = json.load(f)

    return data.get("features", [])

def _run_coding_session(agent_name: str, run_dir: str, feature: Dict, session_num: int) -> Dict[str, Any]:
    """Run a single coding session for a feature."""
    try:
        # This would normally invoke Claude Code to implement the feature
        # For now, we'll simulate success
        print(f"[Session {session_num}] Implementing feature {feature['id']}: {feature['description']}")

        # Update feature list to mark as complete
        feature_file = Path(run_dir) / "feature_list.json"
        with open(feature_file, "r") as f:
            data = json.load(f)

        for f in data["features"]:
            if f["id"] == feature["id"]:
                f["passes"] = True
                data["completed"] += 1
                break

        with open(feature_file, "w") as f:
            json.dump(data, f, indent=2)

        # Update progress file
        progress_file = Path(run_dir) / "claude_progress.md"
        with open(progress_file, "a") as f:
            f.write(f"\n## Session {session_num}: Feature {feature['id']}\n")
            f.write(f"- Implemented: {feature['description']}\n")
            f.write(f"- Status: ✅ Complete\n")
            f.write(f"- Timestamp: {datetime.now().isoformat()}\n")

        return {
            "success": True,
            "feature_id": feature["id"],
            "session_num": session_num
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "feature_id": feature["id"]
        }

def _create_checkpoint(agent_name: str, run_dir: str, completed_features: int) -> Dict[str, Any]:
    """Create a checkpoint for recovery."""
    checkpoint_file = Path(run_dir) / f"checkpoint_{completed_features}.json"

    checkpoint_data = {
        "agent_name": agent_name,
        "completed_features": completed_features,
        "timestamp": datetime.now().isoformat(),
        "run_dir": run_dir
    }

    with open(checkpoint_file, "w") as f:
        json.dump(checkpoint_data, f, indent=2)

    return {
        "checkpoint_created": str(checkpoint_file),
        "features_completed": completed_features
    }

def _finalize_agent_build(agent_name: str, run_dir: str) -> Dict[str, Any]:
    """Finalize the agent build and prepare for deployment."""
    try:
        # Create final report
        report_file = Path(run_dir) / "HARNESS_REPORT.md"
        with open(report_file, "w") as f:
            f.write(f"# Agent Build Report: {agent_name}\n\n")
            f.write(f"Build completed: {datetime.now().isoformat()}\n")
            f.write(f"Run directory: {run_dir}\n")

        return {
            "success": True,
            "agent_name": agent_name,
            "report": str(report_file)
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

def _run_agent_tests(agent_name: str) -> Dict[str, Any]:
    """Run tests for the built agent."""
    try:
        # Run pytest for the agent
        result = subprocess.run(
            ["./venv/bin/pytest", f"tests/test_{agent_name}.py", "-v"],
            capture_output=True,
            text=True,
            timeout=300
        )

        return {
            "passed": result.returncode == 0,
            "output": result.stdout,
            "errors": result.stderr
        }
    except Exception as e:
        return {
            "passed": False,
            "error": str(e)
        }

def _register_with_orchestrator(agent_name: str, build_result: Dict) -> Dict[str, Any]:
    """Register the agent with the orchestrator."""
    try:
        registry_file = Path("orchestrator/registry.json")

        if registry_file.exists():
            with open(registry_file, "r") as f:
                registry = json.load(f)
        else:
            registry = {"agents": {}}

        # Add or update agent entry
        registry["agents"][agent_name] = {
            "name": agent_name,
            "triggers": [agent_name],  # Default triggers
            "capabilities": ["Generated by Agent Harness"],
            "built": datetime.now().isoformat(),
            "auto_generated": True
        }

        with open(registry_file, "w") as f:
            json.dump(registry, f, indent=2)

        return {
            "success": True,
            "registered": True
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

def _find_run_directory(agent_name: str, run_id: Optional[str]) -> Optional[str]:
    """Find an existing run directory."""
    if run_id:
        run_dir = RUNS_DIR / run_id
        if run_dir.exists():
            return str(run_dir)

    # Find most recent run for agent
    runs = list(RUNS_DIR.glob(f"{agent_name}_*"))
    if runs:
        return str(sorted(runs)[-1])

    return None

# Export functions for registration
agent_builder_functions = [
    build_agent_with_harness,
    resume_agent_build
]