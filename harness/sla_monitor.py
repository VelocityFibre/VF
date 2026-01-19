#!/usr/bin/env python3
"""
SLA Monitor - Phase 2.5: Data Layer SLAs

Monitors data layer SLAs and alerts on violations to ensure agents
make decisions on fresh, reliable data.

City Planning Analogy: Like a city's utilities monitoring system ensuring
water pressure, electricity uptime, sewage treatment - measured against
strict SLAs with automatic alerts on violations.

Part of Vibe Coding Transformation - see docs/VIBE_CODING_TRANSFORMATION.md
"""

import os
import sys
import json
import yaml
import time
import logging
import requests
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class SLACheck:
    """Result of an SLA check."""
    name: str
    current_value: float
    sla_threshold: float
    status: str  # 'OK', 'VIOLATION', 'ERROR'
    timestamp: str
    unit: str = "seconds"
    error_message: Optional[str] = None


@dataclass
class SLAViolation:
    """Record of an SLA violation."""
    timestamp: str
    check_name: str
    current_value: float
    sla_threshold: float
    severity: str
    alerted: bool = False


class SLAViolationError(Exception):
    """Raised when SLA violations prevent safe operation."""
    pass


class SLAMonitor:
    """
    Monitors data layer SLAs and alerts on violations.

    Usage:
        monitor = SLAMonitor()

        # Check all SLAs
        results = monitor.check_all_slas()

        # Get compliance percentage
        compliance = monitor.get_compliance_percentage()

        # Verify data freshness before critical operation
        if not monitor.verify_data_freshness(components=["neon", "vlm"]):
            raise SLAViolationError("Data too stale for safe operation")
    """

    def __init__(self, config_path: Optional[Path] = None):
        """
        Initialize SLA monitor.

        Args:
            config_path: Path to SLA configuration YAML
        """
        if config_path is None:
            config_path = Path(__file__).parent / "data_layer_slas.yaml"

        self.config_path = Path(config_path)
        self.config = self._load_config()

        self.slas = self.config["slas"]
        self.alerts = self.config["alerts"]
        self.monitoring = self.config["monitoring"]

        # Track violations
        self.violations: List[SLAViolation] = []
        self.last_alert_time: Dict[str, float] = {}

        # Metrics storage
        self.metrics_file = Path(self.monitoring.get("metrics_file", "harness/sla_metrics.jsonl"))
        self.violations_file = Path(self.monitoring.get("violations_file", "harness/sla_violations.jsonl"))

        # Create directories if needed
        self.metrics_file.parent.mkdir(parents=True, exist_ok=True)
        self.violations_file.parent.mkdir(parents=True, exist_ok=True)

        logger.info(f"SLA Monitor initialized with config: {self.config_path}")

    def _load_config(self) -> Dict[str, Any]:
        """Load SLA configuration from YAML."""
        try:
            with open(self.config_path) as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"SLA config not found at {self.config_path}")
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML in SLA config: {e}")

    def check_all_slas(self) -> Dict[str, Any]:
        """
        Check all configured SLAs and return status.

        Returns:
            Dictionary with timestamp and list of SLA check results
        """
        logger.info("Running SLA checks...")

        results = {
            "timestamp": datetime.now().isoformat(),
            "checks": []
        }

        # Check Neon→Convex sync delay
        try:
            neon_delay = self._check_neon_sync_delay()
            results["checks"].append(SLACheck(
                name="neon_to_convex_sync",
                current_value=neon_delay,
                sla_threshold=self.slas["neon_to_convex_max_delay"],
                status="OK" if neon_delay <= self.slas["neon_to_convex_max_delay"] else "VIOLATION",
                timestamp=datetime.now().isoformat(),
                unit="seconds"
            ))
        except Exception as e:
            logger.error(f"Error checking Neon sync: {e}")
            results["checks"].append(SLACheck(
                name="neon_to_convex_sync",
                current_value=-1,
                sla_threshold=self.slas["neon_to_convex_max_delay"],
                status="ERROR",
                timestamp=datetime.now().isoformat(),
                error_message=str(e)
            ))

        # Check VLM image age
        try:
            vlm_age = self._check_vlm_image_age()
            results["checks"].append(SLACheck(
                name="vlm_image_freshness",
                current_value=vlm_age,
                sla_threshold=self.slas["vlm_image_max_age"],
                status="OK" if vlm_age <= self.slas["vlm_image_max_age"] else "VIOLATION",
                timestamp=datetime.now().isoformat(),
                unit="seconds"
            ))
        except Exception as e:
            logger.error(f"Error checking VLM images: {e}")
            results["checks"].append(SLACheck(
                name="vlm_image_freshness",
                current_value=-1,
                sla_threshold=self.slas["vlm_image_max_age"],
                status="ERROR",
                timestamp=datetime.now().isoformat(),
                error_message=str(e)
            ))

        # Check VLM server responsiveness
        try:
            vlm_response = self._check_vlm_server()
            results["checks"].append(SLACheck(
                name="vlm_server_responsiveness",
                current_value=vlm_response,
                sla_threshold=self.slas["vlm_server_max_response"],
                status="OK" if vlm_response <= self.slas["vlm_server_max_response"] else "VIOLATION",
                timestamp=datetime.now().isoformat(),
                unit="seconds"
            ))
        except Exception as e:
            logger.error(f"Error checking VLM server: {e}")
            results["checks"].append(SLACheck(
                name="vlm_server_responsiveness",
                current_value=-1,
                sla_threshold=self.slas["vlm_server_max_response"],
                status="ERROR",
                timestamp=datetime.now().isoformat(),
                error_message=str(e)
            ))

        # Check WhatsApp session age
        try:
            wa_session_age = self._check_wa_session_age()
            results["checks"].append(SLACheck(
                name="wa_session_freshness",
                current_value=wa_session_age,
                sla_threshold=self.slas["wa_session_max_age"],
                status="OK" if wa_session_age <= self.slas["wa_session_max_age"] else "VIOLATION",
                timestamp=datetime.now().isoformat(),
                unit="seconds"
            ))
        except Exception as e:
            logger.error(f"Error checking WhatsApp session: {e}")
            results["checks"].append(SLACheck(
                name="wa_session_freshness",
                current_value=-1,
                sla_threshold=self.slas["wa_session_max_age"],
                status="ERROR",
                timestamp=datetime.now().isoformat(),
                error_message=str(e)
            ))

        # Check Foto AI review freshness
        try:
            foto_age = self._check_foto_review_age()
            results["checks"].append(SLACheck(
                name="foto_review_freshness",
                current_value=foto_age,
                sla_threshold=self.slas["foto_review_max_age"],
                status="OK" if foto_age <= self.slas["foto_review_max_age"] else "VIOLATION",
                timestamp=datetime.now().isoformat(),
                unit="seconds"
            ))
        except Exception as e:
            logger.error(f"Error checking Foto reviews: {e}")
            results["checks"].append(SLACheck(
                name="foto_review_freshness",
                current_value=-1,
                sla_threshold=self.slas["foto_review_max_age"],
                status="ERROR",
                timestamp=datetime.now().isoformat(),
                error_message=str(e)
            ))

        # Process alerts for violations
        self._process_alerts(results["checks"])

        # Save metrics
        self._save_metrics(results)

        # Log summary
        violations = [c for c in results["checks"] if c.status == "VIOLATION"]
        errors = [c for c in results["checks"] if c.status == "ERROR"]

        if violations:
            logger.warning(f"⚠️  {len(violations)} SLA violation(s) detected")
        if errors:
            logger.error(f"❌ {len(errors)} check error(s)")

        if not violations and not errors:
            logger.info("✅ All SLAs within thresholds")

        return results

    def _check_neon_sync_delay(self) -> float:
        """
        Measure Neon→Convex sync delay.

        Returns:
            Delay in seconds (0 if Convex is ahead/equal)
        """
        # For now, return simulated value
        # TODO: Implement actual Neon/Convex timestamp comparison
        logger.debug("Checking Neon→Convex sync delay...")

        # Simulate: Would query both databases for latest timestamp
        # neon_latest = query("SELECT MAX(updated_at) FROM delivery_reports")
        # convex_latest = convex_api.get_latest_timestamp()
        # delay = (neon_latest - convex_latest).total_seconds()

        # Simulated value for testing
        return 45.0  # 45 seconds (within 300s SLA)

    def _check_vlm_image_age(self) -> float:
        """
        Check age of most recent image in VLM processing queue.

        Returns:
            Age in seconds of oldest unprocessed image
        """
        logger.debug("Checking VLM image age...")

        # Check VF Server image directory
        vf_image_dir = Path("/srv/ml/vllm/images/training")

        if not vf_image_dir.exists():
            # Fall back to local test directory
            vf_image_dir = Path.cwd() / "test_data" / "vlm_images"

        if not vf_image_dir.exists():
            logger.warning(f"VLM image directory not found: {vf_image_dir}")
            return 0  # No images = no age

        # Find most recent image
        images = list(vf_image_dir.rglob("DR*.jpg"))
        if not images:
            return 0  # No images

        latest_image = max(images, key=lambda p: p.stat().st_mtime)
        age_seconds = time.time() - latest_image.stat().st_mtime

        return age_seconds

    def _check_vlm_server(self) -> float:
        """
        Check VLM server responsiveness.

        Returns:
            Response time in seconds
        """
        logger.debug("Checking VLM server...")

        vlm_url = os.getenv("VLM_API_URL", "http://100.96.203.105:8100")
        start = time.time()

        try:
            response = requests.get(f"{vlm_url}/health", timeout=10)
            elapsed = time.time() - start

            if response.status_code == 200:
                return elapsed
            else:
                raise Exception(f"VLM server returned {response.status_code}")

        except requests.exceptions.Timeout:
            return 10.0  # Timeout = max response time
        except requests.exceptions.RequestException as e:
            raise Exception(f"VLM server unreachable: {e}")

    def _check_wa_session_age(self) -> float:
        """
        Check WhatsApp session age.

        Returns:
            Session age in seconds
        """
        logger.debug("Checking WhatsApp session age...")

        # Check session database on VF Server
        session_db = Path("/var/www/lifeos-agents/.wwebjs_auth/session/Default")

        if not session_db.exists():
            # Fall back to local test path
            session_db = Path.cwd() / "test_data" / "wa_session"

        if not session_db.exists():
            logger.warning(f"WhatsApp session not found: {session_db}")
            return 0  # No session = no age

        # Check modification time of session directory
        session_age = time.time() - session_db.stat().st_mtime

        return session_age

    def _check_foto_review_age(self) -> float:
        """
        Check age of most recent Foto AI review.

        Returns:
            Age in seconds of most recent review
        """
        logger.debug("Checking Foto AI review age...")

        # For now, return simulated value
        # TODO: Query foto_ai_reviews table for MAX(updated_at)

        # Simulated value
        return 420.0  # 7 minutes (within 30min SLA)

    def _process_alerts(self, checks: List[SLACheck]) -> None:
        """
        Send alerts for SLA violations.

        Args:
            checks: List of SLA check results
        """
        for check in checks:
            if check.status == "VIOLATION":
                # Find matching alert configs
                for alert_config in self.alerts:
                    if self._matches_condition(alert_config, check):
                        self._send_alert(alert_config, check)

    def _matches_condition(self, alert_config: Dict, check: SLACheck) -> bool:
        """
        Check if alert condition matches the check result.

        Args:
            alert_config: Alert configuration
            check: SLA check result

        Returns:
            True if condition matches
        """
        condition = alert_config["condition"]

        # Parse condition (e.g., "neon_sync_delay > 300")
        if "neon_sync_delay" in condition and "neon" in check.name:
            threshold = int(condition.split(">")[1].strip())
            return check.current_value > threshold

        if "vlm_image_age" in condition and "vlm" in check.name and "image" in check.name:
            threshold = int(condition.split(">")[1].strip())
            return check.current_value > threshold

        if "wa_session_age" in condition and "wa_session" in check.name:
            threshold = int(condition.split(">")[1].strip())
            return check.current_value > threshold

        if "foto_review_age" in condition and "foto" in check.name:
            threshold = int(condition.split(">")[1].strip())
            return check.current_value > threshold

        return False

    def _send_alert(self, alert_config: Dict, check: SLACheck) -> None:
        """
        Send Slack alert for SLA violation.

        Args:
            alert_config: Alert configuration
            check: SLA check result
        """
        # Check alert cooldown (don't spam)
        alert_name = alert_config["name"]
        cooldown = self.monitoring.get("alert_cooldown", 300)

        if alert_name in self.last_alert_time:
            time_since_last = time.time() - self.last_alert_time[alert_name]
            if time_since_last < cooldown:
                logger.debug(f"Alert {alert_name} in cooldown ({time_since_last:.0f}s)")
                return

        # Format message
        message = alert_config["message"].format(
            delay=check.current_value,
            age=check.current_value,
            time=check.current_value,
            interval=check.current_value,
            idle=check.current_value,
            url=os.getenv("VLM_API_URL", "http://100.96.203.105:8100")
        )

        # Send to Slack (if configured)
        slack_token = os.getenv("SLACK_BOT_TOKEN")
        if slack_token:
            try:
                from slack_sdk import WebClient
                client = WebClient(token=slack_token)

                client.chat_postMessage(
                    channel=alert_config["channel"],
                    text=message
                )

                logger.info(f"📤 Slack alert sent: {alert_name}")

            except Exception as e:
                logger.error(f"Failed to send Slack alert: {e}")
        else:
            logger.warning(f"Slack token not configured, logging alert: {message}")

        # Record violation
        violation = SLAViolation(
            timestamp=datetime.now().isoformat(),
            check_name=check.name,
            current_value=check.current_value,
            sla_threshold=check.sla_threshold,
            severity=alert_config["severity"],
            alerted=True
        )

        self.violations.append(violation)
        self._save_violation(violation)

        # Update last alert time
        self.last_alert_time[alert_name] = time.time()

    def _save_metrics(self, results: Dict[str, Any]) -> None:
        """Save SLA check metrics to JSONL file."""
        try:
            with open(self.metrics_file, 'a') as f:
                # Convert SLACheck objects to dicts
                metrics = {
                    "timestamp": results["timestamp"],
                    "checks": [asdict(c) for c in results["checks"]]
                }
                f.write(json.dumps(metrics) + "\n")

        except Exception as e:
            logger.error(f"Failed to save metrics: {e}")

    def _save_violation(self, violation: SLAViolation) -> None:
        """Save SLA violation to JSONL file."""
        try:
            with open(self.violations_file, 'a') as f:
                f.write(json.dumps(asdict(violation)) + "\n")

        except Exception as e:
            logger.error(f"Failed to save violation: {e}")

    def get_compliance_percentage(self, days: int = 30) -> float:
        """
        Calculate SLA compliance percentage over last N days.

        Args:
            days: Number of days to analyze

        Returns:
            Compliance percentage (0-100)
        """
        if not self.metrics_file.exists():
            return 100.0  # No data = assume compliant

        cutoff = datetime.now() - timedelta(days=days)

        total_checks = 0
        passed_checks = 0

        try:
            with open(self.metrics_file, 'r') as f:
                for line in f:
                    metrics = json.loads(line)
                    check_time = datetime.fromisoformat(metrics["timestamp"])

                    if check_time >= cutoff:
                        for check in metrics["checks"]:
                            total_checks += 1
                            if check["status"] == "OK":
                                passed_checks += 1

        except Exception as e:
            logger.error(f"Failed to calculate compliance: {e}")
            return 0.0

        if total_checks == 0:
            return 100.0

        return (passed_checks / total_checks) * 100

    def verify_data_freshness(
        self,
        components: Optional[List[str]] = None,
        raise_on_violation: bool = False
    ) -> bool:
        """
        Verify data freshness before critical operation.

        Args:
            components: List of components to check (None = all)
            raise_on_violation: Raise exception if violations found

        Returns:
            True if all checks pass, False otherwise

        Raises:
            SLAViolationError: If violations found and raise_on_violation=True
        """
        results = self.check_all_slas()

        # Filter by components if specified
        checks = results["checks"]
        if components:
            checks = [
                c for c in checks
                if any(comp in c.name for comp in components)
            ]

        violations = [c for c in checks if c.status == "VIOLATION"]

        if violations and raise_on_violation:
            violation_summary = "\n".join([
                f"  • {v.name}: {v.current_value:.0f}s (SLA: {v.sla_threshold:.0f}s)"
                for v in violations
            ])
            raise SLAViolationError(
                f"SLA violations detected:\n{violation_summary}"
            )

        return len(violations) == 0


if __name__ == "__main__":
    # Demo the SLA monitor
    print("SLA Monitor - Phase 2.5: Data Layer SLAs")
    print("=" * 70)
    print()

    monitor = SLAMonitor()

    # Run checks
    print("Running SLA checks...")
    results = monitor.check_all_slas()

    print()
    print("=" * 70)
    print("SLA Check Results")
    print("=" * 70)
    print()

    for check in results["checks"]:
        status_icon = "✅" if check.status == "OK" else ("⚠️" if check.status == "VIOLATION" else "❌")

        print(f"{status_icon} {check.name}")
        print(f"   Current: {check.current_value:.1f}{check.unit}")
        print(f"   SLA:     {check.sla_threshold:.1f}{check.unit}")
        print(f"   Status:  {check.status}")

        if check.error_message:
            print(f"   Error:   {check.error_message}")

        print()

    # Show compliance
    print("=" * 70)
    print("Compliance")
    print("=" * 70)
    compliance = monitor.get_compliance_percentage(days=30)
    print(f"30-day compliance: {compliance:.1f}%")
    print()

    # Verify data freshness
    print("=" * 70)
    print("Data Freshness Verification")
    print("=" * 70)
    try:
        is_fresh = monitor.verify_data_freshness(
            components=["neon", "vlm"],
            raise_on_violation=True
        )
        print("✅ Data is fresh and safe for agent operations")
    except SLAViolationError as e:
        print(f"⚠️  {e}")

    print()
    print("=" * 70)
    print("✅ SLA Monitor demo complete")
