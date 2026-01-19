#!/usr/bin/env python3
"""
FibreFlow Agent Harness Runner

Autonomous long-running agent builder using Claude Agent SDK.
Orchestrates multiple Claude Code sessions to build complete agents.

Based on Anthropic's Coding Agent Harness, adapted for FibreFlow patterns.

Usage:
    # Full auto-run (recommended)
    ./harness/runner.py --agent sharepoint --model haiku

    # Resume interrupted run
    ./harness/runner.py --agent sharepoint --resume

    # Manual control
    ./harness/runner.py --agent sharepoint --session-type initializer
"""

import os
import sys
import json
import argparse
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional

# Load environment variables from .env
from dotenv import load_dotenv

# Import WorktreeManager for isolated builds
from harness.worktree_manager import WorktreeManager, WorkspaceInfo

# Import SessionExecutor for production SDK integration
from harness.session_executor import SessionExecutor

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Load .env file from project root
load_dotenv(project_root / ".env")

# Constants
HARNESS_DIR = project_root / "harness"
PROMPTS_DIR = HARNESS_DIR / "prompts"
SPECS_DIR = HARNESS_DIR / "specs"
RUNS_DIR = HARNESS_DIR / "runs"
CONFIG_FILE = HARNESS_DIR / "config.json"

# Color output
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    END = '\033[0m'
    BOLD = '\033[1m'


def log(message: str, level: str = "INFO"):
    """Log message with timestamp and color"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    colors = {
        "INFO": Colors.BLUE,
        "SUCCESS": Colors.GREEN,
        "WARNING": Colors.YELLOW,
        "ERROR": Colors.RED,
        "HEADER": Colors.HEADER
    }
    color = colors.get(level, Colors.END)
    print(f"{color}[{timestamp}] {level}: {message}{Colors.END}")


def load_config() -> Dict[str, Any]:
    """Load harness configuration"""
    if not CONFIG_FILE.exists():
        log("Config file not found, using defaults", "WARNING")
        return {
            "max_features": 100,
            "session_timeout_minutes": 30,
            "max_sessions": 50,
            "model": {
                "initializer": "claude-sonnet-4.5-20250929",
                "coding_agent": "claude-3-5-haiku-20241022"
            }
        }

    with open(CONFIG_FILE) as f:
        return json.load(f)


def validate_environment() -> bool:
    """Validate FibreFlow environment is ready"""
    log("Validating environment...", "INFO")

    # Check venv
    if "venv" not in sys.executable:
        log("Virtual environment not active! Activate with: source venv/bin/activate", "ERROR")
        return False

    # Check BaseAgent
    try:
        from shared.base_agent import BaseAgent
        log("✓ BaseAgent accessible", "SUCCESS")
    except ImportError:
        log("✗ BaseAgent not found! Check project structure", "ERROR")
        return False

    # Check Claude credentials
    has_token = bool(os.getenv('CLAUDE_TOKEN'))
    has_api_key = bool(os.getenv('ANTHROPIC_API_KEY'))

    if not (has_token or has_api_key):
        log("✗ No Claude credentials! Set CLAUDE_TOKEN or ANTHROPIC_API_KEY", "ERROR")
        return False

    if has_token:
        log("✓ Using Claude subscription token", "SUCCESS")
    else:
        log("✓ Using Anthropic API key", "SUCCESS")

    # Check git
    try:
        subprocess.run(["git", "status"], check=True, capture_output=True)
        log("✓ Git repository initialized", "SUCCESS")
    except subprocess.CalledProcessError:
        log("✗ Not a git repository! Run: git init", "ERROR")
        return False

    return True


def validate_app_spec(agent_name: str) -> bool:
    """Validate app spec exists and is well-formed"""
    spec_file = SPECS_DIR / f"{agent_name}_spec.md"

    if not spec_file.exists():
        log(f"✗ App spec not found: {spec_file}", "ERROR")
        log(f"Create it with: nano {spec_file}", "INFO")
        return False

    # Check spec has required sections
    with open(spec_file) as f:
        content = f.read()

    required_sections = ["Purpose", "Capabilities", "Tools", "Success Criteria"]
    missing = [s for s in required_sections if s not in content]

    if missing:
        log(f"✗ App spec missing sections: {', '.join(missing)}", "WARNING")
        log("Proceeding anyway, but initializer may struggle", "WARNING")

    log(f"✓ App spec found: {spec_file}", "SUCCESS")
    return True


def create_run_directory(agent_name: str, resume: bool = False) -> Path:
    """Create or resume run directory"""
    RUNS_DIR.mkdir(parents=True, exist_ok=True)

    if resume:
        # Find latest run for this agent
        existing_runs = sorted(RUNS_DIR.glob(f"{agent_name}_*"))
        if not existing_runs:
            log(f"✗ No existing run found for {agent_name}", "ERROR")
            sys.exit(1)

        run_dir = existing_runs[-1]
        log(f"Resuming run: {run_dir.name}", "INFO")
        return run_dir

    # Create new run
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = RUNS_DIR / f"{agent_name}_{timestamp}"
    run_dir.mkdir(parents=True, exist_ok=True)

    # Create sessions directory
    (run_dir / "sessions").mkdir(exist_ok=True)

    # Create symlink to latest (use absolute path for worktree compatibility)
    latest_link = RUNS_DIR / "latest"
    if latest_link.exists():
        latest_link.unlink()
    latest_link.symlink_to(run_dir.resolve(), target_is_directory=True)

    log(f"✓ Created run directory: {run_dir.name}", "SUCCESS")
    return run_dir


def load_prompt(session_type: str) -> str:
    """Load prompt for session type"""
    prompt_file = PROMPTS_DIR / f"{session_type}.md"

    if not prompt_file.exists():
        log(f"✗ Prompt not found: {prompt_file}", "ERROR")
        raise FileNotFoundError(f"Prompt file missing: {prompt_file}")

    with open(prompt_file) as f:
        return f.read()


def run_claude_code_session(
    agent_name: str,
    run_dir: Path,
    session_type: str,
    session_number: int,
    model: str,
    timeout_minutes: int = 30
) -> bool:
    """
    Run a single Claude Code session using SessionExecutor.

    Production implementation using Claude CLI for autonomous coding.

    Args:
        agent_name: Name of agent being built
        run_dir: Run directory for this build
        session_type: "initializer" or "coding"
        session_number: Session number (for logging)
        model: Claude model to use
        timeout_minutes: Session timeout

    Returns:
        bool: True if session succeeded, False otherwise
    """
    log(f"Starting Session #{session_number}: {session_type}", "HEADER")

    session_log = run_dir / "sessions" / f"session_{session_number:03d}.log"

    # Load prompt
    try:
        prompt = load_prompt(session_type)
    except FileNotFoundError as e:
        log(str(e), "ERROR")
        return False

    # Prepare context for prompt substitution
    context = {
        "agent_name": agent_name,
        "run_dir": str(run_dir),
        "session_number": session_number,
        "spec_file": str(SPECS_DIR / f"{agent_name}_spec.md"),
        "feature_list": str(run_dir / "feature_list.json"),
        "progress_file": str(run_dir / "claude_progress.md"),
    }

    log(f"Executing Claude Code session...", "INFO")
    log(f"  Model: {model}", "INFO")
    log(f"  Timeout: {timeout_minutes} minutes", "INFO")
    log(f"  Log: {session_log.name}", "INFO")
    log("", "INFO")

    # Execute session using SessionExecutor
    try:
        executor = SessionExecutor(model=model, timeout_minutes=timeout_minutes)
        success = executor.execute_session(
            prompt=prompt,
            context=context,
            session_log=session_log,
            working_dir=Path.cwd()  # Use current directory (may be in worktree)
        )

        if success:
            log(f"✅ Session #{session_number} completed successfully", "SUCCESS")
        else:
            log(f"❌ Session #{session_number} failed", "ERROR")
            log(f"   Check log: {session_log}", "INFO")

        return success

    except Exception as e:
        log(f"❌ Session execution error: {e}", "ERROR")
        return False


def check_progress(run_dir: Path) -> tuple[int, int]:
    """Check feature completion progress"""
    feature_list_file = run_dir / "feature_list.json"

    if not feature_list_file.exists():
        return 0, 0

    with open(feature_list_file) as f:
        data = json.load(f)

    total = data.get("total_features", 0)
    completed = data.get("completed", 0)

    return completed, total


def run_test_suite(agent_name: str) -> bool:
    """Run pytest test suite for agent"""
    test_file = project_root / "tests" / f"test_{agent_name}.py"

    if not test_file.exists():
        log("No tests found yet", "WARNING")
        return True

    log("Running test suite...", "INFO")

    try:
        result = subprocess.run(
            [str(project_root / "venv" / "bin" / "pytest"), str(test_file), "-v"],
            capture_output=True,
            text=True,
            timeout=120
        )

        if result.returncode == 0:
            log("✓ All tests passed", "SUCCESS")
            return True
        else:
            log(f"✗ Tests failed (exit code: {result.returncode})", "ERROR")
            log(result.stdout, "INFO")
            return False

    except subprocess.TimeoutExpired:
        log("✗ Tests timed out", "ERROR")
        return False
    except Exception as e:
        log(f"✗ Error running tests: {e}", "ERROR")
        return False


def generate_final_report(agent_name: str, run_dir: Path, start_time: datetime):
    """Generate final harness execution report"""
    end_time = datetime.now()
    duration = end_time - start_time

    completed, total = check_progress(run_dir)
    progress_pct = (completed / total * 100) if total > 0 else 0

    report = f"""# FibreFlow Agent Harness - Final Report

**Agent**: {agent_name}
**Run ID**: {run_dir.name}
**Started**: {start_time.strftime("%Y-%m-%d %H:%M:%S")}
**Completed**: {end_time.strftime("%Y-%m-%d %H:%M:%S")}
**Duration**: {duration}

## Summary

**Total Features**: {total}
**Completed**: {completed}
**Progress**: {progress_pct:.1f}%
**Status**: {"✅ COMPLETE" if completed == total else "⚠️ INCOMPLETE"}

## Files Generated

```
agents/{agent_name}/
├── __init__.py
├── agent.py
└── README.md

tests/
└── test_{agent_name}.py

demo_{agent_name}.py
```

## Next Steps

{"✅ Agent is ready for testing and deployment!" if completed == total else """
⚠️ Agent is incomplete. To finish:

1. Resume harness: ./harness/runner.py --agent """ + agent_name + """ --resume
2. OR: Complete remaining features manually
3. Check feature_list.json for incomplete features
"""}

## Testing

```bash
# Run tests
./venv/bin/pytest tests/test_{agent_name}.py -v

# Try demo
./venv/bin/python3 demo_{agent_name}.py

# Test via orchestrator
./venv/bin/python3 orchestrator/orchestrator.py
```

## Deployment

```bash
# Deploy to production
/deployment/deploy {agent_name}
```

---

*Generated by FibreFlow Agent Harness v1.0*
*{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}*
"""

    report_file = run_dir / "HARNESS_REPORT.md"
    with open(report_file, 'w') as f:
        f.write(report)

    log(f"✓ Report generated: {report_file}", "SUCCESS")
    return report_file


def main():
    parser = argparse.ArgumentParser(
        description="FibreFlow Agent Harness - Autonomous Agent Builder"
    )
    parser.add_argument("--agent", required=True, help="Agent name to build")
    parser.add_argument("--model", choices=["haiku", "sonnet", "opus"],
                       default="haiku", help="Model to use (default: haiku)")
    parser.add_argument("--session-type", choices=["initializer", "coding"],
                       help="Session type (auto-detect if not specified)")
    parser.add_argument("--max-sessions", type=int, default=50,
                       help="Maximum coding sessions (default: 50)")
    parser.add_argument("--session-timeout", type=int, default=30,
                       help="Session timeout in minutes (default: 30)")
    parser.add_argument("--resume", action="store_true",
                       help="Resume from latest run")
    parser.add_argument("--auto-continue", action="store_true", default=True,
                       help="Auto-run next session (default: true)")
    parser.add_argument("--use-worktree", action="store_true", default=True,
                       help="Use git worktree for isolated build (default: true)")
    parser.add_argument("--no-worktree", dest="use_worktree", action="store_false",
                       help="Disable worktree (commit directly to main)")
    parser.add_argument("--parallel", type=int, metavar="N",
                       help="Enable parallel execution with N workers (Phase 3)")
    parser.add_argument("--no-parallel", dest="parallel", action="store_const", const=0,
                       help="Disable parallel execution (sequential mode)")

    args = parser.parse_args()

    # Banner
    print()
    log("=" * 70, "HEADER")
    log("FibreFlow Agent Harness - Autonomous Agent Builder", "HEADER")
    log("=" * 70, "HEADER")
    print()

    # Validate environment
    if not validate_environment():
        sys.exit(1)

    # Validate app spec
    if not args.resume and not validate_app_spec(args.agent):
        sys.exit(1)

    # Load config
    config = load_config()

    # Create/resume run directory
    run_dir = create_run_directory(args.agent, args.resume)

    # Track start time
    start_time = datetime.now()

    # Determine session type
    if args.resume:
        # Check if initialization is complete
        feature_list = run_dir / "feature_list.json"
        if not feature_list.exists():
            session_type = "initializer"
            session_number = 1
        else:
            session_type = "coding_agent"
            # Count existing sessions
            existing_sessions = len(list((run_dir / "sessions").glob("session_*.log")))
            session_number = existing_sessions + 1
    else:
        session_type = args.session_type or "initializer"
        session_number = 1

    # Model selection
    model_map = {
        "haiku": "claude-3-5-haiku-20241022",
        "sonnet": "claude-sonnet-4.5-20250929",
        "opus": "claude-opus-4-20250514"
    }
    model = model_map[args.model]

    # Check for Phase 3: Parallel Execution
    if args.parallel and args.parallel > 0:
        # Check that feature_list.json exists (initializer must run first)
        feature_list_path = run_dir / "feature_list.json"
        if not feature_list_path.exists():
            log("❌ Parallel mode requires feature_list.json (run initializer first)", "ERROR")
            log("   Run without --parallel first to initialize agent", "INFO")
            sys.exit(1)

        log(f"🚀 Phase 3: Parallel execution enabled ({args.parallel} workers)", "SUCCESS")
        log("", "INFO")

        # Import and run parallel harness
        from harness.parallel_runner import ParallelHarness

        harness = ParallelHarness(
            agent_name=args.agent,
            run_dir=run_dir,
            max_workers=args.parallel,
            enable_rate_limit_handling=True
        )

        try:
            results = harness.run()

            # Generate final report
            report_file = generate_final_report(args.agent, run_dir, start_time)

            # Exit with success/failure based on completion
            if results['failed'] == 0:
                log("✅ All features completed successfully (parallel mode)", "SUCCESS")
                sys.exit(0)
            else:
                log(f"⚠️  {results['failed']} features failed (parallel mode)", "WARNING")
                sys.exit(1)

        except Exception as e:
            log(f"❌ Parallel execution failed: {e}", "ERROR")
            sys.exit(1)

    # Sequential execution (original behavior)
    # Setup git worktree for isolated development (Phase 1: Auto-Claude integration)
    workspace = None
    original_cwd = Path.cwd()

    if args.use_worktree:
        log("Setting up isolated git worktree (prevents main branch commits)", "INFO")
        manager = WorktreeManager(agent_name=args.agent)

        try:
            workspace = manager.create_workspace()
            manager.change_to_workspace(workspace)
            log(f"✓ Working in isolated environment: {workspace.branch_name}", "SUCCESS")
        except Exception as e:
            log(f"✗ Worktree setup failed: {e}", "ERROR")
            log("Falling back to direct development on main branch", "WARNING")
            workspace = None
    else:
        log("⚠️ Worktree disabled - commits will go directly to main branch", "WARNING")

    # Wrap session execution in try/finally to ensure worktree cleanup
    try:
        # Run sessions
        if session_type == "initializer":
            # Run initializer once
            log(f"Running initializer for {args.agent}...", "INFO")
            success = run_claude_code_session(
                args.agent, run_dir, "initializer", 1, model,
                args.session_timeout
            )

            if not success:
                log("Initializer failed", "ERROR")
                if workspace:
                    # Cleanup on failure
                    os.chdir(original_cwd)
                    manager.cleanup_workspace(workspace, force=True)
                sys.exit(1)

            session_number = 2
            session_type = "coding_agent"

        # Run coding agents
        if args.auto_continue:
            log("Auto-continue mode: will run until complete", "INFO")

            while session_number <= args.max_sessions:
                # Check progress
                completed, total = check_progress(run_dir)

                if total > 0:
                    progress_pct = completed / total * 100
                    log(f"Progress: {completed}/{total} features ({progress_pct:.1f}%)", "INFO")

                    if completed == total:
                        log("🎉 All features complete!", "SUCCESS")
                        break

                # Run coding session
                success = run_claude_code_session(
                    args.agent, run_dir, "coding_agent", session_number, model,
                    args.session_timeout
                )

                if not success:
                    log(f"Session {session_number} failed", "ERROR")
                    break

                # Run tests
                if session_number % 5 == 0:  # Test every 5 sessions
                    run_test_suite(args.agent)

                session_number += 1

                if session_number > args.max_sessions:
                    log(f"Reached max sessions ({args.max_sessions})", "WARNING")
                    break
        else:
            # Run single session
            run_claude_code_session(
                args.agent, run_dir, session_type, session_number, model,
                args.session_timeout
            )

        # Final test suite
        log("Running final test suite...", "INFO")
        run_test_suite(args.agent)

        # Generate report
        report_file = generate_final_report(args.agent, run_dir, start_time)

    finally:
        # Worktree cleanup and merge (Phase 1: Auto-Claude integration)
        if workspace:
            log("", "INFO")
            log("=" * 70, "INFO")
            log("Git Worktree Cleanup", "HEADER")
            log("=" * 70, "INFO")

            # Check if build was successful
            completed, total = check_progress(run_dir)
            build_successful = (completed == total and total > 0)

            if build_successful:
                log("✅ Build complete - merging to main branch", "SUCCESS")

                # Merge workspace to main
                merge_success = manager.merge_to_main(workspace)

                if merge_success:
                    log("✅ Successfully merged to main branch", "SUCCESS")
                    manager.cleanup_workspace(workspace)
                else:
                    log("⚠️  Merge failed - worktree preserved for manual merge", "WARNING")
                    log(f"Worktree location: {workspace.worktree_path}", "INFO")
                    log(f"Branch: {workspace.branch_name}", "INFO")
            else:
                log("⚠️ Build incomplete - preserving worktree for resume", "WARNING")
                log(f"Worktree location: {workspace.worktree_path}", "INFO")
                log(f"To resume: cd {workspace.worktree_path} && ./harness/runner.py --agent {args.agent} --resume", "INFO")

                # Don't cleanup - user might want to resume

        # Return to original directory
        os.chdir(original_cwd)

    # Summary
    print()
    log("=" * 70, "HEADER")
    log("Harness Execution Complete", "HEADER")
    log("=" * 70, "HEADER")
    log(f"Agent: {args.agent}", "INFO")
    log(f"Run Directory: {run_dir}", "INFO")

    # Report file reference
    if 'report_file' in locals():
        log(f"Report: {report_file}", "INFO")

    completed, total = check_progress(run_dir)
    if completed == total and total > 0:
        log("✅ Agent build complete! Ready for testing.", "SUCCESS")
        if workspace:
            log("✅ Changes merged to main branch", "SUCCESS")
    else:
        log(f"⚠️ Agent incomplete: {completed}/{total} features", "WARNING")
        log("Resume with: ./harness/runner.py --agent " + args.agent + " --resume", "INFO")

    print()


if __name__ == "__main__":
    main()
