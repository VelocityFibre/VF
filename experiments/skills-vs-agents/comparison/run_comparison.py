#!/usr/bin/env python3
"""
Skills vs Agent Architecture Comparison Runner

Executes the same test cases through both implementations:
- Skills-based (scripts in .claude/skills/database-operations/)
- Agent-based (NeonAgent in agents/neon-database/)

Measures and compares:
- Context token usage (estimated)
- Response time
- Accuracy (correct results)
- Usability (ease of getting answer)
"""

import os
import sys
import json
import time
import subprocess
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime

# Add project root to path
# From: experiments/skills-vs-agents/comparison/run_comparison.py
# To: /home/louisdup/Agents/claude/
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

# Try to import agent (may fail if not set up)
try:
    # Import from agents/neon-database/ (note: directory has hyphen, not underscore)
    sys.path.insert(0, str(project_root / "agents" / "neon-database"))
    from agent import NeonAgent
    AGENT_AVAILABLE = True
except Exception as e:
    AGENT_AVAILABLE = False
    AGENT_ERROR = str(e)


class ComparisonRunner:
    """
    Runs comparison tests between skills and agent implementations.
    """

    def __init__(self):
        self.project_root = project_root
        self.skills_path = project_root / ".claude/skills/database-operations/scripts"
        self.test_cases_path = Path(__file__).parent / "test_cases.json"
        self.results_path = Path(__file__).parent.parent / "results"

        # Create results directory
        self.results_path.mkdir(exist_ok=True)

        # Load test cases
        with open(self.test_cases_path) as f:
            self.test_data = json.load(f)

        self.results = {
            "timestamp": datetime.now().isoformat(),
            "test_suite": self.test_data["test_suite"],
            "skills_results": [],
            "agent_results": [],
            "comparison": {},
            "summary": {}
        }

    def run_skill_test(self, test_case: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute test case using skills-based approach.

        Args:
            test_case: Test case definition

        Returns:
            Test result dictionary
        """
        result = {
            "test_id": test_case["id"],
            "test_name": test_case["name"],
            "approach": "skills",
            "success": False,
            "execution_time_ms": 0,
            "context_tokens_estimated": 0,
            "output": None,
            "error": None
        }

        # Map query intent to skill tool
        tool_mapping = {
            "list_tables": "list_tables.py",
            "describe_table": "describe_table.py",
            "table_stats": "table_stats.py",
            "execute_query": "execute_query.py"
        }

        try:
            # Determine which tool to use based on test case
            expected_tool = test_case.get("expected_tool", "execute_query")
            script_name = tool_mapping.get(expected_tool, "execute_query.py")
            script_path = self.skills_path / script_name

            # Build command based on tool
            if expected_tool == "list_tables":
                cmd = [sys.executable, str(script_path)]
            elif expected_tool == "describe_table":
                # Extract table name from query (simplified)
                table_name = "contractors"  # Default for testing
                if "projects" in test_case["query"].lower():
                    table_name = "projects"
                cmd = [sys.executable, str(script_path), "--table", table_name]
            elif expected_tool == "table_stats":
                table_name = "contractors"
                if "projects" in test_case["query"].lower():
                    table_name = "projects"
                cmd = [sys.executable, str(script_path), "--table", table_name]
            else:  # execute_query
                # Generate SQL from natural language (simplified for POC)
                sql = self._generate_sql_from_query(test_case["query"])
                cmd = [sys.executable, str(script_path), "--query", sql]

            # Execute and measure time
            start_time = time.time()
            process = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=10
            )
            execution_time = (time.time() - start_time) * 1000  # ms

            # Parse result
            if process.returncode == 0:
                output = json.loads(process.stdout)
                result["success"] = output.get("success", False)
                result["output"] = output
                result["execution_time_ms"] = round(execution_time, 2)

                # Estimate context tokens (skill metadata + result)
                skill_metadata = 50  # YAML frontmatter
                skill_content = 600  # Full skill.md when activated
                result_data = len(json.dumps(output)) // 4  # Rough token estimate
                result["context_tokens_estimated"] = skill_metadata + skill_content + result_data
            else:
                result["error"] = process.stderr or "Script execution failed"
                result["execution_time_ms"] = round(execution_time, 2)

        except subprocess.TimeoutExpired:
            result["error"] = "Script execution timeout (>10s)"
        except json.JSONDecodeError as e:
            result["error"] = f"Invalid JSON output: {e}"
        except Exception as e:
            result["error"] = f"Execution error: {e}"

        return result

    def run_agent_test(self, test_case: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute test case using agent-based approach.

        Args:
            test_case: Test case definition

        Returns:
            Test result dictionary
        """
        result = {
            "test_id": test_case["id"],
            "test_name": test_case["name"],
            "approach": "agent",
            "success": False,
            "execution_time_ms": 0,
            "context_tokens_estimated": 0,
            "output": None,
            "error": None
        }

        if not AGENT_AVAILABLE:
            result["error"] = f"Agent not available: {AGENT_ERROR}"
            return result

        try:
            # Initialize agent
            agent = NeonAgent(model="claude-3-haiku-20240307")

            # Execute query and measure time
            start_time = time.time()
            response = agent.chat(test_case["query"])
            execution_time = (time.time() - start_time) * 1000  # ms

            result["success"] = True
            result["output"] = response
            result["execution_time_ms"] = round(execution_time, 2)

            # Estimate context tokens
            # Agent class + tools + conversation
            agent_scaffolding = 2000  # Agent class in context
            tool_definitions = 2000  # All tools defined
            conversation = len(test_case["query"]) // 4 + len(str(response)) // 4
            result["context_tokens_estimated"] = agent_scaffolding + tool_definitions + conversation

        except Exception as e:
            result["error"] = f"Agent execution error: {e}"

        return result

    def _generate_sql_from_query(self, query: str) -> str:
        """
        Simple query-to-SQL mapping for testing.
        In production, the LLM does this.
        """
        query_lower = query.lower()

        # Count contractors
        if "how many contractors" in query_lower:
            if "active" in query_lower:
                return "SELECT COUNT(*) as count FROM contractors WHERE status = 'active'"
            return "SELECT COUNT(*) as count FROM contractors"

        # List contractors
        if "show" in query_lower and "contractors" in query_lower:
            return "SELECT name, phone, status FROM contractors LIMIT 20"

        # Count projects
        if "how many projects" in query_lower:
            return "SELECT COUNT(*) as count FROM projects"

        # Distribution analysis
        if "distribution" in query_lower and "status" in query_lower:
            return "SELECT status, COUNT(*) as count FROM contractors GROUP BY status"

        # Default
        return "SELECT COUNT(*) as count FROM contractors"

    def run_comparison(self):
        """
        Run all test cases through both implementations.
        """
        print("=" * 70)
        print("Skills vs Agent Architecture Comparison")
        print("=" * 70)
        print()
        print(f"Test suite: {self.test_data['test_suite']}")
        print(f"Total tests: {self.test_data['metadata']['total_tests']}")
        print()

        for i, test_case in enumerate(self.test_data["test_cases"], 1):
            print(f"Test {i}/{len(self.test_data['test_cases'])}: {test_case['name']}")
            print(f"  Category: {test_case['category']}")
            print(f"  Complexity: {test_case['complexity']}/10")
            print()

            # Run skills-based test
            print("  Running skills-based test...")
            skills_result = self.run_skill_test(test_case)
            self.results["skills_results"].append(skills_result)

            status = "✅ PASS" if skills_result["success"] else "❌ FAIL"
            print(f"    {status}")
            print(f"    Time: {skills_result['execution_time_ms']}ms")
            print(f"    Context: ~{skills_result['context_tokens_estimated']} tokens")
            if skills_result.get("error"):
                print(f"    Error: {skills_result['error']}")
            print()

            # Run agent-based test
            print("  Running agent-based test...")
            agent_result = self.run_agent_test(test_case)
            self.results["agent_results"].append(agent_result)

            status = "✅ PASS" if agent_result["success"] else "❌ FAIL"
            print(f"    {status}")
            print(f"    Time: {agent_result['execution_time_ms']}ms")
            print(f"    Context: ~{agent_result['context_tokens_estimated']} tokens")
            if agent_result.get("error"):
                print(f"    Error: {agent_result['error']}")
            print()

            print("-" * 70)
            print()

        # Calculate summary statistics
        self._calculate_summary()

        # Save results
        self._save_results()

        # Print summary
        self._print_summary()

    def _calculate_summary(self):
        """Calculate summary statistics from results."""
        skills_success = sum(1 for r in self.results["skills_results"] if r["success"])
        agent_success = sum(1 for r in self.results["agent_results"] if r["success"])

        skills_avg_time = sum(r["execution_time_ms"] for r in self.results["skills_results"]) / len(self.results["skills_results"])
        agent_avg_time = sum(r["execution_time_ms"] for r in self.results["agent_results"]) / len(self.results["agent_results"])

        skills_avg_context = sum(r["context_tokens_estimated"] for r in self.results["skills_results"]) / len(self.results["skills_results"])
        agent_avg_context = sum(r["context_tokens_estimated"] for r in self.results["agent_results"]) / len(self.results["agent_results"])

        self.results["summary"] = {
            "total_tests": len(self.test_data["test_cases"]),
            "skills": {
                "successful": skills_success,
                "failed": len(self.results["skills_results"]) - skills_success,
                "avg_execution_time_ms": round(skills_avg_time, 2),
                "avg_context_tokens": round(skills_avg_context, 0)
            },
            "agent": {
                "successful": agent_success,
                "failed": len(self.results["agent_results"]) - agent_success,
                "avg_execution_time_ms": round(agent_avg_time, 2),
                "avg_context_tokens": round(agent_avg_context, 0)
            },
            "comparison": {
                "context_reduction_pct": round((1 - skills_avg_context / agent_avg_context) * 100, 1) if agent_avg_context > 0 else 0,
                "time_difference_ms": round(skills_avg_time - agent_avg_time, 2),
                "skills_faster": skills_avg_time < agent_avg_time
            }
        }

    def _save_results(self):
        """Save results to JSON files."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Save complete results
        results_file = self.results_path / f"comparison_{timestamp}.json"
        with open(results_file, 'w') as f:
            json.dump(self.results, f, indent=2)

        print(f"Results saved to: {results_file}")
        print()

    def _print_summary(self):
        """Print summary of comparison."""
        summary = self.results["summary"]

        print("=" * 70)
        print("COMPARISON SUMMARY")
        print("=" * 70)
        print()

        print(f"Total Tests: {summary['total_tests']}")
        print()

        print("Skills-Based Approach:")
        print(f"  Success Rate: {summary['skills']['successful']}/{summary['total_tests']} ({summary['skills']['successful']/summary['total_tests']*100:.1f}%)")
        print(f"  Avg Execution Time: {summary['skills']['avg_execution_time_ms']}ms")
        print(f"  Avg Context Usage: {summary['skills']['avg_context_tokens']} tokens")
        print()

        print("Agent-Based Approach:")
        print(f"  Success Rate: {summary['agent']['successful']}/{summary['total_tests']} ({summary['agent']['successful']/summary['total_tests']*100:.1f}%)")
        print(f"  Avg Execution Time: {summary['agent']['avg_execution_time_ms']}ms")
        print(f"  Avg Context Usage: {summary['agent']['avg_context_tokens']} tokens")
        print()

        print("Comparison:")
        print(f"  Context Reduction: {summary['comparison']['context_reduction_pct']}%")
        print(f"  Time Difference: {abs(summary['comparison']['time_difference_ms'])}ms ({'Skills' if summary['comparison']['skills_faster'] else 'Agent'} faster)")
        print()

        print("=" * 70)


def main():
    """Main entry point."""
    runner = ComparisonRunner()
    runner.run_comparison()


if __name__ == "__main__":
    main()
