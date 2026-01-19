#!/usr/bin/env python3
"""
Simple Dashboard Generator - Single Best Implementation
Faster approach for Week 1 PoC
"""
import os
import sys
from pathlib import Path
from anthropic import Anthropic

def main():
    # Load specification
    spec_file = Path(__file__).parent / "contractor_dashboard_spec.md"
    with open(spec_file, 'r') as f:
        spec = f.read()

    # Initialize client
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("❌ ANTHROPIC_API_KEY not set")
        sys.exit(1)

    client = Anthropic(api_key=api_key)

    print("╔═══════════════════════════════════════════════════════════╗")
    print("║      Contractor Dashboard - Single Best Implementation     ║")
    print("╚═══════════════════════════════════════════════════════════╝")
    print()
    print("📋 Generating production-quality contractor dashboard...")
    print()

    # Generate dashboard
    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=8000,
        messages=[{
            "role": "user",
            "content": f"""{spec}

Generate a COMPLETE, production-ready Contractor Dashboard implementation.

Output ONLY the complete TypeScript/TSX code for pages/contractors/dashboard.tsx
Include ALL components inline (metrics, chart, table, timeline).
Use Recharts for charting, Tailwind for styling, mock data from spec.
"""
        }],
        system="You are an expert Next.js/TypeScript/Tailwind developer building production-quality dashboards."
    )

    code = message.content[0].text

    # Clean code blocks
    if '```' in code:
        code = code.split('```')[1]
        if code.startswith('typescript') or code.startswith('tsx'):
            code = '\n'.join(code.split('\n')[1:])

    # Save output
    output_dir = Path("dashboard_output")
    output_dir.mkdir(exist_ok=True)

    output_file = output_dir / "dashboard.tsx"
    with open(output_file, 'w') as f:
        f.write(code)

    print(f"✅ Dashboard generated: {output_file}")
    print(f"📊 Tokens used: {message.usage.input_tokens + message.usage.output_tokens}")
    print()
    print("🚀 Next: Copy to FibreFlow")
    print(f"   scp {output_file} velo@100.96.203.105:~/fibreflow-louis/pages/contractors/dashboard.tsx")

if __name__ == "__main__":
    main()
