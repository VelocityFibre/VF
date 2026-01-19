"""
The SIMPLEST Inngest function - checks GitHub and does a calculation
"""

import sys
import os
import requests
import random
from datetime import datetime

# Setup paths
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from inngest import TriggerEvent
from client import inngest_client

@inngest_client.create_function(
    fn_id="simple-github-check",
    trigger=TriggerEvent(event="test/check.github"),
    retries=3  # Will retry 3 times if it fails
)
async def check_github(ctx, step):
    """Check if GitHub is accessible"""

    # Step 1: Check GitHub
    github_status = await step.run(
        "check-github",
        lambda: check_github_api()
    )

    # Step 2: Do a calculation
    calc_result = await step.run(
        "do-calculation",
        lambda: random_calculation()
    )

    return {
        "github": github_status,
        "calculation": calc_result,
        "time": datetime.now().isoformat()
    }

def check_github_api():
    """Check GitHub's API"""
    try:
        response = requests.get("https://api.github.com", timeout=5)
        if response.status_code == 200:
            return "✅ GitHub is UP!"
        else:
            return f"⚠️ GitHub returned {response.status_code}"
    except Exception as e:
        return f"❌ Cannot reach GitHub: {e}"

def random_calculation():
    """A calculation that sometimes 'fails' to show retries"""
    # 30% chance of "failure" to demonstrate retries
    if random.random() < 0.3:
        raise Exception("🎲 Random failure - this will retry!")

    # Otherwise return a calculation
    result = random.randint(1, 100) * 42
    return f"✅ Calculation complete: {result}"

# Export for app.py
simple_check_functions = [check_github]