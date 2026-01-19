"""
Inngest client configuration for FibreFlow Agent Workforce

This module initializes the Inngest client and provides the core
configuration for all workflow functions.
"""

import os
from typing import Optional
from inngest import Inngest
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Inngest client
inngest_client = Inngest(
    app_id=os.getenv("INNGEST_APP_ID", "fibreflow-agents"),
    signing_key=os.getenv("INNGEST_SIGNING_KEY"),
    event_key=os.getenv("INNGEST_EVENT_KEY"),
    is_production=os.getenv("INNGEST_ENV", "development") == "production",
)

def get_inngest_client() -> Inngest:
    """
    Get the configured Inngest client instance.

    Returns:
        Inngest: The configured Inngest client
    """
    return inngest_client

# Event definitions for type safety
class Events:
    """Event definitions for Inngest workflows"""

    # Agent building events
    AGENT_BUILD_REQUESTED = "agent/build.requested"
    AGENT_BUILD_STARTED = "agent/build.started"
    AGENT_FEATURE_COMPLETED = "agent/feature.completed"
    AGENT_BUILD_COMPLETED = "agent/build.completed"
    AGENT_BUILD_FAILED = "agent/build.failed"

    # Database sync events
    DB_SYNC_SCHEDULED = "database/sync.scheduled"
    DB_SYNC_STARTED = "database/sync.started"
    DB_SYNC_COMPLETED = "database/sync.completed"
    DB_SYNC_FAILED = "database/sync.failed"

    # WhatsApp events
    WHATSAPP_MESSAGE_QUEUED = "whatsapp/message.queued"
    WHATSAPP_MESSAGE_SENT = "whatsapp/message.sent"
    WHATSAPP_MESSAGE_FAILED = "whatsapp/message.failed"

    # VLM evaluation events
    VLM_EVALUATION_REQUESTED = "vlm/evaluation.requested"
    VLM_EVALUATION_STARTED = "vlm/evaluation.started"
    VLM_EVALUATION_COMPLETED = "vlm/evaluation.completed"
    VLM_EVALUATION_FAILED = "vlm/evaluation.failed"

    # Deployment events
    DEPLOYMENT_REQUESTED = "deployment/requested"
    DEPLOYMENT_STARTED = "deployment/started"
    DEPLOYMENT_COMPLETED = "deployment/completed"
    DEPLOYMENT_FAILED = "deployment/failed"

    # Orchestrator events
    TASK_REQUESTED = "orchestrator/task.requested"
    TASK_ROUTED = "orchestrator/task.routed"
    TASK_COMPLETED = "orchestrator/task.completed"

# Configuration for different environments
class InngestConfig:
    """Configuration settings for Inngest"""

    # Dev server settings
    DEV_SERVER_URL = "http://localhost:8288"
    DEV_API_URL = "http://localhost:3000/api/inngest"

    # Production settings (when using cloud)
    PROD_API_URL = "https://api.inngest.com"

    # Rate limits and timeouts
    DEFAULT_TIMEOUT = "5m"
    DEFAULT_RETRIES = 3
    DEFAULT_RETRY_DELAY = "30s"

    # Concurrency limits
    AGENT_BUILD_CONCURRENCY = 1  # One agent build at a time
    WHATSAPP_RATE_LIMIT = 10  # Messages per minute
    VLM_CONCURRENCY = 5  # Max concurrent evaluations
    DB_SYNC_CONCURRENCY = 1  # Single sync at a time

def validate_config() -> bool:
    """
    Validate that required Inngest configuration is present.

    Returns:
        bool: True if configuration is valid
    """
    required_vars = []  # Start without requiring keys for development

    if os.getenv("INNGEST_ENV") == "production":
        required_vars = ["INNGEST_SIGNING_KEY", "INNGEST_EVENT_KEY"]

    missing = [var for var in required_vars if not os.getenv(var)]

    if missing:
        print(f"⚠️  Missing required environment variables: {', '.join(missing)}")
        print("   Add them to your .env file for production use.")
        return False

    return True

# Validate on import
if not validate_config():
    print("ℹ️  Running in development mode. Some features may be limited.")