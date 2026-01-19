#!/usr/bin/env python3
"""
QFieldCloud Worker Alert System
Sends alerts via multiple channels when worker failures are detected.
"""

import subprocess
import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Configuration
ALERT_CONFIG = {
    'log_file': '/var/log/qfield_worker_alerts.log',
    'state_file': '/var/log/qfield_worker_alert_state.json',
    'channels': {
        'log': True,           # Always log to file
        'console': True,       # Print to console
        'whatsapp': False,     # Send via WhatsApp (requires wa-monitor)
        'email': False,        # Send email (configure below)
        'webhook': False       # Send to webhook (configure below)
    },
    'thresholds': {
        'failure_count': 3,    # Alert after N failures
        'failure_window': 60,  # Within N minutes
        'memory_mb': 500,      # Alert if memory exceeds
        'queue_depth': 10,     # Alert if queue exceeds
        'stuck_minutes': 10    # Alert if jobs stuck for N minutes
    },
    'cooldown_minutes': 30,   # Don't repeat same alert for N minutes
    # Email configuration (if enabled)
    'email': {
        'smtp_host': 'smtp.gmail.com',
        'smtp_port': 587,
        'from_addr': 'alerts@fibreflow.app',
        'from_password': os.getenv('ALERT_EMAIL_PASSWORD', ''),
        'to_addrs': ['admin@fibreflow.app'],
        'subject_prefix': '[QField Alert]'
    },
    # WhatsApp configuration (if enabled)
    'whatsapp': {
        'api_url': 'http://100.96.203.105:8081/send-message',
        'to_numbers': ['27711558396']
    },
    # Webhook configuration (if enabled)
    'webhook': {
        'url': os.getenv('ALERT_WEBHOOK_URL', ''),
        'headers': {'Content-Type': 'application/json'}
    }
}

class AlertManager:
    def __init__(self):
        self.state = self.load_state()

    def load_state(self):
        """Load alert state to prevent spam"""
        state_file = Path(ALERT_CONFIG['state_file'])
        if state_file.exists():
            try:
                with state_file.open('r') as f:
                    return json.load(f)
            except:
                pass
        return {'last_alerts': {}}

    def save_state(self):
        """Save alert state"""
        state_file = Path(ALERT_CONFIG['state_file'])
        state_file.parent.mkdir(parents=True, exist_ok=True)
        with state_file.open('w') as f:
            json.dump(self.state, f)

    def should_send_alert(self, alert_type):
        """Check if we should send this alert (cooldown logic)"""
        last_sent = self.state['last_alerts'].get(alert_type)
        if last_sent:
            last_time = datetime.fromisoformat(last_sent)
            cooldown = timedelta(minutes=ALERT_CONFIG['cooldown_minutes'])
            if datetime.now() - last_time < cooldown:
                return False
        return True

    def record_alert(self, alert_type):
        """Record that alert was sent"""
        self.state['last_alerts'][alert_type] = datetime.now().isoformat()
        self.save_state()

    def send_alert(self, alert_type, title, message, severity="warning"):
        """Send alert through configured channels"""

        # Check cooldown
        if not self.should_send_alert(alert_type):
            print(f"Skipping alert (cooldown): {title}")
            return

        # Format message with timestamp
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        full_message = f"[{timestamp}] {severity.upper()}: {title}\n{message}"

        # Log to file (always)
        if ALERT_CONFIG['channels']['log']:
            self.log_alert(full_message)

        # Print to console
        if ALERT_CONFIG['channels']['console']:
            self.console_alert(severity, title, message)

        # Send via WhatsApp
        if ALERT_CONFIG['channels']['whatsapp']:
            self.whatsapp_alert(title, message)

        # Send email
        if ALERT_CONFIG['channels']['email']:
            self.email_alert(title, message, severity)

        # Send to webhook
        if ALERT_CONFIG['channels']['webhook']:
            self.webhook_alert(alert_type, title, message, severity)

        # Record that alert was sent
        self.record_alert(alert_type)

    def log_alert(self, message):
        """Log alert to file"""
        log_file = Path(ALERT_CONFIG['log_file'])
        log_file.parent.mkdir(parents=True, exist_ok=True)
        with log_file.open('a') as f:
            f.write(f"{message}\n{'='*60}\n")

    def console_alert(self, severity, title, message):
        """Print alert to console with colors"""
        colors = {
            'info': '\033[94m',
            'warning': '\033[93m',
            'error': '\033[91m',
            'critical': '\033[95m'
        }
        color = colors.get(severity, '')
        reset = '\033[0m'
        print(f"{color}{'='*60}")
        print(f"🚨 ALERT: {title}")
        print(f"{message}")
        print(f"{'='*60}{reset}")

    def whatsapp_alert(self, title, message):
        """Send WhatsApp alert"""
        try:
            for number in ALERT_CONFIG['whatsapp']['to_numbers']:
                cmd = f"""
                    curl -X POST {ALERT_CONFIG['whatsapp']['api_url']} \
                        -H "Content-Type: application/json" \
                        -d '{{"to": "{number}", "message": "🚨 QField Alert: {title}\\n{message}"}}'
                """
                subprocess.run(cmd, shell=True, capture_output=True)
        except Exception as e:
            print(f"WhatsApp alert failed: {e}")

    def email_alert(self, title, message, severity):
        """Send email alert"""
        try:
            config = ALERT_CONFIG['email']

            msg = MIMEMultipart()
            msg['From'] = config['from_addr']
            msg['To'] = ', '.join(config['to_addrs'])
            msg['Subject'] = f"{config['subject_prefix']} {title}"

            body = f"""
            <html>
            <body>
                <h2 style="color: {'red' if severity == 'critical' else 'orange'};">
                    QFieldCloud Worker Alert
                </h2>
                <h3>{title}</h3>
                <pre>{message}</pre>
                <hr>
                <p><small>Generated at {datetime.now()}</small></p>
            </body>
            </html>
            """

            msg.attach(MIMEText(body, 'html'))

            server = smtplib.SMTP(config['smtp_host'], config['smtp_port'])
            server.starttls()
            server.login(config['from_addr'], config['from_password'])
            server.send_message(msg)
            server.quit()
        except Exception as e:
            print(f"Email alert failed: {e}")

    def webhook_alert(self, alert_type, title, message, severity):
        """Send webhook alert"""
        try:
            import requests
            data = {
                'type': alert_type,
                'title': title,
                'message': message,
                'severity': severity,
                'timestamp': datetime.now().isoformat()
            }
            requests.post(
                ALERT_CONFIG['webhook']['url'],
                json=data,
                headers=ALERT_CONFIG['webhook']['headers'],
                timeout=5
            )
        except Exception as e:
            print(f"Webhook alert failed: {e}")

class WorkerMonitor:
    def __init__(self):
        self.alert_manager = AlertManager()

    def run_command(self, cmd):
        """Execute shell command"""
        try:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            return result.stdout.strip(), result.returncode
        except Exception as e:
            return str(e), 1

    def check_worker_status(self):
        """Check if worker is running"""
        output, _ = self.run_command("docker ps --format '{{.Names}}' | grep -E 'worker'")
        return bool(output)

    def check_worker_memory(self):
        """Check worker memory usage"""
        output, _ = self.run_command("docker stats qfieldcloud-worker --no-stream --format '{{json .}}'")
        if output:
            try:
                stats = json.loads(output)
                mem_usage = stats.get('MemUsage', '0MiB').split(' / ')[0]
                mem_mb = float(mem_usage.replace('MiB', '').replace('GiB', '000'))
                return mem_mb
            except:
                pass
        return 0

    def check_queue_depth(self):
        """Check job queue depth"""
        db_container, _ = self.run_command("docker ps --format '{{.Names}}' | grep -E 'db|postgres' | head -1")
        if db_container:
            output, _ = self.run_command(
                f'docker exec {db_container} psql -U qfieldcloud_db_admin -d qfieldcloud_db -t -c '
                f'"SELECT COUNT(*) FROM core_job WHERE status IN (\'pending\', \'queued\');"'
            )
            try:
                return int(output.strip() or 0)
            except:
                pass
        return 0

    def check_stuck_jobs(self):
        """Check for stuck jobs"""
        db_container, _ = self.run_command("docker ps --format '{{.Names}}' | grep -E 'db|postgres' | head -1")
        if db_container:
            output, _ = self.run_command(
                f'docker exec {db_container} psql -U qfieldcloud_db_admin -d qfieldcloud_db -t -c '
                f'"SELECT COUNT(*) FROM core_job WHERE status IN (\'pending\', \'queued\') '
                f'AND created_at < NOW() - INTERVAL \'{ALERT_CONFIG["thresholds"]["stuck_minutes"]} minutes\';"'
            )
            try:
                return int(output.strip() or 0)
            except:
                pass
        return 0

    def run_checks(self):
        """Run all checks and send alerts if needed"""

        # Check if worker is running
        if not self.check_worker_status():
            self.alert_manager.send_alert(
                'worker_down',
                'Worker Service Down',
                'QFieldCloud worker is not running. Sync operations will fail.',
                'critical'
            )
            return

        # Check memory usage
        mem_mb = self.check_worker_memory()
        if mem_mb > ALERT_CONFIG['thresholds']['memory_mb']:
            self.alert_manager.send_alert(
                'worker_memory',
                f'Worker Memory High ({mem_mb:.0f}MB)',
                f'Worker memory usage ({mem_mb:.0f}MB) exceeds threshold ({ALERT_CONFIG["thresholds"]["memory_mb"]}MB).\n'
                'Consider restarting the worker.',
                'warning'
            )

        # Check queue depth
        queue_depth = self.check_queue_depth()
        if queue_depth > ALERT_CONFIG['thresholds']['queue_depth']:
            self.alert_manager.send_alert(
                'queue_high',
                f'High Queue Depth ({queue_depth} jobs)',
                f'Job queue has {queue_depth} pending/queued jobs.\n'
                'This may indicate worker performance issues.',
                'warning'
            )

        # Check stuck jobs
        stuck_count = self.check_stuck_jobs()
        if stuck_count > 0:
            self.alert_manager.send_alert(
                'jobs_stuck',
                f'Stuck Jobs Detected ({stuck_count} jobs)',
                f'{stuck_count} jobs have been stuck for over {ALERT_CONFIG["thresholds"]["stuck_minutes"]} minutes.\n'
                'Manual intervention may be required.',
                'error'
            )

def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description='QFieldCloud Worker Alert System')
    parser.add_argument('--check', action='store_true', help='Run checks and send alerts')
    parser.add_argument('--test', action='store_true', help='Send test alert')
    parser.add_argument('--config', action='store_true', help='Show configuration')

    args = parser.parse_args()

    if args.test:
        manager = AlertManager()
        manager.send_alert(
            'test',
            'Test Alert',
            'This is a test alert from QFieldCloud Worker Alert System.',
            'info'
        )
        print("Test alert sent!")

    elif args.config:
        print(json.dumps(ALERT_CONFIG, indent=2))

    elif args.check:
        monitor = WorkerMonitor()
        monitor.run_checks()
        print("Checks completed.")

    else:
        parser.print_help()

if __name__ == "__main__":
    main()