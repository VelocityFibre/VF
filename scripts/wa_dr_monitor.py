#!/usr/bin/env python3
"""
WhatsApp DR Monitoring and Evaluation System
Monitors for new DR submissions, evaluates images, and prepares feedback
"""

import json
import time
import subprocess
import logging
from datetime import datetime
from typing import Dict, List, Optional, Set
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
VF_SERVER_HOST = os.getenv('VF_SERVER_HOST', '100.96.203.105')
VF_SERVER_USER = os.getenv('VF_SERVER_USER', 'louis')
VF_SERVER_PASSWORD = os.getenv('VF_SERVER_PASSWORD', 'VeloAdmin2025!')
POLL_INTERVAL = 30  # seconds
EVALUATION_TIMEOUT = 180  # seconds

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('wa_dr_monitor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class WaDrMonitor:
    def __init__(self):
        self.processed_drs: Set[str] = set()
        self.pending_evaluations: Dict[str, Dict] = {}

    def execute_on_server(self, command: str) -> Dict:
        """Execute command on VF server via SSH"""
        try:
            if VF_SERVER_PASSWORD:
                result = subprocess.run(
                    ['sshpass', '-p', VF_SERVER_PASSWORD, 'ssh',
                     '-o', 'StrictHostKeyChecking=no',
                     '-o', 'ConnectTimeout=10',
                     f'{VF_SERVER_USER}@{VF_SERVER_HOST}', command],
                    capture_output=True, text=True, timeout=30
                )
            else:
                result = subprocess.run(
                    ['ssh', f'{VF_SERVER_USER}@{VF_SERVER_HOST}', command],
                    capture_output=True, text=True, timeout=30
                )

            return {
                'success': result.returncode == 0,
                'output': result.stdout,
                'error': result.stderr if result.stderr else None
            }
        except subprocess.TimeoutExpired:
            return {'success': False, 'error': 'Command timed out'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def get_all_drs(self) -> List[Dict]:
        """Fetch all DRs with photos from the API"""
        logger.info("Fetching all DRs with photos...")

        command = 'curl -s localhost:3005/api/foto/photos'
        result = self.execute_on_server(command)

        if not result['success']:
            logger.error(f"Failed to fetch DRs: {result['error']}")
            return []

        try:
            data = json.loads(result['output'])
            if data.get('success') and 'data' in data:
                drs = data['data']
                logger.info(f"Found {len(drs)} total DRs")
                return drs
            else:
                logger.error(f"API returned error: {data.get('message', 'Unknown error')}")
                return []
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse API response: {e}")
            return []

    def check_evaluation_status(self, dr_number: str) -> Optional[Dict]:
        """Check if a DR has already been evaluated"""
        logger.debug(f"Checking evaluation status for {dr_number}")

        command = f'curl -s localhost:3005/api/foto/evaluation/{dr_number}'
        result = self.execute_on_server(command)

        if not result['success']:
            return None

        try:
            data = json.loads(result['output'])
            if data.get('success') and 'data' in data:
                return data['data']
            return None
        except:
            return None

    def evaluate_dr(self, dr_number: str) -> Optional[Dict]:
        """Evaluate a DR's images"""
        logger.info(f"Starting evaluation for {dr_number}")

        # Use a background process for long-running evaluation
        command = f'''curl -X POST localhost:3005/api/foto/evaluate \\
            -H "Content-Type: application/json" \\
            -d '{{"dr_number": "{dr_number}"}}'"""

        # Execute with longer timeout
        try:
            if VF_SERVER_PASSWORD:
                result = subprocess.run(
                    ['sshpass', '-p', VF_SERVER_PASSWORD, 'ssh',
                     '-o', 'StrictHostKeyChecking=no',
                     f'{VF_SERVER_USER}@{VF_SERVER_HOST}', command],
                    capture_output=True, text=True, timeout=EVALUATION_TIMEOUT
                )
            else:
                result = subprocess.run(
                    ['ssh', f'{VF_SERVER_USER}@{VF_SERVER_HOST}', command],
                    capture_output=True, text=True, timeout=EVALUATION_TIMEOUT
                )

            if result.returncode == 0:
                data = json.loads(result.stdout)
                if data.get('success'):
                    logger.info(f"Evaluation complete for {dr_number}")
                    logger.info(f"  Status: {data['data']['overall_status']}")
                    logger.info(f"  Score: {data['data']['average_score']}/10")
                    logger.info(f"  Steps: {data['data']['passed_steps']}/{data['data']['total_steps']}")
                    return data['data']
                else:
                    logger.error(f"Evaluation failed: {data.get('error', 'Unknown error')}")
            else:
                logger.error(f"Command failed: {result.stderr}")

        except subprocess.TimeoutExpired:
            logger.warning(f"Evaluation timed out for {dr_number} after {EVALUATION_TIMEOUT}s")
        except Exception as e:
            logger.error(f"Evaluation error: {e}")

        return None

    def prepare_feedback_message(self, evaluation: Dict) -> str:
        """Prepare WhatsApp feedback message for human review"""
        dr_number = evaluation['dr_number']
        status = evaluation['overall_status']
        score = evaluation['average_score']
        passed = evaluation['passed_steps']
        total = evaluation['total_steps']

        # Build feedback message
        if status == 'PASS':
            emoji = "✅"
            message = f"{emoji} *QA PASSED* - {dr_number}\n\n"
        elif status == 'PARTIAL':
            emoji = "⚠️"
            message = f"{emoji} *QA PARTIAL* - {dr_number}\n\n"
        else:
            emoji = "❌"
            message = f"{emoji} *QA FAILED* - {dr_number}\n\n"

        message += f"Score: {score}/10\n"
        message += f"Steps Passed: {passed}/{total}\n\n"

        # Add detailed feedback for each step
        if 'steps' in evaluation:
            message += "*Detailed Results:*\n"
            for step in evaluation['steps']:
                step_emoji = "✓" if step['passed'] else "✗"
                message += f"{step_emoji} {step['name']}: {step['score']}/10\n"
                if step.get('issues'):
                    for issue in step['issues']:
                        message += f"  - {issue}\n"

        message += "\n_Please review and approve/adjust this feedback before sending._"

        return message

    def send_feedback(self, dr_number: str) -> bool:
        """Mark feedback as sent for a DR"""
        logger.info(f"Marking feedback as sent for {dr_number}")

        command = f'''curl -X POST localhost:3005/api/foto/feedback \\
            -H "Content-Type: application/json" \\
            -d '{{"dr_number": "{dr_number}"}}'"""

        result = self.execute_on_server(command)

        if result['success']:
            try:
                data = json.loads(result['output'])
                if data.get('success'):
                    logger.info(f"Feedback marked as sent for {dr_number}")
                    return True
            except:
                pass

        logger.error(f"Failed to mark feedback as sent for {dr_number}")
        return False

    def process_new_drs(self):
        """Process any new DRs that haven't been evaluated"""
        drs = self.get_all_drs()

        new_drs = []
        for dr in drs:
            dr_number = dr['dr_number']

            # Skip if already processed
            if dr_number in self.processed_drs:
                continue

            # Check if already evaluated
            existing_eval = self.check_evaluation_status(dr_number)
            if existing_eval:
                self.processed_drs.add(dr_number)
                if not existing_eval.get('feedback_sent'):
                    logger.info(f"Found unevaluated DR: {dr_number} (already evaluated, needs feedback)")
                    # Prepare feedback for human review
                    feedback = self.prepare_feedback_message(existing_eval)
                    logger.info(f"Feedback prepared for {dr_number}:\n{feedback}\n")
                continue

            # New DR that needs evaluation
            new_drs.append(dr_number)

        if new_drs:
            logger.info(f"Found {len(new_drs)} new DRs to evaluate: {', '.join(new_drs)}")

            for dr_number in new_drs:
                logger.info(f"Evaluating {dr_number}...")
                evaluation = self.evaluate_dr(dr_number)

                if evaluation:
                    self.processed_drs.add(dr_number)

                    # Prepare feedback for human review
                    feedback = self.prepare_feedback_message(evaluation)
                    logger.info(f"Feedback prepared for {dr_number}:\n{feedback}\n")

                    # Store for human approval
                    self.pending_evaluations[dr_number] = {
                        'evaluation': evaluation,
                        'feedback': feedback,
                        'timestamp': datetime.now().isoformat()
                    }
                else:
                    logger.warning(f"Failed to evaluate {dr_number}, will retry later")
        else:
            logger.debug("No new DRs to process")

    def run(self):
        """Main monitoring loop"""
        logger.info("Starting WA DR Monitor...")
        logger.info(f"Polling interval: {POLL_INTERVAL} seconds")
        logger.info(f"Server: {VF_SERVER_USER}@{VF_SERVER_HOST}")

        while True:
            try:
                self.process_new_drs()

                # Display pending evaluations for human review
                if self.pending_evaluations:
                    logger.info(f"\n{'='*50}")
                    logger.info(f"PENDING HUMAN REVIEW: {len(self.pending_evaluations)} evaluations")
                    logger.info(f"{'='*50}")
                    for dr_number, data in self.pending_evaluations.items():
                        logger.info(f"DR: {dr_number}")
                        logger.info(f"Time: {data['timestamp']}")
                        logger.info(f"Status: {data['evaluation']['overall_status']}")
                        logger.info(f"{'='*50}\n")

                logger.info(f"Sleeping for {POLL_INTERVAL} seconds...")
                time.sleep(POLL_INTERVAL)

            except KeyboardInterrupt:
                logger.info("Monitoring stopped by user")
                break
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                time.sleep(POLL_INTERVAL)

def main():
    monitor = WaDrMonitor()
    monitor.run()

if __name__ == "__main__":
    main()