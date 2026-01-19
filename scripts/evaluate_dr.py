#!/usr/bin/env python3
"""
Direct DR Evaluation Script
Evaluates a specific DR number and returns formatted feedback
"""

import json
import sys
import subprocess
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

VF_SERVER_HOST = os.getenv('VF_SERVER_HOST', '100.96.203.105')
VF_SERVER_USER = os.getenv('VF_SERVER_USER', 'louis')
VF_SERVER_PASSWORD = os.getenv('VF_SERVER_PASSWORD', 'VeloAdmin2025!')

def execute_on_server(command: str, timeout: int = 180):
    """Execute command on VF server via SSH"""
    try:
        if VF_SERVER_PASSWORD:
            result = subprocess.run(
                ['sshpass', '-p', VF_SERVER_PASSWORD, 'ssh',
                 '-o', 'StrictHostKeyChecking=no',
                 '-o', 'IdentitiesOnly=yes',
                 '-o', 'PubkeyAuthentication=no',
                 f'{VF_SERVER_USER}@{VF_SERVER_HOST}', command],
                capture_output=True, text=True, timeout=timeout
            )
        else:
            result = subprocess.run(
                ['ssh', f'{VF_SERVER_USER}@{VF_SERVER_HOST}', command],
                capture_output=True, text=True, timeout=timeout
            )

        return {
            'success': result.returncode == 0,
            'output': result.stdout,
            'error': result.stderr if result.stderr else None
        }
    except subprocess.TimeoutExpired:
        return {'success': False, 'error': f'Command timed out after {timeout} seconds'}
    except Exception as e:
        return {'success': False, 'error': str(e)}

def evaluate_dr(dr_number: str):
    """Evaluate a DR and return the results"""
    print(f"Evaluating {dr_number}...")

    # First check if already evaluated
    check_command = f'curl -s localhost:3005/api/foto/evaluation/{dr_number}'
    result = execute_on_server(check_command, timeout=10)

    if result['success']:
        try:
            data = json.loads(result['output'])
            if data.get('success') and 'data' in data:
                print("DR already evaluated, returning existing evaluation")
                return data['data']
        except:
            pass

    # Perform new evaluation
    eval_command = f'''curl -X POST localhost:3005/api/foto/evaluate \\
        -H "Content-Type: application/json" \\
        -d '{{"dr_number": "{dr_number}"}}' --max-time 180'''

    print("Starting evaluation (this may take up to 3 minutes)...")
    result = execute_on_server(eval_command, timeout=200)

    if not result['success']:
        print(f"Error: {result['error']}")
        return None

    try:
        data = json.loads(result['output'])
        if data.get('success'):
            return data['data']
        else:
            print(f"Evaluation failed: {data.get('error', 'Unknown error')}")
            return None
    except json.JSONDecodeError as e:
        print(f"Failed to parse response: {e}")
        print(f"Raw response: {result['output'][:500]}")
        return None

def format_feedback(evaluation):
    """Format evaluation results as WhatsApp message"""
    if not evaluation:
        return None

    dr_number = evaluation['dr_number']
    status = evaluation['overall_status']
    score = evaluation['average_score']
    passed = evaluation['passed_steps']
    total = evaluation['total_steps']

    # Build feedback message
    if status == 'PASS':
        emoji = "✅"
        header = f"{emoji} *QA PASSED*"
    elif status == 'PARTIAL':
        emoji = "⚠️"
        header = f"{emoji} *QA PARTIAL PASS*"
    else:
        emoji = "❌"
        header = f"{emoji} *QA FAILED*"

    message = f"{header}\nDR: {dr_number}\n\n"
    message += f"📊 Overall Score: {score}/10\n"
    message += f"✔️ Steps Passed: {passed}/{total}\n\n"

    # Add step details if available
    if 'steps' in evaluation and evaluation['steps']:
        message += "*Detailed Results:*\n"
        for i, step in enumerate(evaluation['steps'], 1):
            step_emoji = "✓" if step.get('passed', False) else "✗"
            step_name = step.get('name', f'Step {i}')
            step_score = step.get('score', 0)
            message += f"{step_emoji} {step_name}: {step_score}/10\n"

            if step.get('issues'):
                for issue in step['issues']:
                    message += f"  ↳ {issue}\n"

    # Add recommendations
    message += "\n*Recommendations:*\n"
    if status == 'PASS':
        message += "✅ Good work! All quality standards met.\n"
    elif status == 'PARTIAL':
        message += "⚠️ Please review and address the noted issues.\n"
    else:
        message += "❌ Significant issues found. Please rework and resubmit.\n"

    return message

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 evaluate_dr.py <DR_NUMBER>")
        print("Example: python3 evaluate_dr.py DR1730550")
        sys.exit(1)

    dr_number = sys.argv[1]

    # Validate DR format
    if not dr_number.startswith('DR'):
        print(f"Error: Invalid DR number format. Must start with 'DR'")
        sys.exit(1)

    # Evaluate
    evaluation = evaluate_dr(dr_number)

    if evaluation:
        print("\n" + "="*60)
        print("EVALUATION RESULTS")
        print("="*60)
        print(f"DR Number: {evaluation['dr_number']}")
        print(f"Status: {evaluation['overall_status']}")
        print(f"Score: {evaluation['average_score']}/10")
        print(f"Passed Steps: {evaluation['passed_steps']}/{evaluation['total_steps']}")
        print(f"Feedback Sent: {evaluation.get('feedback_sent', False)}")

        # Format and display WhatsApp message
        print("\n" + "="*60)
        print("WHATSAPP FEEDBACK MESSAGE")
        print("="*60)
        feedback = format_feedback(evaluation)
        if feedback:
            print(feedback)

        # Save results to file
        filename = f"evaluation_{dr_number}.json"
        with open(filename, 'w') as f:
            json.dump({
                'evaluation': evaluation,
                'feedback': feedback
            }, f, indent=2)
        print(f"\nResults saved to: {filename}")

        # Return success
        sys.exit(0)
    else:
        print("Evaluation failed")
        sys.exit(1)

if __name__ == "__main__":
    main()