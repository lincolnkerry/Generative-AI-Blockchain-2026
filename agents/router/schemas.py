"""Schemas for the Router package.

Includes routing results and LiteLLM/OpenAI-compatible chat schemas
so the router can serve as a drop-in proxy.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


# ── Routing schemas ──────────────────────────────────────────────────────────


class RouteResult(BaseModel):
    """Concrete routing result produced by the Router.

    Attributes
    ----------
    endpoint : str
        Target endpoint: ``"external_api"`` or ``"local_api"``.
    requires_masking : bool
        Whether the text must be masked before transmission.
    description : str
        Human-readable description of the chosen path (Korean).
    """

    endpoint: str = Field(
        ...,
        description="Target endpoint: 'external_api' or 'local_api'.",
        examples=["external_api", "local_api"],
    )
    requires_masking: bool = Field(
        ...,
        description="Whether masking is required before sending.",
        examples=[True, False],
    )
    description: str = Field(
        ...,
        description="Human-readable description of the routing decision (Korean).",
        examples=["민감 정보 마스킹 후 외부 API로 전송, 응답 재수화"],
    )


# ── LiteLLM / OpenAI-compatible schemas ──────────────────────────────────────


class ChatMessage(BaseModel):
    """OpenAI-compatible chat message.

    Attributes
    ----------
    role : str
        One of ``"system"``, ``"user"``, or ``"assistant"``.
    content : str
        The message content.
    """

    role: str = Field(
        ...,
        description="Message role.",
        examples=["user"],
    )
    content: str = Field(
        ...,
        description="Message content.",
    )


class ChatRequest(BaseModel):
    """OpenAI-compatible chat completions request.

    Attributes
    ----------
    model : str, optional
        Model to use. Defaults to ``"auto"`` (routed by Privacy Router).
    messages : list of ChatMessage
        Conversation messages.
    temperature : float or None, optional
        Sampling temperature (0.0 ~ 2.0).
    max_tokens : int or None, optional
        Maximum completion tokens.
    stream : bool, optional
        Whether to stream the response.
    """

    model: str = Field(
        default="auto",
        description="Model identifier, or 'auto' for Privacy Router routing.",
    )
    messages: list[ChatMessage] = Field(
        ...,
        description="Conversation messages.",
    )
    temperature: float | None = Field(
        default=0.7,
        ge=0.0,
        le=2.0,
        description="Sampling temperature.",
    )
    max_tokens: int | None = Field(
        default=256,
        ge=1,
        description="Maximum tokens to generate.",
    )
    stream: bool = Field(
        default=False,
        description="Whether to stream the response.",
    )


class ChatChoice(BaseModel):
    """A single completion choice.

    Attributes
    ----------
    index : int
        Choice index.
    message : ChatMessage
        The response message.
    finish_reason : str
        Reason the generation stopped.
    """

    index: int = Field(default=0, description="Choice index.")
    message: ChatMessage = Field(..., description="Response message.")
    finish_reason: str = Field(default="stop", description="Completion stop reason.")


class ChatUsage(BaseModel):
    """Token usage statistics.

    Attributes
    ----------
    prompt_tokens : int
        Tokens in the prompt.
    completion_tokens : int
        Tokens in the completion.
    total_tokens : int
        Total tokens.
    """

    prompt_tokens: int = Field(default=0, ge=0, description="Prompt token count.")
    completion_tokens: int = Field(default=0, ge=0, description="Completion token count.")
    total_tokens: int = Field(default=0, ge=0, description="Total token count.")


class ChatResponse(BaseModel):
    """OpenAI-compatible chat completions response.

    Attributes
    ----------
    id : str
        Response identifier.
    object : str
        Always ``"chat.completion"``.
    created : int
        Unix timestamp.
    model : str
        Model used.
    choices : list of ChatChoice
        Completion choices.
    usage : ChatUsage
        Token usage statistics.
    route_result : RouteResult or None, optional
        Privacy Router's routing decision metadata.
    """

    id: str = Field(..., description="Response identifier.")
    object: str = Field(default="chat.completion", description="Object type.")
    created: int = Field(..., description="Unix timestamp of creation.")
    model: str = Field(..., description="Model identifier.")
    choices: list[ChatChoice] = Field(..., description="Completion choices.")
    usage: ChatUsage = Field(
        default_factory=ChatUsage, description="Token usage."
    )
    route_result: RouteResult | None = Field(
        default=None,
        description="Privacy Router routing metadata.",
    )


# ── Pipeline result ─────────────────────────────────────────────────────────


class PipelineResult(BaseModel):
    """Full result from the Privacy Router pipeline.

    Attributes
    ----------
    sensitivity : Sensitivity
        Sensitivity assessment from the Extractor.
    judgment : Judgment
        Policy judgment from the Judge.
    route : RouteResult
        Concrete routing result.
    response : str or None
        Final LLM response text (if execution was performed).
    """

    sensitivity: Any = Field(
        ..., description="Sensitivity assessment."
    )
    judgment: Any = Field(
        ..., description="Policy judgment."
    )
    route: RouteResult = Field(
        ..., description="Routing result."
    )
    response: str | None = Field(
        default=None, description="Final LLM response text."
    )
