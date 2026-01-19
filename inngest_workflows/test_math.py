#!/usr/bin/env python3
"""
SIMPLEST TEST EVER - Just does math
No servers, no network, just shows retries!
"""

import random

def do_simple_math():
    """Math that sometimes 'fails' to show retries"""

    # Roll the dice
    dice = random.randint(1, 10)

    # 40% chance of "failure"
    if dice <= 4:
        print(f"  🎲 Rolled {dice} - Oops, 'failed'! (This will retry)")
        raise Exception("Math error - will retry!")

    # Success!
    result = dice * 100
    print(f"  🎲 Rolled {dice} - Success! Result = {result}")
    return result

# Test it
print("\n🧮 SIMPLE MATH TEST")
print("==================")
print("This function fails 40% of the time on purpose")
print("to show how Inngest retries automatically!\n")

for i in range(3):
    print(f"Attempt {i+1}:")
    try:
        result = do_simple_math()
        print(f"  ✅ Success! Got {result}\n")
    except Exception as e:
        print(f"  ❌ Failed: {e}\n")

print("👆 Without Inngest, failures just fail")
print("👇 With Inngest, it retries automatically!")