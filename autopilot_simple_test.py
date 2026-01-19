#!/usr/bin/env python3
"""
Simplified Autopilot Test - Manual Review Version
Generates health check endpoint with 3 parallel attempts for manual review
"""
import os
import sys
import json
import asyncio
from pathlib import Path
from datetime import datetime
from anthropic import Anthropic

# Configuration
N_ATTEMPTS = 3  # Reduced for cost/time savings
TASK_DESCRIPTION = """
Create a Next.js API route for a health check endpoint at /api/health

Requirements:
1. File location: pages/api/health.ts
2. Returns JSON with:
   - status: "healthy"
   - timestamp: current ISO timestamp
   - version: "1.0.0"
   - database: Check Convex connection status
   - uptime: Process uptime in seconds
3. TypeScript with proper types
4. Include error handling
5. Follow Next.js 13 API route conventions
6. Add JSDoc comments
"""

async def generate_implementation(attempt_num: int, client: Anthropic) -> dict:
    """Generate one implementation attempt"""
    print(f"   Attempt {attempt_num}: Generating implementation...")

    try:
        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2000,
            messages=[{
                "role": "user",
                "content": f"{TASK_DESCRIPTION}\n\nProvide ONLY the TypeScript code, no explanations."
            }]
        )

        code = message.content[0].text

        # Score the implementation
        score = await score_implementation(code, client)

        return {
            "attempt": attempt_num,
            "code": code,
            "score": score,
            "model": message.model,
            "tokens": message.usage.input_tokens + message.usage.output_tokens
        }

    except Exception as e:
        print(f"   ❌ Attempt {attempt_num} failed: {e}")
        return {
            "attempt": attempt_num,
            "error": str(e),
            "score": 0
        }

async def score_implementation(code: str, client: Anthropic) -> dict:
    """Score an implementation on multiple criteria"""

    scoring_prompt = f"""
Rate this Next.js API health check implementation on a scale of 1-10 for each criterion.
Return ONLY a JSON object with scores, no explanation.

Code to evaluate:
```typescript
{code}
```

Criteria:
1. correctness - Does it meet all requirements?
2. typescript_quality - Proper types, interfaces, no 'any'?
3. error_handling - Comprehensive error handling?
4. code_style - Clean, readable, follows conventions?
5. documentation - Good JSDoc comments?

Return format: {{"correctness": 8, "typescript_quality": 9, ...}}
"""

    try:
        message = client.messages.create(
            model="claude-haiku-4-20250514",  # Use Haiku for scoring to save cost
            max_tokens=200,
            messages=[{"role": "user", "content": scoring_prompt}]
        )

        scores_text = message.content[0].text
        # Extract JSON from response
        import re
        json_match = re.search(r'\{[^}]+\}', scores_text)
        if json_match:
            scores = json.loads(json_match.group())
            total = sum(scores.values())
            scores['total'] = total
            return scores
        else:
            return {"error": "Could not parse scores", "total": 0}

    except Exception as e:
        print(f"   ⚠ Scoring failed: {e}")
        return {"error": str(e), "total": 0}

async def run_autopilot():
    """Run simplified autopilot test"""
    print("╔═══════════════════════════════════════════════════════════╗")
    print("║         Simplified Autopilot Test - Manual Review         ║")
    print("╚═══════════════════════════════════════════════════════════╝")
    print()
    print(f"📋 Task: Health Check API Endpoint")
    print(f"🔄 Attempts: {N_ATTEMPTS} parallel implementations")
    print(f"🎯 Goal: Generate code for manual review")
    print()

    # Initialize Anthropic client
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("❌ ANTHROPIC_API_KEY not set")
        sys.exit(1)

    client = Anthropic(api_key=api_key)

    # Run parallel attempts
    print("🚀 Generating implementations...")
    print()

    tasks = [generate_implementation(i+1, client) for i in range(N_ATTEMPTS)]
    results = await asyncio.gather(*tasks)

    # Filter successful results
    successful = [r for r in results if 'code' in r]

    if not successful:
        print("❌ All attempts failed")
        return

    print()
    print("📊 Scoring Results:")
    print()

    for result in successful:
        score = result.get('score', {})
        total = score.get('total', 0)
        print(f"   Attempt {result['attempt']}: Total Score = {total}/50")
        if 'correctness' in score:
            print(f"      • Correctness: {score.get('correctness', 0)}/10")
            print(f"      • TypeScript Quality: {score.get('typescript_quality', 0)}/10")
            print(f"      • Error Handling: {score.get('error_handling', 0)}/10")
            print(f"      • Code Style: {score.get('code_style', 0)}/10")
            print(f"      • Documentation: {score.get('documentation', 0)}/10")
        print()

    # Select best implementation
    best = max(successful, key=lambda r: r.get('score', {}).get('total', 0))

    print("=" * 60)
    print(f"🏆 Best Implementation: Attempt {best['attempt']}")
    print(f"   Score: {best['score']['total']}/50")
    print("=" * 60)
    print()

    # Save outputs
    output_dir = Path("autopilot_output")
    output_dir.mkdir(exist_ok=True)

    # Save best implementation
    best_file = output_dir / "health_check_BEST.ts"
    with open(best_file, 'w') as f:
        f.write(best['code'])
    print(f"✅ Best implementation saved: {best_file}")

    # Save all attempts for comparison
    for result in successful:
        attempt_file = output_dir / f"health_check_attempt_{result['attempt']}.ts"
        with open(attempt_file, 'w') as f:
            f.write(result['code'])
    print(f"✅ All attempts saved to: {output_dir}/")

    # Save detailed results
    results_file = output_dir / "results.json"
    with open(results_file, 'w') as f:
        json.dump({
            "task": TASK_DESCRIPTION,
            "timestamp": datetime.now().isoformat(),
            "attempts": N_ATTEMPTS,
            "successful": len(successful),
            "best_attempt": best['attempt'],
            "best_score": best['score'],
            "all_results": results
        }, f, indent=2)
    print(f"✅ Results saved: {results_file}")

    print()
    print("=" * 60)
    print("🎉 AUTOPILOT TEST COMPLETE - READY FOR MANUAL REVIEW")
    print("=" * 60)
    print()
    print("📁 Output Files:")
    print(f"   • {best_file} - Best implementation (USE THIS)")
    print(f"   • {output_dir}/health_check_attempt_*.ts - All attempts (compare)")
    print(f"   • {results_file} - Detailed scoring")
    print()
    print("🔍 Manual Review Checklist:")
    print("   1. Does it meet all requirements?")
    print("   2. TypeScript types correct?")
    print("   3. Error handling comprehensive?")
    print("   4. Would you deploy this to production?")
    print("   5. How does it compare to what you'd write manually?")
    print()
    print("📊 Cost Comparison:")
    total_tokens = sum(r.get('tokens', 0) for r in successful)
    print(f"   • Total tokens: {total_tokens}")
    print(f"   • Estimated cost: ~$0.15 (3 attempts)")
    print(f"   • Time saved vs manual: ~15-20 minutes")
    print()

if __name__ == "__main__":
    asyncio.run(run_autopilot())
