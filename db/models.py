"""Database models — SQLModel ORM for PostgreSQL/SQLite.

Tables:
    - providers: API provider configuration
    - api_keys: authentication keys per provider
    - models: registered models with tier (local/external)
    - agent_configs: per-agent model assignment
    - usage_logs: request/response tracking
    - masking_sessions: masking session tracking with chat context
    - masking_contracts: per-session placeholder-to-hash mappings
"""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlmodel import Field, SQLModel


class Provider(SQLModel, table=True):
    """API provider configuration."""

    __tablename__ = "providers"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    name: str = Field(...)
    provider_type: str = Field(...)  # openrouter | openai | custom
    api_key_env: str | None = Field(default=None)
    api_base: str | None = Field(default=None)
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class ApiKey(SQLModel, table=True):
    """API key for authentication."""

    __tablename__ = "api_keys"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    provider_id: str = Field(foreign_key="providers.id")
    name: str = Field(default="default")
    key_hash: str = Field(...)
    prefix: str = Field(...)  # pr-xxxx...
    is_active: bool = Field(default=True)
    last_used_at: datetime | None = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Model(SQLModel, table=True):
    """Registered AI model."""

    __tablename__ = "models"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    provider_id: str = Field(foreign_key="providers.id")
    model_id: str = Field(...)
    display_name: str | None = Field(default=None)
    location: str = Field(default="external")  # local | external
    tier: str = Field(default="small")  # small | middle | large
    cost_per_1m_tokens: float = Field(default=0.0, ge=0.0)
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)



class AgentConfig(SQLModel, table=True):
    """Per-agent model assignment."""

    __tablename__ = "agent_configs"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    agent_name: str = Field(..., unique=True)  # extractor | judge | generator | local
    model_id: str = Field(foreign_key="models.id")
    temperature: float = Field(default=0.0, ge=0.0, le=2.0)
    max_tokens: int = Field(default=4096, ge=1)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class UsageLog(SQLModel, table=True):
    """Request/response tracking."""

    __tablename__ = "usage_logs"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    event: str = Field(...)  # classify | generate
    input_hash: str = Field(...)
    is_sensitive: bool = Field(default=False)
    records_count: int = Field(default=0)
    policy_action: str | None = Field(default=None)
    model_used: str | None = Field(default=None)
    latency_ms: float = Field(default=0.0)
    status_code: int = Field(default=200)
    created_at: datetime = Field(default_factory=datetime.utcnow)



class Response(SQLModel, table=True):
    """Stored OpenResponses-compatible response."""

    __tablename__ = "responses"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    model: str = Field(...)
    output_text: str = Field(default="")
    output_json: str = Field(default="{}")  # JSON string of full output
    status: str = Field(default="completed")
    created_at: datetime = Field(default_factory=datetime.utcnow)


class MaskingSession(SQLModel, table=True):
    """Masking session — tracks a conversation's masking context.

    Each masking session corresponds to a chat/conversation and stores
    the mapping between placeholder UIDs and original values.
    """

    __tablename__ = "masking_sessions"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    chat_id: str | None = Field(default=None, index=True)  # foreign key to chat/conversation
    input_hash: str = Field(default="")  # SHA-256 of original input
    record_count: int = Field(default=0)  # number of masked records
    policy_action: str = Field(default="")  # routing decision
    is_active: bool = Field(default=True)  # session still valid
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: datetime | None = Field(default=None)  # TTL for session


class MaskingRecord(SQLModel, table=True):
    """Individual masking record — placeholder-to-hash mapping.

    Each record stores the UID, category, placeholder, and SHA-256 hash
    of the original value. The original value is NEVER stored.
    """

    __tablename__ = "masking_records"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    session_id: str = Field(index=True)  # FK to masking_sessions.id
    uid: str = Field(index=True)  # deterministic UID: category + hash prefix
    category: str = Field(...)  # e.g., RESIDENT_REGISTRATION_NUMBER
    placeholder: str = Field(...)  # e.g., [RESIDENT_REGISTRATION_NUMBER#abc123]
    value_hash: str = Field(...)  # SHA-256 of original value (never stored)
    span: str = Field(default="")  # original text span (for audit only)
    confidence: float = Field(default=0.0)
    is_load_bearing: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)