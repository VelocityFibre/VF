#!/usr/bin/env python3
"""
Autopilot CLI for FibreFlow
Wraps the vibe coding transformation system with a simple interface
"""
import os
import sys
import json
import argparse
from pathlib import Path
from datetime import datetime

def main():
    parser = argparse.ArgumentParser(
        description='FibreFlow Autopilot - Vibe Coding Transformation',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Build a new feature
  python3 autopilot/cli.py feature "Add health check endpoint at /api/health"

  # Build a new page/component
  python3 autopilot/cli.py page "ContractorDashboard" "/contractors/dashboard"

  # Run with specific model tier
  python3 autopilot/cli.py feature "Add CSV export" --model sonnet

  # Dry run (no actual execution)
  python3 autopilot/cli.py feature "Add search filter" --dry-run
        """
    )

    parser.add_argument('type', choices=['feature', 'page', 'component', 'api'],
                       help='Type of work to build')
    parser.add_argument('description', help='Description of what to build')
    parser.add_argument('route', nargs='?', default=None,
                       help='Route/path (for pages/api)')
    parser.add_argument('--model', choices=['haiku', 'sonnet', 'opus'],
                       default='auto', help='Model tier to use (default: auto-select)')
    parser.add_argument('--attempts', type=int, default=15,
                       help='Number of parallel attempts (default: 15)')
    parser.add_argument('--dry-run', action='store_true',
                       help='Show what would be built without executing')
    parser.add_argument('--output', default=None,
                       help='Output directory for generated code')

    args = parser.parse_args()

    # Validate environment
    if not os.getenv('E2B_API_KEY'):
        print("❌ E2B_API_KEY not set in environment")
        print("   Add to ~/fibreflow-louis/.env.local:")
        print("   E2B_API_KEY=your_key_here")
        sys.exit(1)

    if not os.getenv('ANTHROPIC_API_KEY'):
        print("❌ ANTHROPIC_API_KEY not set in environment")
        print("   Add to ~/fibreflow-louis/.env.local:")
        print("   ANTHROPIC_API_KEY=your_key_here")
        sys.exit(1)

    # Build task specification
    task = {
        'type': args.type,
        'description': args.description,
        'route': args.route,
        'model': args.model,
        'attempts': args.attempts,
        'timestamp': datetime.now().isoformat()
    }

    # Print what we're doing
    print("╔═══════════════════════════════════════════════════════════╗")
    print("║      FibreFlow Autopilot - Vibe Coding Transformation      ║")
    print("╚═══════════════════════════════════════════════════════════╝")
    print()
    print(f"📋 Task Type: {args.type.upper()}")
    print(f"📝 Description: {args.description}")
    if args.route:
        print(f"🔗 Route: {args.route}")
    print(f"🤖 Model Strategy: {args.model}")
    print(f"🔄 Parallel Attempts: {args.attempts}")
    print()

    if args.dry_run:
        print("🔍 DRY RUN MODE - No actual execution")
        print()
        print("Would execute:")
        print(f"  1. Create {args.attempts} parallel E2B sandboxes")
        print(f"  2. Each builds: {args.description}")
        print(f"  3. Run consensus validation")
        print(f"  4. Select best implementation")
        print(f"  5. Generate comprehensive tests")
        print()
        print("Expected savings:")
        print("  • Time: 85%+ (6.5 hours → 30 minutes)")
        print("  • Cost: 75%+ (tiered model selection)")
        print("  • Coverage: 95%+ (vs 60-70% manual)")
        print()
        print("Ready to run? Remove --dry-run flag")
        sys.exit(0)

    # Import autopilot components
    sys.path.insert(0, str(Path(__file__).parent.parent))

    try:
        from autopilot.harness.autopilot_orchestrator import AutopilotOrchestrator
        from autopilot.orchestrator.model_router import ModelRouter
        from autopilot.harness.best_of_n_selector import BestOfNSelector

        print("✅ Autopilot components loaded")
        print()

    except ImportError as e:
        print(f"❌ Failed to import autopilot components: {e}")
        print()
        print("Make sure you're running from ~/fibreflow-louis/autopilot/venv:")
        print("  cd ~/fibreflow-louis")
        print("  source autopilot/venv/bin/activate")
        print("  python3 autopilot/cli.py feature 'your task'")
        sys.exit(1)

    # Execute autopilot
    print("🚀 Launching Autopilot...")
    print("=" * 60)
    print()

    try:
        orchestrator = AutopilotOrchestrator(
            model_router=ModelRouter(),
            selector=BestOfNSelector()
        )

        result = orchestrator.build(
            task_type=args.type,
            description=args.description,
            route=args.route,
            model_tier=args.model,
            n_attempts=args.attempts,
            output_dir=args.output
        )

        print()
        print("=" * 60)
        print("🎉 AUTOPILOT COMPLETE!")
        print()
        print("📊 Results:")
        print(f"  ✅ Implementation: {result['best_implementation']['path']}")
        print(f"  ✅ Tests: {result['test_coverage']}% coverage")
        print(f"  ✅ Time saved: {result['time_savings']}%")
        print(f"  ✅ Cost saved: {result['cost_savings']}%")
        print()
        print(f"📁 Output: {result['output_directory']}")
        print()

        # Save results
        results_file = Path(args.output or '.') / 'autopilot_results.json'
        with open(results_file, 'w') as f:
            json.dump(result, f, indent=2)
        print(f"💾 Results saved to: {results_file}")

    except Exception as e:
        print()
        print("❌ AUTOPILOT FAILED")
        print(f"   Error: {e}")
        print()
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()
