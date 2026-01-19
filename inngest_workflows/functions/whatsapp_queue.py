"""
WhatsApp message queue with rate limiting using Inngest

This module provides a durable queue for WhatsApp messages with:
- Rate limiting (10 messages per minute)
- Automatic retries with exponential backoff
- Phone pairing validation
- Error handling and dead letter queue
"""

import os
import sys
import json
import time
import requests
from typing import Dict, Any, Optional
from datetime import datetime

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from inngest import Inngest, Function, TriggerEvent
from client import inngest_client, Events, InngestConfig

# WhatsApp service configuration
WHATSAPP_SERVICE_URL = os.getenv("WHATSAPP_SERVICE_URL", "http://100.96.203.105:8081")
WHATSAPP_PHONE = os.getenv("WHATSAPP_PHONE", "+27 71 155 8396")

@inngest_client.create_function(
    fn_id="send-whatsapp-message",
    trigger=TriggerEvent(event=Events.WHATSAPP_MESSAGE_QUEUED),
    throttle={
        "limit": InngestConfig.WHATSAPP_RATE_LIMIT,
        "period": 60000,  # 60 seconds in milliseconds
        "key": "event.data.phone"  # Rate limit per recipient
    },
    retries=5
)
async def send_whatsapp_message(ctx, step):
    """
    Send a WhatsApp message with rate limiting and retries.

    This function ensures messages are sent reliably without
    overwhelming the WhatsApp service or getting the phone banned.

    Args:
        ctx: Inngest context with event data
        step: Inngest step runner

    Event data should contain:
        - phone: Recipient phone number
        - message: Message text
        - priority: Optional priority level (high/normal/low)
        - group_id: Optional group ID for group messages
    """

    # Extract message data
    phone = ctx.event.data.get("phone")
    message = ctx.event.data.get("message")
    priority = ctx.event.data.get("priority", "normal")
    group_id = ctx.event.data.get("group_id")

    if not phone or not message:
        raise ValueError("Phone and message are required")

    # Step 1: Check WhatsApp service status
    service_status = await step.run(
        "check-service",
        lambda: _check_whatsapp_service(),
        retry={"attempts": 3, "delay": "10s"}
    )

    if not service_status.get("running"):
        # Service not running - wait and retry
        await step.sleep("wait-for-service", "2m")
        raise Exception(f"WhatsApp service not running: {service_status.get('error')}")

    if not service_status.get("paired"):
        # Phone not paired - this is critical
        await step.run(
            "log-pairing-error",
            lambda: _log_error(
                f"Phone {WHATSAPP_PHONE} is not paired. "
                "Please pair via WhatsApp Linked Devices."
            )
        )
        # Don't retry immediately for pairing issues
        await step.sleep("wait-for-pairing", "30m")
        raise Exception("Phone not paired with WhatsApp")

    # Step 2: Format message
    formatted_message = await step.run(
        "format-message",
        lambda: _format_message(message, priority)
    )

    # Step 3: Send message
    result = await step.run(
        "send-message",
        lambda: _send_via_whatsapp(
            phone=phone,
            message=formatted_message,
            group_id=group_id
        ),
        retry={
            "attempts": 3,
            "delay": "exponential",
            "initial_interval": "30s",
            "max_interval": "5m"
        }
    )

    # Step 4: Log success
    await step.run(
        "log-success",
        lambda: _log_message_sent(phone, message, result)
    )

    # Step 5: Send confirmation event (optional)
    if ctx.event.data.get("request_confirmation"):
        await step.send_event(
            "send-confirmation",
            {
                "name": Events.WHATSAPP_MESSAGE_SENT,
                "data": {
                    "phone": phone,
                    "message_id": result.get("message_id"),
                    "timestamp": datetime.utcnow().isoformat()
                }
            }
        )

    return result

@inngest_client.create_function(
    fn_id="batch-whatsapp-messages",
    trigger=TriggerEvent(event="whatsapp/batch.requested"),
    concurrency=[{"limit": 1, "scope": "fn"}]
)
async def send_batch_messages(ctx, step):
    """
    Send multiple WhatsApp messages with proper spacing.

    This function handles batch message sending, ensuring proper
    rate limiting across multiple recipients.
    """

    messages = ctx.event.data.get("messages", [])

    if not messages:
        return {"status": "no_messages"}

    results = []

    for i, msg_data in enumerate(messages):
        # Send each message as a separate queued event
        result = await step.send_event(
            f"queue-message-{i}",
            {
                "name": Events.WHATSAPP_MESSAGE_QUEUED,
                "data": msg_data
            }
        )
        results.append(result)

        # Add delay between queueing messages
        if i < len(messages) - 1:
            await step.sleep(f"batch-delay-{i}", "6s")  # 10 per minute = 6s spacing

    return {
        "status": "queued",
        "messages_queued": len(results),
        "timestamp": datetime.utcnow().isoformat()
    }

@inngest_client.create_function(
    fn_id="whatsapp-feedback-handler",
    trigger=TriggerEvent(event="foto/feedback.requested"),
    retries=3
)
async def handle_foto_feedback(ctx, step):
    """
    Handle foto review feedback via WhatsApp.

    This integrates with the wa-monitor module to send
    evaluation results to contractors.
    """

    dr_number = ctx.event.data.get("dr_number")
    evaluation = ctx.event.data.get("evaluation")
    contractor_phone = ctx.event.data.get("contractor_phone")

    if not all([dr_number, evaluation, contractor_phone]):
        raise ValueError("Missing required feedback data")

    # Format feedback message
    feedback = await step.run(
        "format-feedback",
        lambda: _format_foto_feedback(dr_number, evaluation)
    )

    # Queue the message
    await step.send_event(
        "queue-feedback",
        {
            "name": Events.WHATSAPP_MESSAGE_QUEUED,
            "data": {
                "phone": contractor_phone,
                "message": feedback["message"],
                "priority": "high" if feedback.get("score", 100) < 70 else "normal",
                "request_confirmation": True
            }
        }
    )

    return {"status": "feedback_queued", "dr_number": dr_number}

# Helper functions
def _check_whatsapp_service() -> Dict[str, Any]:
    """Check if WhatsApp service is running and phone is paired."""
    try:
        response = requests.get(
            f"{WHATSAPP_SERVICE_URL}/api/status",
            timeout=5
        )

        if response.status_code == 200:
            data = response.json()
            return {
                "running": True,
                "paired": data.get("paired", False),
                "phone": data.get("phone", WHATSAPP_PHONE)
            }
        else:
            return {
                "running": True,
                "paired": False,
                "error": f"Status check returned {response.status_code}"
            }
    except requests.RequestException as e:
        return {
            "running": False,
            "paired": False,
            "error": str(e)
        }

def _format_message(message: str, priority: str) -> str:
    """Format message with priority indicators."""
    if priority == "high":
        return f"🔴 URGENT: {message}"
    elif priority == "low":
        return f"ℹ️ {message}"
    else:
        return message

def _send_via_whatsapp(phone: str, message: str, group_id: Optional[str] = None) -> Dict[str, Any]:
    """Send message via WhatsApp service."""
    try:
        endpoint = "/api/send-group" if group_id else "/api/send"

        payload = {
            "phone": phone,
            "message": message
        }

        if group_id:
            payload["group_id"] = group_id

        response = requests.post(
            f"{WHATSAPP_SERVICE_URL}{endpoint}",
            json=payload,
            timeout=30
        )

        if response.status_code == 200:
            return {
                "status": "sent",
                "message_id": response.json().get("message_id"),
                "timestamp": datetime.utcnow().isoformat()
            }
        else:
            raise Exception(f"WhatsApp API error: {response.status_code} - {response.text}")

    except Exception as e:
        raise Exception(f"Failed to send WhatsApp message: {str(e)}")

def _format_foto_feedback(dr_number: str, evaluation: Dict[str, Any]) -> Dict[str, Any]:
    """Format foto evaluation feedback for WhatsApp."""
    score = evaluation.get("score", "N/A")
    issues = evaluation.get("issues", [])
    recommendations = evaluation.get("recommendations", [])

    message = f"""
📸 Foto Review Feedback
DR Number: {dr_number}
Score: {score}/100

Issues Found:
{chr(10).join(f'• {issue}' for issue in issues[:3]) if issues else '✅ No major issues'}

Recommendations:
{chr(10).join(f'• {rec}' for rec in recommendations[:3]) if recommendations else 'None'}

View full details: https://app.fibreflow.app/wa-monitor
"""
    return {"message": message.strip(), "score": score}

def _log_message_sent(phone: str, message: str, result: Dict[str, Any]):
    """Log successful message send."""
    log_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "phone": phone,
        "message_preview": message[:100],
        "result": result,
        "service": "whatsapp"
    }
    print(f"[WhatsApp Sent] {json.dumps(log_entry)}")
    return log_entry

def _log_error(error_message: str):
    """Log WhatsApp errors."""
    error_log = {
        "timestamp": datetime.utcnow().isoformat(),
        "error": error_message,
        "service": "whatsapp",
        "severity": "error"
    }
    print(f"[WhatsApp Error] {json.dumps(error_log)}")
    return error_log

# Export functions for registration
whatsapp_queue_functions = [
    send_whatsapp_message,
    send_batch_messages,
    handle_foto_feedback
]