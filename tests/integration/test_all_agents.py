#!/usr/bin/env python3
"""
Comprehensive Test Suite for All VF Agents
Tests unified agent, specialized agents, and orchestrator integration.
"""

import os
import sys
import json
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Load environment variables
env_path = project_root / '.env'
if env_path.exists():
    load_dotenv(env_path)

# Import from new location (agents/convex-database/)
try:
    sys.path.insert(0, str(project_root / 'agents' / 'convex-database'))
    from convex_agent import ConvexAgent
except ImportError:
    ConvexAgent = None

import pytest


@pytest.mark.skipif(ConvexAgent is None, reason="convex_agent.py not available")
@pytest.mark.integration
def test_unified_convex_agent():
    """Test 1: Unified Convex Agent with all tools."""
    print("\n" + "="*70)
    print("TEST 1: UNIFIED CONVEX AGENT (with contractors & projects)")
    print("="*70)

    agent = ConvexAgent()
    test_results = []

    queries = [
        ("Tasks", "How many tasks do we have?"),
        ("Contractors", "List all contractors"),
        ("Contractors Count", "How many contractors do we have?"),
        ("Projects", "Show me all projects"),
        ("Projects Count", "How many projects do we have?"),
        ("Multi-Query", "Give me an overview: contractors, projects, and tasks")
    ]

    for category, query in queries:
        try:
            print(f"\n🔍 {category}: '{query}'")
            agent.reset_conversation()
            response = agent.chat(query)
            print(f"✅ Response ({len(response)} chars):\n{response[:200]}...")
            test_results.append((category, True, len(response)))
        except Exception as e:
            print(f"❌ Error: {e}")
            test_results.append((category, False, str(e)))

    return test_results


def test_contractor_agent():
    """Test 2: Specialized Contractor Agent."""
    print("\n" + "="*70)
    print("TEST 2: CONTRACTOR AGENT (Specialized)")
    print("="*70)

    from agents.contractor_agent.agent import ContractorAgent

    agent = ContractorAgent()
    test_results = []

    queries = [
        ("List All", "List all contractors"),
        ("Count", "How many contractors do we have?"),
        ("Search", "Search for contractors with 'Fiber' in the name"),
        ("Stats", "Give me contractor statistics"),
        ("Active Only", "Show me only active contractors")
    ]

    for category, query in queries:
        try:
            print(f"\n🔍 {category}: '{query}'")
            agent.reset_conversation()
            response = agent.chat(query)
            print(f"✅ Response ({len(response)} chars):\n{response[:200]}...")
            test_results.append((category, True, len(response)))
        except Exception as e:
            print(f"❌ Error: {e}")
            test_results.append((category, False, str(e)))

    return test_results


def test_project_agent():
    """Test 3: Specialized Project Agent."""
    print("\n" + "="*70)
    print("TEST 3: PROJECT AGENT (Specialized)")
    print("="*70)

    from agents.project_agent.agent import ProjectAgent

    agent = ProjectAgent()
    test_results = []

    queries = [
        ("List All", "List all projects"),
        ("Count", "How many projects do we have?"),
        ("Search", "Search for Lawley project"),
        ("Stats", "Show me project statistics"),
        ("Status", "What's the status of our projects?")
    ]

    for category, query in queries:
        try:
            print(f"\n🔍 {category}: '{query}'")
            agent.reset_conversation()
            response = agent.chat(query)
            print(f"✅ Response ({len(response)} chars):\n{response[:200]}...")
            test_results.append((category, True, len(response)))
        except Exception as e:
            print(f"❌ Error: {e}")
            test_results.append((category, False, str(e)))

    return test_results


def test_orchestrator_routing():
    """Test 4: Orchestrator Routing to New Agents."""
    print("\n" + "="*70)
    print("TEST 4: ORCHESTRATOR ROUTING")
    print("="*70)

    from orchestrator.orchestrator import AgentOrchestrator

    orch = AgentOrchestrator()

    # Test routing
    test_cases = [
        ("Show me all contractors", "contractor-agent"),
        ("List all projects", "project-agent"),
        ("How many tasks do we have?", "convex-database"),
        ("What's the CPU usage?", "vps-monitor"),
    ]

    test_results = []

    for query, expected_agent in test_cases:
        try:
            print(f"\n🔍 Query: '{query}'")
            result = orch.route_task(query, auto_select=True)

            if result['status'] == 'routed':
                agent_id = result['agent']['agent_id']
                matched = agent_id == expected_agent
                status = "✅" if matched else "⚠️"
                print(f"{status} Routed to: {agent_id} (expected: {expected_agent})")
                test_results.append((query, matched, agent_id))
            else:
                print(f"❌ No route found")
                test_results.append((query, False, "no_route"))

        except Exception as e:
            print(f"❌ Error: {e}")
            test_results.append((query, False, str(e)))

    return test_results


def main():
    """Run all agent tests."""
    print("\n" + "="*70)
    print("VF AGENT WORKFORCE - COMPREHENSIVE TEST SUITE")
    print("="*70)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    load_env()

    all_results = {}

    # Test 1: Unified Agent
    try:
        all_results['unified_agent'] = test_unified_convex_agent()
    except Exception as e:
        print(f"\n❌ Unified Agent Test Failed: {e}")
        all_results['unified_agent'] = []

    # Test 2: Contractor Agent
    try:
        all_results['contractor_agent'] = test_contractor_agent()
    except Exception as e:
        print(f"\n❌ Contractor Agent Test Failed: {e}")
        all_results['contractor_agent'] = []

    # Test 3: Project Agent
    try:
        all_results['project_agent'] = test_project_agent()
    except Exception as e:
        print(f"\n❌ Project Agent Test Failed: {e}")
        all_results['project_agent'] = []

    # Test 4: Orchestrator
    try:
        all_results['orchestrator'] = test_orchestrator_routing()
    except Exception as e:
        print(f"\n❌ Orchestrator Test Failed: {e}")
        all_results['orchestrator'] = []

    # Summary Report
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)

    total_tests = 0
    passed_tests = 0

    for test_name, results in all_results.items():
        if isinstance(results, list) and len(results) > 0:
            test_passed = sum(1 for r in results if isinstance(r, tuple) and r[1] == True)
            test_total = len(results)
            total_tests += test_total
            passed_tests += test_passed

            print(f"\n{test_name.upper()}:")
            print(f"  Passed: {test_passed}/{test_total}")

            for result in results:
                if isinstance(result, tuple):
                    category = result[0]
                    success = result[1]
                    status = "✅" if success else "❌"
                    print(f"  {status} {category}")

    print(f"\n{'='*70}")
    print(f"OVERALL RESULTS:")
    print(f"  Total Tests: {total_tests}")
    print(f"  Passed: {passed_tests}")
    print(f"  Failed: {total_tests - passed_tests}")
    print(f"  Success Rate: {(passed_tests/total_tests*100):.1f}%")
    print("="*70)

    if passed_tests == total_tests:
        print("\n🎉 ALL TESTS PASSED! Agent workforce fully operational.")
    else:
        print(f"\n⚠️  {total_tests - passed_tests} test(s) failed. Review output above.")

    # Save results
    report_file = f"agent_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_file, 'w') as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total": total_tests,
                "passed": passed_tests,
                "failed": total_tests - passed_tests,
                "success_rate": f"{(passed_tests/total_tests*100):.1f}%"
            },
            "results": {k: [str(r) for r in v] for k, v in all_results.items()}
        }, f, indent=2)

    print(f"\n📄 Full report saved to: {report_file}")

    return 0 if passed_tests == total_tests else 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
