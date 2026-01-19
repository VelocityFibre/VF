#!/usr/bin/env python3
"""
External Agent Access Test
Verify that an external agent can access the Superior Agent Brain system.

Usage:
    python test_external_access.py
"""

import sys
import os
from pathlib import Path

# Add Superior Brain to path
BRAIN_PATH = '/home/louisdup/Agents/claude'
sys.path.insert(0, BRAIN_PATH)

def test_imports():
    """Test that all imports work."""
    print("\n" + "="*70)
    print("TEST 1: Importing Components")
    print("="*70)

    try:
        from superior_agent_brain import SuperiorAgentBrain
        print("✅ Superior Agent Brain imported")
    except ImportError as e:
        print(f"❌ Failed to import SuperiorAgentBrain: {e}")
        return False

    try:
        from memory import VectorMemory, PersistentMemory, MetaLearner, KnowledgeGraph
        print("✅ Memory systems imported")
    except ImportError as e:
        print(f"❌ Failed to import memory systems: {e}")
        return False

    try:
        from orchestrator.orchestrator import AgentOrchestrator
        print("✅ Orchestrator imported")
    except ImportError as e:
        print(f"❌ Failed to import orchestrator: {e}")
        return False

    return True


def test_environment():
    """Test environment variables."""
    print("\n" + "="*70)
    print("TEST 2: Environment Variables")
    print("="*70)

    required = ['ANTHROPIC_API_KEY', 'NEON_DATABASE_URL']
    optional = ['CONVEX_URL', 'QDRANT_URL']

    all_ok = True

    for var in required:
        if os.environ.get(var):
            print(f"✅ {var} is set")
        else:
            print(f"❌ {var} is NOT set (required)")
            all_ok = False

    for var in optional:
        if os.environ.get(var):
            print(f"✅ {var} is set")
        else:
            print(f"⚠️  {var} is not set (optional)")

    return all_ok


def test_brain_initialization():
    """Test brain initialization."""
    print("\n" + "="*70)
    print("TEST 3: Brain Initialization")
    print("="*70)

    try:
        from superior_agent_brain import SuperiorAgentBrain

        print("Initializing brain (this may take a moment)...")
        brain = SuperiorAgentBrain(
            enable_vector_memory=False,  # Skip for quick test
            enable_persistent_memory=False,
            enable_meta_learning=False,
            enable_knowledge_graph=False,
            enable_orchestration=False
        )

        print("✅ Brain initialized successfully")

        # Test basic chat
        print("\nTesting basic chat...")
        response = brain.chat("Hello, this is a test")
        print(f"✅ Chat works! Response received ({len(response)} characters)")

        brain.close()
        print("✅ Brain closed cleanly")

        return True

    except Exception as e:
        print(f"❌ Brain initialization failed: {e}")
        return False


def test_file_access():
    """Test that key files exist."""
    print("\n" + "="*70)
    print("TEST 4: File Access")
    print("="*70)

    files_to_check = [
        '/home/louisdup/Agents/claude/superior_agent_brain.py',
        '/home/louisdup/Agents/claude/docs/MASTER_INDEX.md',
        '/home/louisdup/Agents/claude/docs/EXTERNAL_AGENT_ACCESS_GUIDE.md',
        '/home/louisdup/Agents/claude/system_manifest.json',
        '/home/louisdup/Agents/claude/EXTERNAL_AGENT_QUICK_REF.txt',
    ]

    all_exist = True

    for file_path in files_to_check:
        if Path(file_path).exists():
            print(f"✅ {Path(file_path).name}")
        else:
            print(f"❌ {Path(file_path).name} not found")
            all_exist = False

    return all_exist


def test_manifest():
    """Test system manifest."""
    print("\n" + "="*70)
    print("TEST 5: System Manifest")
    print("="*70)

    try:
        import json

        manifest_path = '/home/louisdup/Agents/claude/system_manifest.json'
        with open(manifest_path) as f:
            manifest = json.load(f)

        print(f"✅ Manifest loaded")
        print(f"   System: {manifest['system']['name']}")
        print(f"   Version: {manifest['system']['version']}")
        print(f"   Status: {manifest['system']['status']}")
        print(f"   Implementation: {manifest['status']['implementation']}")

        # Check capabilities
        caps = manifest['capabilities']
        cap_count = sum(1 for v in caps.values() if v)
        print(f"   Capabilities: {cap_count}/{len(caps)} active")

        return True

    except Exception as e:
        print(f"❌ Manifest test failed: {e}")
        return False


def test_http_api():
    """Test HTTP API if running."""
    print("\n" + "="*70)
    print("TEST 6: HTTP API (Optional)")
    print("="*70)

    try:
        import requests

        response = requests.get('http://localhost:8000/status', timeout=2)

        if response.status_code == 200:
            data = response.json()
            print("✅ API is running")
            print(f"   Session: {data.get('session_id', 'N/A')}")
            print(f"   Model: {data.get('model', 'N/A')}")
            return True
        else:
            print(f"⚠️  API responded with status {response.status_code}")
            return False

    except requests.exceptions.ConnectionError:
        print("⚠️  API not running (this is OK for local testing)")
        return True
    except ImportError:
        print("⚠️  'requests' not installed (pip install requests)")
        return True
    except Exception as e:
        print(f"⚠️  API test failed: {e}")
        return True


def test_documentation():
    """Test documentation access."""
    print("\n" + "="*70)
    print("TEST 7: Documentation Access")
    print("="*70)

    docs_path = Path('/home/louisdup/Agents/claude/docs')

    if not docs_path.exists():
        print("❌ Documentation directory not found")
        return False

    docs = list(docs_path.glob('*.md'))
    print(f"✅ Found {len(docs)} documentation files:")

    for doc in docs:
        print(f"   • {doc.name}")

    return len(docs) > 0


def run_all_tests():
    """Run all tests."""
    print("\n" + "█"*70)
    print("EXTERNAL AGENT ACCESS TEST SUITE")
    print("█"*70)
    print(f"\nTesting access to: {BRAIN_PATH}")
    print(f"Python version: {sys.version.split()[0]}")

    # Load environment from .env if exists
    env_path = Path(BRAIN_PATH) / '.env'
    if env_path.exists():
        print(f"Loading environment from: {env_path}")
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()
    else:
        print(f"⚠️  No .env file found at {env_path}")

    # Run tests
    results = {
        "Imports": test_imports(),
        "Environment": test_environment(),
        "Brain Init": test_brain_initialization(),
        "File Access": test_file_access(),
        "Manifest": test_manifest(),
        "HTTP API": test_http_api(),
        "Documentation": test_documentation()
    }

    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:20s} {status}")

    print("="*70)
    print(f"Results: {passed}/{total} tests passed")
    print("="*70)

    if passed == total:
        print("\n🎉 All tests passed! External agent access is fully functional.")
        print("\nNext steps:")
        print("  1. See EXTERNAL_AGENT_QUICK_REF.txt for usage examples")
        print("  2. Read docs/EXTERNAL_AGENT_ACCESS_GUIDE.md for full details")
        print("  3. Review system_manifest.json for system capabilities")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Check output above for details.")
        return 1


if __name__ == "__main__":
    exit_code = run_all_tests()
    sys.exit(exit_code)
