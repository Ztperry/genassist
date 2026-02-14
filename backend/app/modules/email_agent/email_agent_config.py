"""
Configuration model for the Email Agent feature.

The configuration is stored in the DataSource.connection_data JSONB field
under the "email_agent_config" key, alongside the existing OAuth token data.
"""

from typing import Optional, List, Literal
from uuid import UUID
from pydantic import BaseModel, Field


class EmailAgentConfig(BaseModel):
    """Configuration for the Email Agent on a Gmail data source."""

    data_source_id: UUID
    llm_provider_id: Optional[str] = None
    polling_enabled: bool = True
    mode: Literal["autonomous", "recommend_only"] = "autonomous"
    system_prompt: Optional[str] = None
    max_emails_per_poll: int = Field(default=10, ge=1, le=50)
    auto_mark_as_read: bool = True
    rules: Optional[str] = None
    allowed_actions: List[str] = Field(
        default=[
            "reply_to_email",
            "mark_as_read",
            "forward_email",
            "flag_for_review",
            "categorize",
            "ignore",
        ]
    )

    class Config:
        json_schema_extra = {
            "example": {
                "data_source_id": "123e4567-e89b-12d3-a456-426614174000",
                "llm_provider_id": None,
                "polling_enabled": True,
                "mode": "autonomous",
                "system_prompt": None,
                "max_emails_per_poll": 10,
                "auto_mark_as_read": True,
                "rules": "Always flag emails from legal@company.com for review.",
                "allowed_actions": [
                    "reply_to_email",
                    "mark_as_read",
                    "forward_email",
                    "flag_for_review",
                    "categorize",
                    "ignore",
                ],
            }
        }
