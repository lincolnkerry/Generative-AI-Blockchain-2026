"""Database models — SQLModel ORM for PostgreSQL/SQLite.

Tables:
    - providers: API provider configuration
    - api_keys: authentication keys per provider
    - models: registered models with tier (local/external)
    - agent_configs: per-agent model assignment
    - usage_logs: request/response tracking
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlmodel import Field, Relationship, SQLModel


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

    models: list["Model"] = Relationship(back_populates="provider")
    api_keys: list["ApiKey"] = Relationship(back_populates="provider")


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

    provider: Provider = Relationship(back_populates="api_keys")


class Model(SQLModel, table=True):
    """Registered AI model."""

    __tablename__ = "models"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    provider_id: str = Field(foreign_key="providers.id")
    model_id: str = Field(...)
    display_name: str | None = Field(default=None)
    tier: str = Field(default="external")  # local | external
    cost_per_1m_tokens: float = Field(default=0.0, ge=0.0)
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    provider: Provider = Relationship(back_populates="models")


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
