"""
Core Email Agent orchestration.

Fetches unread emails from a Gmail data source, runs a ReAct agent
to analyze each email and decide on an action, and tracks processed
email IDs in Redis to avoid duplicates.
"""

import json
import logging
from datetime import datetime
from typing import Dict, Any, List
from uuid import UUID

from app.modules.email_agent.email_agent_config import EmailAgentConfig
from app.modules.email_agent.email_agent_prompts import (
    build_system_prompt,
    format_email_as_query,
)
from app.modules.email_agent.email_agent_tools import build_tools_for_email
from app.modules.integration.gmail_connector import GmailConnector
from app.modules.workflow.agents.react_agent import ReActAgent
from app.modules.workflow.llm.provider import LLMProvider

logger = logging.getLogger(__name__)

# Redis key pattern and TTL for processed email deduplication
REDIS_PROCESSED_KEY = "email_agent:processed:{ds_id}"
REDIS_HISTORY_KEY = "email_agent:history:{ds_id}"
REDIS_PROCESSED_TTL = 60 * 60 * 24 * 7  # 7 days
REDIS_HISTORY_TTL = 60 * 60 * 24 * 3  # 3 days
MAX_HISTORY_ENTRIES = 100


async def _get_redis():
    """Get the Redis string client from the dependency injector."""
    from app.dependencies.injector import injector
    from app.dependencies.dependency_injection import RedisString

    return injector.get(RedisString)


async def _get_processed_ids(redis, ds_id: UUID) -> set:
    """Get the set of already-processed email IDs from Redis."""
    key = REDIS_PROCESSED_KEY.format(ds_id=str(ds_id))
    members = await redis.smembers(key)
    return {m.decode("utf-8") if isinstance(m, bytes) else m for m in members}


async def _mark_as_processed(redis, ds_id: UUID, email_id: str):
    """Mark an email ID as processed in Redis."""
    key = REDIS_PROCESSED_KEY.format(ds_id=str(ds_id))
    await redis.sadd(key, email_id)
    await redis.expire(key, REDIS_PROCESSED_TTL)


async def _save_history_entry(redis, ds_id: UUID, entry: dict):
    """Save a processing history entry to Redis."""
    key = REDIS_HISTORY_KEY.format(ds_id=str(ds_id))
    await redis.lpush(key, json.dumps(entry, default=str))
    await redis.ltrim(key, 0, MAX_HISTORY_ENTRIES - 1)
    await redis.expire(key, REDIS_HISTORY_TTL)


async def get_processing_history(ds_id: UUID) -> List[dict]:
    """Retrieve recent processing history for a data source."""
    redis = await _get_redis()
    key = REDIS_HISTORY_KEY.format(ds_id=str(ds_id))
    entries = await redis.lrange(key, 0, MAX_HISTORY_ENTRIES - 1)
    return [json.loads(e.decode("utf-8") if isinstance(e, bytes) else e) for e in entries]


async def process_emails_for_datasource(ds_id: UUID, config: EmailAgentConfig) -> Dict[str, Any]:
    """Process unread emails for a Gmail data source using an AI agent.

    Args:
        ds_id: The UUID of the Gmail DataSource record.
        config: The EmailAgentConfig for this data source.

    Returns:
        Summary dict with processed count, actions taken, and errors.
    """
    actions_taken: List[Dict[str, Any]] = []
    errors: List[Dict[str, Any]] = []

    try:
        # 1. Initialize Gmail connector
        gmail_connector = GmailConnector(ds_id)

        # 2. Fetch unread emails
        search_criteria = {
            "is_unread": True,
            "max_results": config.max_emails_per_poll,
        }
        emails = await gmail_connector.search_emails(search_criteria)

        if not emails:
            logger.info(f"No unread emails found for data source {ds_id}")
            return {"processed": 0, "actions": [], "errors": []}

        logger.info(f"Found {len(emails)} unread emails for data source {ds_id}")

        # 3. Filter out already-processed emails
        redis = await _get_redis()
        processed_ids = await _get_processed_ids(redis, ds_id)
        new_emails = [e for e in emails if e.get("id") not in processed_ids]

        if not new_emails:
            logger.info(f"All {len(emails)} emails already processed for data source {ds_id}")
            return {"processed": 0, "actions": [], "errors": []}

        logger.info(f"Processing {len(new_emails)} new emails (skipped {len(emails) - len(new_emails)} already processed)")

        # 4. Initialize LLM provider
        llm_provider = LLMProvider()
        llm_model = await llm_provider.get_model(config.llm_provider_id)

        # 5. Build system prompt
        system_prompt = build_system_prompt(
            custom_rules=config.rules,
            mode=config.mode,
            base_prompt=config.system_prompt,
        )

        # 6. Process each email
        for email in new_emails:
            email_id = email.get("id", "")
            email_subject = email.get("subject", "(no subject)")
            email_from = email.get("from", "Unknown")

            try:
                result = await _process_single_email(
                    gmail_connector=gmail_connector,
                    llm_model=llm_model,
                    system_prompt=system_prompt,
                    email=email,
                    config=config,
                )

                action_record = {
                    "email_id": email_id,
                    "from": email_from,
                    "subject": email_subject,
                    "action_taken": result.get("action", "unknown"),
                    "agent_reasoning": result.get("reasoning", ""),
                    "timestamp": datetime.utcnow().isoformat(),
                    "mode": config.mode,
                    "status": result.get("status", "unknown"),
                }
                actions_taken.append(action_record)

                # Save to history
                await _save_history_entry(redis, ds_id, action_record)

                # Mark as processed
                await _mark_as_processed(redis, ds_id, email_id)

                # Auto mark as read in autonomous mode
                if config.auto_mark_as_read and config.mode == "autonomous":
                    await gmail_connector.mark_as_read(email_id)

                logger.info(
                    f"Processed email '{email_subject}' from {email_from} -> action: {result.get('action', 'unknown')}"
                )

            except Exception as e:
                error_record = {
                    "email_id": email_id,
                    "from": email_from,
                    "subject": email_subject,
                    "error": str(e),
                    "timestamp": datetime.utcnow().isoformat(),
                }
                errors.append(error_record)
                logger.error(f"Error processing email '{email_subject}': {e}")

                # Still mark as processed to avoid retrying broken emails
                await _mark_as_processed(redis, ds_id, email_id)

    except Exception as e:
        logger.error(f"Error in email agent for data source {ds_id}: {e}")
        errors.append({"error": str(e), "timestamp": datetime.utcnow().isoformat()})

    return {
        "processed": len(actions_taken),
        "actions": actions_taken,
        "errors": errors,
    }


async def _process_single_email(
    gmail_connector: GmailConnector,
    llm_model,
    system_prompt: str,
    email: Dict[str, Any],
    config: EmailAgentConfig,
) -> Dict[str, Any]:
    """Process a single email using the ReAct agent.

    Args:
        gmail_connector: Initialized GmailConnector.
        llm_model: LangChain BaseChatModel instance.
        system_prompt: The assembled system prompt.
        email: The email dict to process.
        config: The email agent configuration.

    Returns:
        Dict with action taken, reasoning, and status.
    """
    # Build tools (only in autonomous mode)
    if config.mode == "autonomous":
        tools = build_tools_for_email(
            gmail_connector=gmail_connector,
            email_context=email,
            allowed_actions=config.allowed_actions,
        )
    else:
        # Recommend-only mode: no tools, agent just provides analysis
        tools = []

    # Create the ReAct agent
    agent = ReActAgent(
        llm_model=llm_model,
        system_prompt=system_prompt,
        tools=tools,
        verbose=True,
        max_iterations=5,
    )

    # Format the email as a query for the agent
    query = format_email_as_query(email)

    # Invoke the agent
    result = await agent.invoke(query)

    # Extract the action from the agent's result
    action = _extract_action_from_result(result, config.mode)

    return action


def _extract_action_from_result(agent_result: Dict[str, Any], mode: str) -> Dict[str, Any]:
    """Extract a structured action from the agent's result.

    Args:
        agent_result: The raw result dict from ReActAgent.invoke().
        mode: "autonomous" or "recommend_only".

    Returns:
        Dict with action, reasoning, and status.
    """
    status = agent_result.get("status", "error")
    response_text = agent_result.get("response", "")
    tools_used = agent_result.get("tools_used", [])

    # Determine the action taken
    if mode == "recommend_only":
        return {
            "action": "recommendation",
            "reasoning": response_text,
            "status": status,
        }

    # In autonomous mode, determine action from tools used
    if tools_used:
        last_tool = tools_used[-1]
        action_name = last_tool.get("tool_name", "unknown")
        return {
            "action": action_name,
            "reasoning": response_text,
            "tool_result": last_tool.get("result", ""),
            "status": status,
        }

    # No tools used — agent gave a direct answer
    return {
        "action": "no_action",
        "reasoning": response_text,
        "status": status,
    }
