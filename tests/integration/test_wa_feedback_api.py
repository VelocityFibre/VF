#!/usr/bin/env python3
"""
Test script for WhatsApp feedback API endpoints
Tests both local and production endpoints
"""

import requests
import json
import sys
from typing import Dict, Any

# API endpoints
LOCAL_API = "http://localhost:3005"
PROD_API = "https://app.fibreflow.app"

def test_evaluate_endpoint(base_url: str, dr_number: str) -> Dict[str, Any]:
    """Test the evaluation endpoint"""
    url = f"{base_url}/api/foto/evaluate"

    print(f"Testing evaluation endpoint: {url}")

    try:
        response = requests.post(
            url,
            json={"dr_number": dr_number},
            headers={"Content-Type": "application/json"},
            timeout=180
        )

        if response.status_code == 200:
            result = response.json()
            print(f"✅ Evaluation successful: {result.get('success', False)}")
            if result.get('data'):
                print(f"   Status: {result['data'].get('overall_status')}")
                print(f"   Score: {result['data'].get('average_score')}/10")
            return result
        else:
            print(f"❌ HTTP Error {response.status_code}: {response.text[:200]}")
            return {"success": False, "error": f"HTTP {response.status_code}"}
    except requests.exceptions.Timeout:
        print(f"❌ Request timed out after 180 seconds")
        return {"success": False, "error": "Timeout"}
    except Exception as e:
        print(f"❌ Error: {e}")
        return {"success": False, "error": str(e)}

def test_feedback_endpoint(base_url: str, dr_number: str, message: str) -> bool:
    """Test the feedback sending endpoint"""
    url = f"{base_url}/api/foto/feedback"

    print(f"Testing feedback endpoint: {url}")

    try:
        response = requests.post(
            url,
            json={
                "dr_number": dr_number,
                "message": message,
                "evaluation": {
                    "dr_number": dr_number,
                    "overall_status": "PASS",
                    "average_score": 8
                }
            },
            headers={"Content-Type": "application/json"},
            timeout=30
        )

        if response.status_code == 200:
            result = response.json()
            success = result.get('success', False)
            print(f"✅ Feedback sent: {success}" if success else f"❌ Feedback failed: {result.get('error')}")
            return success
        else:
            print(f"❌ HTTP Error {response.status_code}: {response.text[:200]}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_evaluations_list(base_url: str) -> bool:
    """Test the evaluations list endpoint"""
    url = f"{base_url}/api/foto/evaluations"

    print(f"Testing evaluations list endpoint: {url}")

    try:
        response = requests.get(url, timeout=30)

        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                count = len(result.get('data', []))
                print(f"✅ Found {count} evaluations")
                return True
            else:
                print(f"❌ Failed to get evaluations: {result.get('error')}")
                return False
        else:
            print(f"❌ HTTP Error {response.status_code}: {response.text[:200]}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    """Main test function"""
    print("="*60)
    print("WhatsApp Feedback API Test")
    print("="*60)

    # Select environment
    if len(sys.argv) > 1 and sys.argv[1] == "--prod":
        base_url = PROD_API
        print(f"Testing PRODUCTION API: {base_url}")
    else:
        base_url = LOCAL_API
        print(f"Testing LOCAL API: {base_url}")
        print("Use --prod flag to test production API")

    print("-"*60)

    # Test DR number
    dr_number = "DR1730550"
    if len(sys.argv) > 2:
        dr_number = sys.argv[2]

    print(f"Test DR Number: {dr_number}\n")

    # Test 1: Check evaluations list
    print("1. Testing evaluations list...")
    test_evaluations_list(base_url)
    print()

    # Test 2: Evaluate a DR
    print("2. Testing DR evaluation...")
    eval_result = test_evaluate_endpoint(base_url, dr_number)
    print()

    # Test 3: Send feedback
    if eval_result.get('success'):
        print("3. Testing feedback sending...")
        test_message = f"✅ QA PASSED\\nDR: {dr_number}\\nScore: 8/10\\n\\nTest feedback message"
        test_feedback_endpoint(base_url, dr_number, test_message)
    else:
        print("3. Skipping feedback test (evaluation failed)")

    print("\n" + "="*60)
    print("Test complete!")
    print("="*60)

if __name__ == "__main__":
    main()