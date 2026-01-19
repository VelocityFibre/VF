#!/usr/bin/env python3
"""
Trigger VLM evaluation for a DR number
"""

import requests
import json
import sys
import time

VF_SERVER = "100.96.203.105"

def trigger_evaluation(dr_number):
    """Trigger VLM evaluation for a DR"""
    print(f"\n🚀 Triggering evaluation for {dr_number}...")

    url = f"http://{VF_SERVER}:3005/api/foto/evaluate"
    payload = {"dr_number": dr_number}

    try:
        response = requests.post(url, json=payload, timeout=60)

        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                result = data.get('data', {})
                print(f"✅ Evaluation complete!")
                print(f"   Status: {result.get('overall_status', 'Unknown')}")
                print(f"   Score: {result.get('average_score', 0)}/10")
                print(f"   Steps: {result.get('passed_steps', 0)}/{result.get('total_steps', 0)} passed")

                # Check if already has feedback
                if result.get('feedback_sent'):
                    print(f"   ℹ️  Feedback already sent on {result.get('feedback_sent_at', 'Unknown')}")
                else:
                    print(f"   📝 Ready for human review at:")
                    print(f"      http://{VF_SERVER}:3005/foto-reviews")

                return True
            else:
                print(f"❌ Evaluation failed: {data.get('message', 'Unknown error')}")
                return False
        else:
            print(f"❌ HTTP Error {response.status_code}")
            print(response.text[:500])
            return False

    except requests.Timeout:
        print("❌ Request timed out (VLM processing can take 15-30 seconds)")
        return False
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

def check_evaluation(dr_number):
    """Check if evaluation exists"""
    url = f"http://{VF_SERVER}:3005/api/foto/evaluation/{dr_number}"

    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data.get('success') and data.get('data'):
                result = data['data']
                print(f"\n📊 Existing evaluation found:")
                print(f"   Status: {result.get('overall_status', 'Unknown')}")
                print(f"   Score: {result.get('average_score', 0)}/10")
                print(f"   Date: {result.get('evaluation_date', 'Unknown')}")
                print(f"   Feedback Sent: {result.get('feedback_sent', False)}")
                return True
        return False
    except:
        return False

def main():
    if len(sys.argv) != 2:
        print("Usage: python trigger_evaluation.py DR_NUMBER")
        print("Example: python trigger_evaluation.py DR1234567")
        sys.exit(1)

    dr_number = sys.argv[1]

    # Check if already evaluated
    if check_evaluation(dr_number):
        print("\n⚠️  This DR has already been evaluated.")
        response = input("Re-evaluate? (y/n): ")
        if response.lower() != 'y':
            print("Cancelled.")
            sys.exit(0)

    # Trigger evaluation
    print(f"\n⏳ Starting VLM evaluation (this takes 15-30 seconds)...")
    start_time = time.time()

    success = trigger_evaluation(dr_number)

    elapsed = time.time() - start_time
    print(f"\n⏱️  Completed in {elapsed:.1f} seconds")

    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()