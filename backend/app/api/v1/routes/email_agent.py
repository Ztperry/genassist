"""
REST API endpoints for the Email Agent feature.

Provides configuration management, manual triggering, and history
retrieval for email agents on Gmail data sources.
"""

import logging
from uuid import UUID
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from fastapi_injector import Injected

from app.auth.dependencies import auth
from app.services.datasources import DataSourceService
from app.schemas.datasource import DataSourceUpdate
from app.modules.email_agent.email_agent_config import EmailAgentConfig
from app.modules.email_agent.email_agent import (
    process_emails_for_datasource,
    get_processing_history,
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Email Agent"], dependencies=[Depends(auth)])


@router.get("/configs")
async def list_email_agent_configs(
    ds_service: DataSourceService = Injected(DataSourceService),
):
    """List all Gmail data sources and their email agent configurations."""
    gmail_datasources = await ds_service.get_by_type("gmail")
    configs = []
    for ds in gmail_datasources:
        connection_data = ds.connection_data if isinstance(ds.connection_data, dict) else {}
        agent_config = connection_data.get("email_agent_config")

        configs.append({
            "data_source_id": str(ds.id),
            "data_source_name": ds.name,
            "is_active": ds.is_active,
            "email_agent_config": agent_config,
            "has_email_agent": agent_config is not None,
        })

    return configs


@router.get("/{ds_id}/config")
async def get_email_agent_config(
    ds_id: UUID,
    ds_service: DataSourceService = Injected(DataSourceService),
):
    """Get the email agent configuration for a specific Gmail data source."""
    ds = await ds_service.get_by_id(ds_id)
    if not ds:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Data source with ID {ds_id} not found",
        )

    connection_data = ds.connection_data if isinstance(ds.connection_data, dict) else {}
    agent_config = connection_data.get("email_agent_config")

    return {
        "data_source_id": str(ds.id),
        "data_source_name": ds.name,
        "email_agent_config": agent_config,
    }


@router.put("/{ds_id}/config")
async def update_email_agent_config(
    ds_id: UUID,
    config: dict,
    ds_service: DataSourceService = Injected(DataSourceService),
):
    """Update the email agent configuration for a Gmail data source.

    The config dict is validated against EmailAgentConfig and stored
    in connection_data["email_agent_config"].
    """
    ds = await ds_service.get_by_id(ds_id)
    if not ds:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Data source with ID {ds_id} not found",
        )

    # Validate the config
    try:
        config["data_source_id"] = str(ds_id)
        validated = EmailAgentConfig(**config)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid email agent configuration: {str(e)}",
        )

    # Patch connection_data with the new config
    connection_data = ds.connection_data if isinstance(ds.connection_data, dict) else {}
    connection_data["email_agent_config"] = validated.model_dump(mode="json")

    ds_update = DataSourceUpdate(
        name=ds.name,
        source_type=ds.source_type,
        is_active=ds.is_active,
        connection_data=connection_data,
    )
    updated = await ds_service.update(ds_id, ds_update)

    return {
        "data_source_id": str(ds_id),
        "data_source_name": ds.name,
        "email_agent_config": connection_data.get("email_agent_config"),
        "message": "Email agent configuration updated successfully",
    }


@router.post("/{ds_id}/trigger")
async def trigger_email_agent(
    ds_id: UUID,
    background_tasks: BackgroundTasks,
    ds_service: DataSourceService = Injected(DataSourceService),
):
    """Manually trigger the email agent for a specific data source.

    Runs the email agent processing in the background and returns immediately.
    """
    ds = await ds_service.get_by_id(ds_id, decrypt_sensitive=True)
    if not ds:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Data source with ID {ds_id} not found",
        )

    connection_data = ds.connection_data if isinstance(ds.connection_data, dict) else {}
    agent_config_data = connection_data.get("email_agent_config")

    if not agent_config_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No email agent configuration found for this data source. Configure it first.",
        )

    try:
        agent_config_data["data_source_id"] = str(ds_id)
        config = EmailAgentConfig(**agent_config_data)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid email agent configuration: {str(e)}",
        )

    # Run processing in background
    background_tasks.add_task(process_emails_for_datasource, ds_id, config)

    return {
        "message": "Email agent processing triggered",
        "data_source_id": str(ds_id),
        "mode": config.mode,
    }


@router.get("/{ds_id}/history")
async def get_email_agent_history(
    ds_id: UUID,
    ds_service: DataSourceService = Injected(DataSourceService),
):
    """Get recent processing history for a data source's email agent."""
    ds = await ds_service.get_by_id(ds_id)
    if not ds:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Data source with ID {ds_id} not found",
        )

    history = await get_processing_history(ds_id)

    return {
        "data_source_id": str(ds_id),
        "data_source_name": ds.name,
        "history": history,
        "count": len(history),
    }


@router.delete("/{ds_id}/config")
async def delete_email_agent_config(
    ds_id: UUID,
    ds_service: DataSourceService = Injected(DataSourceService),
):
    """Remove the email agent configuration from a data source."""
    ds = await ds_service.get_by_id(ds_id)
    if not ds:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Data source with ID {ds_id} not found",
        )

    connection_data = ds.connection_data if isinstance(ds.connection_data, dict) else {}
    if "email_agent_config" not in connection_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No email agent configuration found for this data source",
        )

    del connection_data["email_agent_config"]

    ds_update = DataSourceUpdate(
        name=ds.name,
        source_type=ds.source_type,
        is_active=ds.is_active,
        connection_data=connection_data,
    )
    await ds_service.update(ds_id, ds_update)

    return {
        "message": "Email agent configuration removed",
        "data_source_id": str(ds_id),
    }
