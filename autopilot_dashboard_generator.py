#!/usr/bin/env python3
"""
Autopilot Dashboard Generator - Week 1 PoC Main Event
Generates Contractor Dashboard with 5 parallel attempts
"""
import os
import sys
import json
import asyncio
from pathlib import Path
from datetime import datetime
from anthropic import Anthropic

# Configuration
N_ATTEMPTS = 5  # 5 parallel implementations for best-of-N selection
SPEC_FILE = "contractor_dashboard_spec.md"

def load_specification():
    """Load the dashboard specification"""
    spec_path = Path(__file__).parent / SPEC_FILE
    if not spec_path.exists():
        print(f"❌ Specification file not found: {spec_path}")
        sys.exit(1)

    with open(spec_path, 'r') as f:
        return f.read()

async def generate_dashboard_implementation(attempt_num: int, spec: str, client: Anthropic) -> dict:
    """Generate one complete dashboard implementation"""
    print(f"   🔨 Attempt {attempt_num}: Generating dashboard...")
    start_time = datetime.now()

    system_prompt = """You are an expert Next.js/TypeScript/Tailwind developer.
Generate production-quality code following all requirements in the specification.
Focus on clean architecture, proper TypeScript types, and beautiful UI."""

    user_prompt = f"""{spec}

Generate a COMPLETE, production-ready implementation of the Contractor Dashboard.

Requirements:
1. Single file: pages/contractors/dashboard.tsx
2. Include ALL components inline (MetricCard, Chart, Table, Timeline)
3. Use Recharts for the performance chart
4. Use mock data (provided in spec) for now
5. Fully responsive design with Tailwind CSS
6. Comprehensive TypeScript types
7. JSDoc comments for all functions/components
8. Error handling and loading states
9. Beautiful, professional UI

Output ONLY the complete TypeScript/TSX code. No explanations.
Start with: import {{ useState, useEffect }}...
"""

    try:
        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=8000,  # Dashboard needs more tokens
            messages=[{
                "role": "user",
                "content": user_prompt
            }],
            system=system_prompt
        )

        code = message.content[0].text

        # Clean code blocks if present
        if '```' in code:
            code = code.split('```')[1]
            if code.startswith('typescript') or code.startswith('tsx'):
                code = '\n'.join(code.split('\n')[1:])

        generation_time = (datetime.now() - start_time).total_seconds()

        # Score the implementation
        print(f"   📊 Attempt {attempt_num}: Scoring implementation...")
        score = await score_dashboard(code, spec, client)

        return {
            "attempt": attempt_num,
            "code": code,
            "score": score,
            "model": message.model,
            "tokens": message.usage.input_tokens + message.usage.output_tokens,
            "generation_time": generation_time,
            "success": True
        }

    except Exception as e:
        print(f"   ❌ Attempt {attempt_num} failed: {e}")
        return {
            "attempt": attempt_num,
            "error": str(e),
            "score": {"total": 0},
            "success": False
        }

async def score_dashboard(code: str, spec: str, client: Anthropic) -> dict:
    """Score a dashboard implementation comprehensively"""

    scoring_prompt = f"""Rate this Contractor Dashboard implementation on a scale of 1-10 for each criterion.
Analyze the code carefully and return ONLY a JSON object with scores.

Code to evaluate:
```typescript
{code[:4000]}  # First 4000 chars for scoring
```

Original specification:
{spec[:2000]}  # First 2000 chars of spec

Score these criteria (1-10):
1. completeness - Are all required components present? (metrics, chart, table, timeline)
2. typescript_quality - Proper types, interfaces, no 'any'?
3. ui_design - Professional, clean, follows Tailwind best practices?
4. responsive_design - Mobile-friendly, adapts to screen sizes?
5. code_organization - Well-structured, reusable components?
6. error_handling - Loading states, error boundaries, graceful fallbacks?
7. data_integration - Proper mock data, ready for Convex integration?
8. accessibility - ARIA labels, semantic HTML, keyboard nav?
9. documentation - JSDoc comments, clear variable names?
10. production_ready - Would you deploy this as-is?

Return ONLY this format: {{"completeness": 9, "typescript_quality": 8, ...}}
"""

    try:
        message = client.messages.create(
            model="claude-3-5-sonnet-20241022",  # Use Sonnet 3.5 for scoring (cheaper than Sonnet 4)
            max_tokens=300,
            messages=[{"role": "user", "content": scoring_prompt}]
        )

        scores_text = message.content[0].text

        # Extract JSON from response
        import re
        json_match = re.search(r'\{[^}]+\}', scores_text, re.DOTALL)
        if json_match:
            scores = json.loads(json_match.group())
            total = sum(scores.values())
            scores['total'] = total
            scores['average'] = round(total / 10, 1)
            return scores
        else:
            return {"error": "Could not parse scores", "total": 0}

    except Exception as e:
        print(f"   ⚠ Scoring failed: {e}")
        return {"error": str(e), "total": 0}

async def run_dashboard_autopilot():
    """Main autopilot orchestrator for dashboard generation"""
    print("╔═══════════════════════════════════════════════════════════╗")
    print("║     Contractor Dashboard - Autopilot Generation PoC       ║")
    print("║              Week 1 Transformation Proof                   ║")
    print("╚═══════════════════════════════════════════════════════════╝")
    print()

    # Load specification
    print("📋 Loading specification...")
    spec = load_specification()
    spec_lines = len(spec.split('\n'))
    spec_words = len(spec.split())
    print(f"   ✅ Loaded: {spec_lines} lines, {spec_words} words")
    print()

    # Validate environment
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("❌ ANTHROPIC_API_KEY not set")
        sys.exit(1)

    client = Anthropic(api_key=api_key)

    # Run parallel generation
    print(f"🚀 Generating {N_ATTEMPTS} parallel dashboard implementations...")
    print(f"⏱️  Expected time: 2-3 minutes")
    print(f"💰 Expected cost: ~$1.50-$2.00")
    print()

    start_time = datetime.now()

    tasks = [generate_dashboard_implementation(i+1, spec, client) for i in range(N_ATTEMPTS)]
    results = await asyncio.gather(*tasks)

    total_time = (datetime.now() - start_time).total_seconds()

    # Filter successful results
    successful = [r for r in results if r.get('success', False)]
    failed_count = len(results) - len(successful)

    print()
    print("=" * 63)
    print(f"🎉 Generation Complete! {len(successful)}/{N_ATTEMPTS} successful")
    print(f"⏱️  Total time: {total_time:.1f} seconds ({total_time/60:.1f} minutes)")
    print("=" * 63)
    print()

    if not successful:
        print("❌ All attempts failed - no dashboard generated")
        return

    # Display scoring results
    print("📊 SCORING RESULTS:")
    print()
    print("Rank | Attempt | Total | Complete | TypeScript | UI | Responsive | Prod Ready")
    print("-" * 80)

    # Sort by total score
    ranked = sorted(successful, key=lambda r: r.get('score', {}).get('total', 0), reverse=True)

    for rank, result in enumerate(ranked, 1):
        score = result.get('score', {})
        medal = "🥇" if rank == 1 else "🥈" if rank == 2 else "🥉" if rank == 3 else "  "
        print(f"{medal} #{rank}  | Attempt {result['attempt']} | "
              f"{score.get('total', 0):>3}/100 | "
              f"{score.get('completeness', 0):>8} | "
              f"{score.get('typescript_quality', 0):>10} | "
              f"{score.get('ui_design', 0):>2} | "
              f"{score.get('responsive_design', 0):>10} | "
              f"{score.get('production_ready', 0):>10}")

    print()

    # Select best implementation
    best = ranked[0]

    print("=" * 63)
    print(f"🏆 BEST IMPLEMENTATION: Attempt {best['attempt']}")
    print(f"   Total Score: {best['score']['total']}/100")
    print(f"   Average: {best['score']['average']}/10")
    print("=" * 63)
    print()

    # Detailed scoring breakdown
    print("📈 Detailed Scores:")
    score = best['score']
    criteria = [
        ('Completeness', score.get('completeness', 0)),
        ('TypeScript Quality', score.get('typescript_quality', 0)),
        ('UI Design', score.get('ui_design', 0)),
        ('Responsive Design', score.get('responsive_design', 0)),
        ('Code Organization', score.get('code_organization', 0)),
        ('Error Handling', score.get('error_handling', 0)),
        ('Data Integration', score.get('data_integration', 0)),
        ('Accessibility', score.get('accessibility', 0)),
        ('Documentation', score.get('documentation', 0)),
        ('Production Ready', score.get('production_ready', 0)),
    ]

    for name, value in criteria:
        bar = "█" * value + "░" * (10 - value)
        print(f"   {name:.<25} {bar} {value}/10")

    print()

    # Save outputs
    output_dir = Path("dashboard_autopilot_output")
    output_dir.mkdir(exist_ok=True)

    # Save best implementation
    best_file = output_dir / "dashboard_BEST.tsx"
    with open(best_file, 'w') as f:
        f.write(best['code'])
    print(f"✅ Best implementation: {best_file}")

    # Save all attempts
    for result in successful:
        attempt_file = output_dir / f"dashboard_attempt_{result['attempt']}.tsx"
        with open(attempt_file, 'w') as f:
            f.write(result['code'])
    print(f"✅ All attempts: {output_dir}/dashboard_attempt_*.tsx")

    # Save detailed results
    results_file = output_dir / "results.json"
    with open(results_file, 'w') as f:
        # Don't save full code in JSON (too large)
        summary_results = [{
            "attempt": r['attempt'],
            "score": r['score'],
            "tokens": r.get('tokens', 0),
            "generation_time": r.get('generation_time', 0),
            "success": r['success']
        } for r in results]

        json.dump({
            "specification": SPEC_FILE,
            "timestamp": datetime.now().isoformat(),
            "attempts": N_ATTEMPTS,
            "successful": len(successful),
            "failed": failed_count,
            "total_time_seconds": total_time,
            "best_attempt": best['attempt'],
            "best_score": best['score'],
            "all_results": summary_results,
            "total_tokens": sum(r.get('tokens', 0) for r in successful),
            "estimated_cost": sum(r.get('tokens', 0) for r in successful) * 0.000015  # Rough estimate
        }, f, indent=2)
    print(f"✅ Results: {results_file}")

    print()
    print("=" * 63)
    print("🎉 DAY 3 COMPLETE: CONTRACTOR DASHBOARD GENERATED!")
    print("=" * 63)
    print()
    print("📊 Performance Stats:")
    total_tokens = sum(r.get('tokens', 0) for r in successful)
    estimated_cost = total_tokens * 0.000015
    print(f"   • Total tokens: {total_tokens:,}")
    print(f"   • Estimated cost: ${estimated_cost:.2f}")
    print(f"   • Generation time: {total_time/60:.1f} minutes")
    print(f"   • Manual estimate: 7-10 hours")
    print(f"   • Time saved: ~{((8*60 - total_time/60) / (8*60) * 100):.0f}%")
    print()
    print("🚀 Next Steps:")
    print("   1. Review generated dashboard files")
    print(f"   2. Copy best to FibreFlow: {best_file} → pages/contractors/dashboard.tsx")
    print("   3. Load in browser: http://100.96.203.105:3006/contractors/dashboard")
    print("   4. Visual review and comparison")
    print()

if __name__ == "__main__":
    asyncio.run(run_dashboard_autopilot())
