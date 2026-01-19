"""
Multi-Agent Convergence Orchestrator

Runs multiple specialized agents in parallel on the same commit for consensus-driven analysis.
This is the heart of Phase 3's collective intelligence system.

Architecture:
    Git Commit → Convergence Orchestrator
                        ↓
            ┌───────────┼───────────┬──────────┐
            ↓           ↓           ↓          ↓
        Critic      Test-Gen    Doc-Writer  Impact
            ↓           ↓           ↓          ↓
            └───────────┴───────────┴──────────┘
                        ↓
                Convergence Layer
                        ↓
                Unified Report
                        ↓
            Proactivity Queue

Convergence Rules:
    - If 2+ agents agree on issue → High confidence
    - If 1 agent finds critical issue → Immediate alert
    - If agents disagree → Human review required
    - Generate unified task list (no duplicates)

Usage:
    from orchestrator.convergence import ConvergenceOrchestrator

    orchestrator = ConvergenceOrchestrator(api_key)
    result = orchestrator.analyze_commit(commit_hash="abc123")

    print(f"Consensus: {result['consensus']}")
    print(f"Tasks: {result['unified_tasks']}")
"""

import os
import asyncio
import subprocess
from datetime import datetime
from typing import Dict, Any, List, Set
from pathlib import Path

# Import agents and shared modules
import sys
project_root = os.path.abspath(os.path.dirname(__file__) + '/..')
sys.path.insert(0, project_root)

# Import agents by loading their modules directly
import importlib.util

def load_agent_module(agent_name: str):
    """Dynamically load agent module."""
    agent_path = os.path.join(project_root, f"agents/{agent_name}/agent.py")
    spec = importlib.util.spec_from_file_location(f"{agent_name}_agent", agent_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

# Load agent modules
code_critic_module = load_agent_module("code-critic")
test_gen_module = load_agent_module("test-generator")
doc_writer_module = load_agent_module("doc-writer")

# Get agent classes
CodeCriticAgent = code_critic_module.CodeCriticAgent
TestGeneratorAgent = test_gen_module.TestGeneratorAgent
DocWriterAgent = doc_writer_module.DocWriterAgent

# Import queue
from shared.confidence import ProactivityQueue


class ConvergenceOrchestrator:
    """Orchestrates multiple agents in parallel for consensus-driven analysis."""

    def __init__(self, anthropic_api_key: str, timeout: int = 30):
        """Initialize convergence orchestrator.

        Args:
            anthropic_api_key: Anthropic API key for agent initialization
            timeout: Timeout in seconds for each agent (default: 30)
        """
        self.api_key = anthropic_api_key
        self.timeout = timeout

        # Initialize queue for storing converged tasks
        self.queue = ProactivityQueue()

    async def analyze_commit(self, commit_hash: str = "HEAD") -> Dict[str, Any]:
        """Analyze a commit using multiple agents in parallel.

        Args:
            commit_hash: Git commit hash to analyze (default: HEAD)

        Returns:
            Dict with convergence results and unified task list
        """
        try:
            # Get commit details
            commit_info = self._get_commit_info(commit_hash)

            if not commit_info["success"]:
                return {
                    "success": False,
                    "error": commit_info.get("error")
                }

            # Run agents in parallel
            print(f"Running multi-agent analysis on commit {commit_hash[:7]}...")
            print()

            agent_results = await self._run_agents_parallel(
                commit_hash=commit_hash,
                files_changed=commit_info["files_changed"]
            )

            # Analyze convergence
            convergence = self._analyze_convergence(agent_results)

            # Generate unified task list
            unified_tasks = self._generate_unified_tasks(
                agent_results=agent_results,
                convergence=convergence
            )

            # Add tasks to proactivity queue
            for task in unified_tasks:
                self.queue.add_task(
                    task_type=task["type"],
                    description=task["description"],
                    file=task["file"],
                    line=task.get("line"),
                    context={
                        "confidence": task["confidence"],
                        "auto_fixable": task["auto_fixable"],
                        "risk_level": task["risk_level"],
                        "source": task["source"]
                    }
                )

            return {
                "success": True,
                "commit_hash": commit_hash,
                "commit_message": commit_info["message"],
                "files_changed": len(commit_info["files_changed"]),
                "agents_run": len(agent_results),
                "agents_succeeded": sum(1 for r in agent_results.values() if r["success"]),
                "agent_results": agent_results,
                "convergence": convergence,
                "unified_tasks": unified_tasks,
                "tasks_added_to_queue": len(unified_tasks)
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Convergence analysis failed: {str(e)}"
            }

    async def _run_agents_parallel(self, commit_hash: str, files_changed: List[str]) -> Dict[str, Dict[str, Any]]:
        """Run all agents in parallel with timeout.

        Args:
            commit_hash: Commit to analyze
            files_changed: List of modified files

        Returns:
            Dict mapping agent name to result
        """
        # Create agent tasks
        tasks = {
            "critic": self._run_critic_agent(commit_hash),
            "test_gen": self._run_test_gen_agent(files_changed),
            "doc_writer": self._run_doc_writer_agent(files_changed)
            # Impact analyzer will be added in next component
        }

        # Run all agents concurrently with timeout
        results = {}

        for agent_name, task in tasks.items():
            try:
                print(f"Starting {agent_name} agent...")

                result = await asyncio.wait_for(task, timeout=self.timeout)

                results[agent_name] = {
                    "success": True,
                    "data": result,
                    "agent": agent_name
                }

                print(f"✓ {agent_name} completed")

            except asyncio.TimeoutError:
                results[agent_name] = {
                    "success": False,
                    "error": f"Agent timed out after {self.timeout}s",
                    "agent": agent_name
                }

                print(f"✗ {agent_name} timed out")

            except Exception as e:
                results[agent_name] = {
                    "success": False,
                    "error": str(e),
                    "agent": agent_name
                }

                print(f"✗ {agent_name} failed: {str(e)}")

        print()

        return results

    async def _run_critic_agent(self, commit_hash: str) -> Dict[str, Any]:
        """Run code critic agent on commit.

        Args:
            commit_hash: Commit to review

        Returns:
            Critic analysis results
        """
        # Run in executor to avoid blocking
        loop = asyncio.get_event_loop()

        def run_critic():
            critic = CodeCriticAgent(self.api_key)
            return critic._review_commit(
                commit_hash=commit_hash,
                review_types=["security", "performance", "best_practices"]
            )

        return await loop.run_in_executor(None, run_critic)

    async def _run_test_gen_agent(self, files_changed: List[str]) -> Dict[str, Any]:
        """Run test generator agent on changed files.

        Args:
            files_changed: List of modified files

        Returns:
            Test generation analysis
        """
        loop = asyncio.get_event_loop()

        def run_test_gen():
            test_gen = TestGeneratorAgent(self.api_key)

            # Scan Python files for untested functions
            results = []

            for file_path in files_changed:
                if file_path.endswith('.py'):
                    scan = test_gen._scan_for_untested_functions(file_path)

                    if scan["success"] and scan["untested"]:
                        results.append({
                            "file": file_path,
                            "untested_count": scan["untested_functions"],
                            "untested": scan["untested"][:5],  # First 5
                            "coverage": scan["coverage_percent"]
                        })

            return {
                "files_scanned": len([f for f in files_changed if f.endswith('.py')]),
                "files_with_gaps": len(results),
                "results": results
            }

        return await loop.run_in_executor(None, run_test_gen)

    async def _run_doc_writer_agent(self, files_changed: List[str]) -> Dict[str, Any]:
        """Run doc writer agent on changed files.

        Args:
            files_changed: List of modified files

        Returns:
            Documentation analysis
        """
        loop = asyncio.get_event_loop()

        def run_doc_writer():
            doc_writer = DocWriterAgent(self.api_key)

            # Scan Python files for missing docstrings
            results = []

            for file_path in files_changed:
                if file_path.endswith('.py'):
                    scan = doc_writer._scan_for_missing_docstrings(file_path)

                    if scan["success"] and (scan["missing"] or scan["incomplete"]):
                        results.append({
                            "file": file_path,
                            "missing_count": scan["missing_docstrings"],
                            "incomplete_count": scan["incomplete_docstrings"],
                            "missing": scan["missing"][:5],  # First 5
                            "coverage": scan["coverage_percent"]
                        })

            return {
                "files_scanned": len([f for f in files_changed if f.endswith('.py')]),
                "files_with_gaps": len(results),
                "results": results
            }

        return await loop.run_in_executor(None, run_doc_writer)

    def _analyze_convergence(self, agent_results: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze convergence across agent results.

        Args:
            agent_results: Results from all agents

        Returns:
            Convergence analysis
        """
        # Count agreements
        issues_by_file: Dict[str, List[str]] = {}  # file -> [agent_name]

        for agent_name, result in agent_results.items():
            if not result["success"]:
                continue

            data = result["data"]

            # Extract files with issues
            files_with_issues = set()

            if agent_name == "critic":
                # Critic: extract files from issues
                issues_list = data.get("issues", [])

                if isinstance(issues_list, list):
                    for issue in issues_list:
                        if isinstance(issue, dict):
                            files_with_issues.add(issue.get("file", "unknown"))

            elif agent_name == "test_gen":
                # Test-gen: files with untested functions
                for file_result in data.get("results", []):
                    files_with_issues.add(file_result["file"])

            elif agent_name == "doc_writer":
                # Doc-writer: files with missing docs
                for file_result in data.get("results", []):
                    files_with_issues.add(file_result["file"])

            # Track agreements
            for file_path in files_with_issues:
                if file_path not in issues_by_file:
                    issues_by_file[file_path] = []

                issues_by_file[file_path].append(agent_name)

        # Find consensus (2+ agents agree)
        consensus_files = {
            file_path: agents
            for file_path, agents in issues_by_file.items()
            if len(agents) >= 2
        }

        # Find critical issues (any agent found critical)
        critical_issues = []

        if "critic" in agent_results and agent_results["critic"]["success"]:
            critic_data = agent_results["critic"]["data"]

            for issue in critic_data.get("issues", []):
                if issue.get("severity") == "critical":
                    critical_issues.append(issue)

        return {
            "total_files_flagged": len(issues_by_file),
            "consensus_files": len(consensus_files),
            "consensus_details": consensus_files,
            "critical_issues": len(critical_issues),
            "critical_details": critical_issues,
            "requires_human_review": len(critical_issues) > 0
        }

    def _generate_unified_tasks(self, agent_results: Dict[str, Dict[str, Any]], convergence: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate unified task list from agent results.

        Args:
            agent_results: Results from all agents
            convergence: Convergence analysis

        Returns:
            List of unified tasks (no duplicates)
        """
        tasks = []
        seen_tasks: Set[str] = set()  # For deduplication

        # Add critical issues first (highest priority)
        for issue in convergence["critical_details"]:
            task_key = f"{issue['file']}:{issue.get('line', 0)}:{issue['type']}"

            if task_key not in seen_tasks:
                tasks.append({
                    "type": "security_critical",
                    "description": issue["description"],
                    "file": issue["file"],
                    "line": issue.get("line"),
                    "confidence": "high",
                    "auto_fixable": False,  # Critical issues need human review
                    "risk_level": "critical",
                    "source": "code_critic",
                    "priority": "critical"
                })

                seen_tasks.add(task_key)

        # Add consensus issues (2+ agents agree)
        for file_path, agents in convergence["consensus_details"].items():
            # Aggregate issues from agreeing agents
            for agent_name in agents:
                if agent_name not in agent_results or not agent_results[agent_name]["success"]:
                    continue

                data = agent_results[agent_name]["data"]

                if agent_name == "critic":
                    # Add critic issues for this file
                    issues_list = data.get("issues", [])

                    if isinstance(issues_list, list):
                        for issue in issues_list:
                            if not isinstance(issue, dict):
                                continue

                            if issue.get("file") == file_path:
                                issue_type = issue.get("type", "code_quality")
                                task_key = f"{file_path}:{issue.get('line', 0)}:{issue_type}"

                                if task_key not in seen_tasks:
                                    tasks.append({
                                        "type": issue_type,
                                        "description": issue.get("description", "Code quality issue"),
                                        "file": file_path,
                                        "line": issue.get("line"),
                                        "confidence": "high",  # Consensus = high confidence
                                        "auto_fixable": issue.get("severity") in ["low", "medium"],
                                        "risk_level": issue.get("severity", "medium"),
                                        "source": "multi_agent_consensus",
                                        "agents_agree": len(agents)
                                    })

                                    seen_tasks.add(task_key)

                elif agent_name == "test_gen":
                    # Add test generation tasks
                    for file_result in data.get("results", []):
                        if file_result["file"] == file_path:
                            for func in file_result["untested"][:3]:  # Top 3
                                task_key = f"{file_path}:{func['line']}:missing_test"

                                if task_key not in seen_tasks:
                                    tasks.append({
                                        "type": "test_coverage",
                                        "description": f"Generate tests for {func['name']}()",
                                        "file": file_path,
                                        "line": func["line"],
                                        "confidence": "high" if len(agents) >= 2 else "medium",
                                        "auto_fixable": True,
                                        "risk_level": "low",
                                        "source": "test_gen",
                                        "function_name": func["name"]
                                    })

                                    seen_tasks.add(task_key)

                elif agent_name == "doc_writer":
                    # Add documentation tasks
                    for file_result in data.get("results", []):
                        if file_result["file"] == file_path:
                            for func in file_result["missing"][:3]:  # Top 3
                                task_key = f"{file_path}:{func['line']}:missing_docstring"

                                if task_key not in seen_tasks:
                                    tasks.append({
                                        "type": "missing_docstring",
                                        "description": f"Add docstring for {func['name']}()",
                                        "file": file_path,
                                        "line": func["line"],
                                        "confidence": "high" if len(agents) >= 2 else "medium",
                                        "auto_fixable": True,
                                        "risk_level": "none",
                                        "source": "doc_writer",
                                        "function_name": func["name"]
                                    })

                                    seen_tasks.add(task_key)

        return tasks

    def _get_commit_info(self, commit_hash: str) -> Dict[str, Any]:
        """Get information about a commit.

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

            return {
                "success": True,
                "hash": commit_hash,
                "message": message,
                "files_changed": [f for f in files if f]
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to get commit info: {str(e)}"
            }


if __name__ == "__main__":
    """Demo usage of Convergence Orchestrator."""
    print("=== Multi-Agent Convergence Orchestrator Demo ===\n")

    # Get API key
    api_key = os.getenv("ANTHROPIC_API_KEY")

    if not api_key:
        print("✗ ANTHROPIC_API_KEY not set")
        exit(1)

    orchestrator = ConvergenceOrchestrator(api_key, timeout=30)

    # Analyze latest commit
    print("Analyzing latest commit with multi-agent convergence...\n")

    async def run_analysis():
        result = await orchestrator.analyze_commit()

        if result["success"]:
            print(f"\n{'='*60}\n")
            print(f"✓ Convergence Analysis Complete")
            print()
            print(f"Commit: {result['commit_hash'][:7]}")
            print(f"Message: {result['commit_message'][:50]}...")
            print(f"Files Changed: {result['files_changed']}")
            print()
            print(f"Agents Run: {result['agents_run']}")
            print(f"Agents Succeeded: {result['agents_succeeded']}")
            print()
            print("Convergence:")
            print(f"  Files Flagged: {result['convergence']['total_files_flagged']}")
            print(f"  Consensus Files (2+ agents): {result['convergence']['consensus_files']}")
            print(f"  Critical Issues: {result['convergence']['critical_issues']}")
            print(f"  Requires Human Review: {result['convergence']['requires_human_review']}")
            print()
            print(f"Unified Tasks Generated: {result['tasks_added_to_queue']}")
            print()

            if result['unified_tasks']:
                print("Sample Tasks:")

                for task in result['unified_tasks'][:5]:
                    print(f"  [{task['confidence'].upper()}] {task['description']}")
                    print(f"    {task['file']}:{task['line']} (source: {task['source']})")
                    print()
        else:
            print(f"✗ Analysis failed: {result['error']}")

    # Run async analysis
    asyncio.run(run_analysis())
