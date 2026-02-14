"""
Celery periodic task for the Email Agent.

Polls Gmail for unread emails and processes them using an AI agent.
Follows the same pattern as zendesk_tasks.py.
"""

import asyncio
import logging
from uuid import UUID

from celery import shared_task

from app.core.utils.date_time_utils import utc_now
from app.dependencies.injector import injector
from app.services.datasources import DataSourceService
from app.modules.email_agent.email_agent import process_emails_for_datasource
from app.modules.email_agent.email_agent_config import EmailAgentConfig

logger = logging.getLogger(__name__)


@shared_task
def process_email_agent_task():
    """Celery entry point: run the email agent for all tenants."""
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    if loop.is_closed():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    return loop.run_until_complete(process_email_agent_async_with_scope())


async def process_email_agent_async_with_scope():
    """Wrapper to run email agent processing for all tenants."""
    from app.tasks.base import run_task_with_tenant_support

    result = await run_task_with_tenant_support(
        process_all_email_agents, "Email agent processing"
    )
    if result.get("status") == "success":
        result["status"] = "completed"
    return result


async def process_all_email_agents():
    """Find all Gmail data sources with email agent enabled and process each.

    Returns:
        Summary dict with aggregated processing results.
    """
    ds_service = injector.get(DataSourceService)
    gmail_datasources = await ds_service.get_by_type("gmail", decrypt_sensitive=True)

    total_processed = 0
    total_failed = 0
    results = []

    for ds in gmail_datasources:
        if not ds.is_active:
            continue

        connection_data = ds.connection_data if isinstance(ds.connection_data, dict) else {}
        agent_config_data = connection_data.get("email_agent_config")

        if not agent_config_data:
            continue

        # Parse config
        try:
            agent_config_data["data_source_id"] = str(ds.id)
            config = EmailAgentConfig(**agent_config_data)
        except Exception as e:
            logger.error(f"Invalid email agent config for data source {ds.id}: {e}")
            total_failed += 1
            continue

        if not config.polling_enabled:
            continue

        # Process emails for this data source
        try:
            logger.info(f"Processing email agent for data source: {ds.name} ({ds.id})")
            result = await process_emails_for_datasource(ds.id, config)
            total_processed += result.get("processed", 0)
            results.append({
                "data_source_id": str(ds.id),
                "data_source_name": ds.name,
                "processed": result.get("processed", 0),
                "actions": result.get("actions", []),
                "errors": result.get("errors", []),
            })
        except Exception as e:
            logger.error(f"Error processing email agent for data source {ds.id}: {e}")
            total_failed += 1
            results.append({
                "data_source_id": str(ds.id),
                "data_source_name": ds.name,
                "error": str(e),
            })

    return {
        "status": "completed",
        "total_processed": total_processed,
        "total_failed": total_failed,
        "data_sources": results,
        "timestamp": utc_now().isoformat(),
    }
