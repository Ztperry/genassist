"""
Tool wrappers for the Email Agent.

Creates BaseTool instances that wrap GmailConnector methods.
Each factory function captures the current email context and GmailConnector
instance via closure, so the agent only needs to provide action-specific parameters.
"""

import json
import logging
from typing import Dict, Any, List

from app.modules.workflow.agents.base_tool import BaseTool
from app.modules.integration.gmail_connector import GmailConnector

logger = logging.getLogger(__name__)


def create_reply_tool(gmail_connector: GmailConnector, email_context: Dict[str, Any]) -> BaseTool:
    """Create a tool for replying to the current email."""

    async def reply_function(params: dict) -> str:
        parameters = params.get("parameters", params)
        reply_body = parameters.get("reply_body", "")
        if not reply_body:
            return json.dumps({"success": False, "error": "reply_body is required"})
        try:
            result = await gmail_connector.reply_to_email(email_context, reply_body)
            return json.dumps(result)
        except Exception as e:
            logger.error(f"Error replying to email: {e}")
            return json.dumps({"success": False, "error": str(e)})

    return BaseTool(
        node_id="email_agent_reply",
        name="reply_to_email",
        description="Send a reply to the current email. Use this when the email requires a response.",
        parameters={
            "reply_body": {
                "type": "string",
                "required": True,
                "description": "The body text of the reply email. Be professional and concise.",
            }
        },
        function=reply_function,
    )


def create_mark_as_read_tool(gmail_connector: GmailConnector, email_context: Dict[str, Any]) -> BaseTool:
    """Create a tool for marking the current email as read."""

    async def mark_as_read_function(params: dict) -> str:
        email_id = email_context.get("id", "")
        if not email_id:
            return json.dumps({"success": False, "error": "No email ID available"})
        try:
            success = await gmail_connector.mark_as_read(email_id)
            return json.dumps({"success": success, "action": "marked_as_read", "email_id": email_id})
        except Exception as e:
            logger.error(f"Error marking email as read: {e}")
            return json.dumps({"success": False, "error": str(e)})

    return BaseTool(
        node_id="email_agent_mark_read",
        name="mark_as_read",
        description="Mark the current email as read. Use this for informational emails that need no action.",
        parameters={},
        function=mark_as_read_function,
    )


def create_forward_tool(gmail_connector: GmailConnector, email_context: Dict[str, Any]) -> BaseTool:
    """Create a tool for forwarding the current email."""

    async def forward_function(params: dict) -> str:
        parameters = params.get("parameters", params)
        to = parameters.get("to", "")
        note = parameters.get("note", "")
        if not to:
            return json.dumps({"success": False, "error": "Recipient email address (to) is required"})

        original_from = email_context.get("from", "Unknown")
        original_subject = email_context.get("subject", "(no subject)")
        original_body = email_context.get("body", "")
        original_date = email_context.get("date", "")

        forward_subject = f"Fwd: {original_subject}"
        forward_body = ""
        if note:
            forward_body += f"{note}\n\n"
        forward_body += (
            f"---------- Forwarded message ----------\n"
            f"From: {original_from}\n"
            f"Date: {original_date}\n"
            f"Subject: {original_subject}\n\n"
            f"{original_body}"
        )

        try:
            result = await gmail_connector.send_email(
                to=to,
                subject=forward_subject,
                body=forward_body,
            )
            return json.dumps(result)
        except Exception as e:
            logger.error(f"Error forwarding email: {e}")
            return json.dumps({"success": False, "error": str(e)})

    return BaseTool(
        node_id="email_agent_forward",
        name="forward_email",
        description="Forward the current email to another recipient. Use this to delegate or escalate.",
        parameters={
            "to": {
                "type": "string",
                "required": True,
                "description": "The email address to forward this email to.",
            },
            "note": {
                "type": "string",
                "required": False,
                "description": "An optional note to include above the forwarded message.",
            },
        },
        function=forward_function,
    )


def create_flag_for_review_tool(email_context: Dict[str, Any]) -> BaseTool:
    """Create a tool for flagging the current email for human review."""

    async def flag_function(params: dict) -> str:
        parameters = params.get("parameters", params)
        reason = parameters.get("reason", "No reason provided")
        result = {
            "success": True,
            "action": "flagged_for_review",
            "email_id": email_context.get("id", ""),
            "subject": email_context.get("subject", ""),
            "from": email_context.get("from", ""),
            "reason": reason,
        }
        logger.info(f"Email flagged for review: {email_context.get('subject', '')} - Reason: {reason}")
        return json.dumps(result)

    return BaseTool(
        node_id="email_agent_flag",
        name="flag_for_review",
        description="Flag the current email for human review. Use this for sensitive, important, or unclear emails.",
        parameters={
            "reason": {
                "type": "string",
                "required": True,
                "description": "The reason why this email needs human review.",
            }
        },
        function=flag_function,
    )


def create_categorize_tool(email_context: Dict[str, Any]) -> BaseTool:
    """Create a tool for categorizing the current email."""

    async def categorize_function(params: dict) -> str:
        parameters = params.get("parameters", params)
        category = parameters.get("category", "uncategorized")
        result = {
            "success": True,
            "action": "categorized",
            "email_id": email_context.get("id", ""),
            "subject": email_context.get("subject", ""),
            "category": category,
        }
        logger.info(f"Email categorized: {email_context.get('subject', '')} -> {category}")
        return json.dumps(result)

    return BaseTool(
        node_id="email_agent_categorize",
        name="categorize",
        description="Categorize the current email with a label. Use this for organizational purposes.",
        parameters={
            "category": {
                "type": "string",
                "required": True,
                "description": "The category or label to assign (e.g., 'work', 'personal', 'urgent', 'support', 'sales').",
            }
        },
        function=categorize_function,
    )


def create_ignore_tool(email_context: Dict[str, Any]) -> BaseTool:
    """Create a tool for ignoring the current email."""

    async def ignore_function(params: dict) -> str:
        result = {
            "success": True,
            "action": "ignored",
            "email_id": email_context.get("id", ""),
            "subject": email_context.get("subject", ""),
        }
        logger.info(f"Email ignored: {email_context.get('subject', '')}")
        return json.dumps(result)

    return BaseTool(
        node_id="email_agent_ignore",
        name="ignore",
        description="Ignore the current email. Use this for spam, irrelevant, or no-action-needed emails.",
        parameters={},
        function=ignore_function,
    )


def build_tools_for_email(
    gmail_connector: GmailConnector,
    email_context: Dict[str, Any],
    allowed_actions: List[str] | None = None,
) -> List[BaseTool]:
    """Build the complete set of tools for processing a single email.

    Args:
        gmail_connector: Initialized GmailConnector instance.
        email_context: The email dict being processed (captured in closures).
        allowed_actions: Optional list of allowed action names to filter tools.

    Returns:
        List of BaseTool instances the agent can use.
    """
    all_tools = {
        "reply_to_email": lambda: create_reply_tool(gmail_connector, email_context),
        "mark_as_read": lambda: create_mark_as_read_tool(gmail_connector, email_context),
        "forward_email": lambda: create_forward_tool(gmail_connector, email_context),
        "flag_for_review": lambda: create_flag_for_review_tool(email_context),
        "categorize": lambda: create_categorize_tool(email_context),
        "ignore": lambda: create_ignore_tool(email_context),
    }

    if allowed_actions is None:
        allowed_actions = list(all_tools.keys())

    tools = []
    for action_name in allowed_actions:
        factory = all_tools.get(action_name)
        if factory:
            tools.append(factory())
        else:
            logger.warning(f"Unknown action in allowed_actions: {action_name}")

    return tools
