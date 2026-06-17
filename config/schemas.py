"""Config schemas — Pydantic models for .privacy-router.config.yaml.

All public types are re-exported via ``config/__init__.py``.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


# ── Model spec ───────────────────────────────────────────────────────────────


class ModelSpec(BaseModel):
    """A single model entry in the model registry.

    litellm infers the provider from the ``id`` prefix:

    - ``openrouter/...`` → OpenRouter
    - ``openai/...`` → OpenAI or any OpenAI-compatible endpoint
      (set ``api_base`` for custom endpoints like Ollama, vLLM)
    - ``ollama/...`` → Ollama (auto-detected by litellm)
    - ``anthropic/...`` → Anthropic
    - ``google/...`` → Google (Gemini)

    API keys are resolved by litellm automatically from environment
    variables (``OPENAI_API_KEY``, ``ANTHROPIC_API_KEY``, etc.).

    Attributes
    ----------
    id : str
        litellm model identifier.
    api_base : str or None
        Base URL for OpenAI-compatible endpoints.
        Unnecessary for litellm-native providers (OpenRouter, etc.).
    location : str
        ``"local"`` (on-premises) or ``"external"`` (cloud API).
    tier : str
        Capability tier: ``"small"`` (<8B), ``"middle"`` (8-30B), or ``"large"`` (>30B).
    cost_per_1m_tokens : float
        Approximate cost per 1M input tokens (USD). Informational only.

    Examples
    --------
    >>> m = ModelSpec(id="openrouter/mistralai/ministral-3b-2512", location="external", tier="small", cost_per_1m_tokens=0.10)
    >>> m.tier
    'small'

    >>> local = ModelSpec(id="openai/qwen2.5:7b", api_base="http://localhost:11434/v1", location="local", tier="small", cost_per_1m_tokens=0.0)
    >>> local.location
    'local'
    """

    id: str = Field(
        ...,
        description="litellm model identifier. Prefix determines provider routing.",
        examples=["openrouter/mistralai/ministral-3b-2512", "openai/qwen2.5:7b"],
    )
    api_base: str | None = Field(
        default=None,
        description="Base URL for OpenAI-compatible endpoints. Not needed for native litellm providers.",
        examples=["http://localhost:11434/v1"],
    )
    location: Literal["local", "external"] = Field(
        default="external",
        description="Model location: local (on-premises) or external (cloud API).",
        examples=["local", "external"],
    )
    tier: Literal["small", "middle", "large"] = Field(
        ...,
        description="Capability tier: small (<8B), middle (8-30B), large (>30B).",
        examples=["small", "middle", "large"],
    )
    cost_per_1m_tokens: float = Field(
        ...,
        ge=0.0,
        description="Approximate cost per 1M input tokens (USD). Informational only.",
        examples=[0.10, 0.25],
    )


# ── Agent config ─────────────────────────────────────────────────────────────


class LLMConfig(BaseModel):
    """LLM call-level knobs shared by all agents.

    Attributes
    ----------
    temperature : float
        Sampling temperature (0.0 = deterministic).
    max_tokens : int
        Maximum completion tokens.

    Examples
    --------
    >>> c = LLMConfig(temperature=0.0, max_tokens=4096)
    >>> c.temperature
    0.0
    """

    temperature: float = Field(
        ...,
        ge=0.0,
        le=2.0,
        description="Sampling temperature.",
        examples=[0.0],
    )
    max_tokens: int = Field(
        ...,
        ge=1,
        description="Maximum completion tokens.",
        examples=[4096],
    )


class AgentConfig(BaseModel):
    """Per-agent configuration: which model to use and how.

    Attributes
    ----------
    model : str
        Model id (must match a key in the top-level ``models`` list).
    config : LLMConfig
        LLM call parameters.

    Examples
    --------
    >>> a = AgentConfig(model="openrouter/mistralai/ministral-3b-2512", config=LLMConfig(temperature=0.0, max_tokens=4096))
    >>> a.model
    'openrouter/mistralai/ministral-3b-2512'
    """

    model: str = Field(
        ...,
        description="Model id. Must appear in the top-level models registry.",
        examples=["openrouter/mistralai/ministral-3b-2512"],
    )
    config: LLMConfig = Field(
        ...,
        description="LLM call parameters (temperature, max_tokens).",
    )


# ── Top-level config ─────────────────────────────────────────────────────────


class PrivacyRouterConfig(BaseModel):
    """Root config for .privacy-router.config.yaml.

    Attributes
    ----------
    models : list of ModelSpec
        Available model registry.
    extractor : AgentConfig
        Extractor agent configuration.
    judge : AgentConfig
        Judge agent configuration.

    Examples
    --------
    >>> c = PrivacyRouterConfig(
    ...     models=[ModelSpec(id="openrouter/mistralai/ministral-3b-2512", tier="smol", cost_per_1m_tokens=0.10)],
    ...     extractor=AgentConfig(model="openrouter/mistralai/ministral-3b-2512", config=LLMConfig(temperature=0.0, max_tokens=4096)),
    ...     judge=AgentConfig(model="openrouter/google/gemini-3.1-flash-lite", config=LLMConfig(temperature=0.0, max_tokens=2048)),
    ... )
    >>> c.extractor.model
    'openrouter/mistralai/ministral-3b-2512'
    """

    models: list[ModelSpec] = Field(
        ...,
        min_length=1,
        description="Available model registry.",
    )
    extractor: AgentConfig = Field(
        ...,
        description="Extractor agent configuration.",
    )
    judge: AgentConfig = Field(
        ...,
        description="Judge agent configuration.",
    )
    generator: AgentConfig = Field(
        ...,
        description="Generator (external AI) agent configuration.",
    )
    local: AgentConfig = Field(
        ...,
        description="Local AI agent configuration (Ollama, vLLM, etc.).",
    )
