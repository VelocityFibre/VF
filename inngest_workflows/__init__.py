"""
Inngest workflow orchestration for FibreFlow Agent Workforce

This package provides durable, event-driven workflows for:
- Agent building and deployment
- Database synchronization
- WhatsApp message queueing
- VLM evaluation pipelines
"""

from .client import inngest_client, Events, InngestConfig, get_inngest_client

__all__ = [
    "inngest_client",
    "Events",
    "InngestConfig",
    "get_inngest_client",
]