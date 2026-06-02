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
        examples=["주민등록번호 901212-1234567을 포함한 이메일을 작성해줘."],
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
        examples=["auto", "openrouter/google/gemini-3.1-flash-lite"],
    )
    messages: list[ChatMessage] = Field(
        ...,
        description="Conversation messages.",
        examples=[[ChatMessage(role="user", content="hello")]],
    )
    temperature: float | None = Field(
        default=0.7,
        ge=0.0,
        le=2.0,
        description="Sampling temperature.",
        examples=[0.7],
    )
    max_tokens: int | None = Field(
        default=256,
        ge=1,
        description="Maximum tokens to generate.",
        examples=[256],
    )
    stream: bool = Field(
        default=False,
        description="Whether to stream the response.",
        examples=[False],
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

    index: int = Field(default=0, description="Choice index.", examples=[0])
    message: ChatMessage = Field(..., description="Response message.", examples=[ChatMessage(role="assistant", content="처리 완료")])
    finish_reason: str = Field(default="stop", description="Completion stop reason.", examples=["stop"])


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

    prompt_tokens: int = Field(default=0, ge=0, description="Prompt token count.", examples=[150])
    completion_tokens: int = Field(default=0, ge=0, description="Completion token count.", examples=[80])
    total_tokens: int = Field(default=0, ge=0, description="Total token count.", examples=[230])


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

    id: str = Field(..., description="Response identifier.", examples=["chatcmpl-abc123"])
    object: str = Field(default="chat.completion", description="Object type.", examples=["chat.completion"])
    created: int = Field(..., description="Unix timestamp of creation.", examples=[1717200000])
    model: str = Field(..., description="Model identifier.", examples=["privacy-router"])
    choices: list[ChatChoice] = Field(..., description="Completion choices.")
    usage: ChatUsage = Field(
        default_factory=ChatUsage, description="Token usage."
    )
    route_result: RouteResult | None = Field(
        default=None,
        description="Privacy Router routing metadata.",
        examples=[RouteResult(endpoint="external_api", requires_masking=True, description="민감 정보 마스킹 후 외부 API로 전송")],
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
        ..., description="Sensitivity assessment.", examples=[{"is_sensitive": True, "rationale": "주민등록번호 탐지"}]
    )
    judgment: Any = Field(
        ..., description="Policy judgment.", examples=[{"policy_action": "mask_and_send"}]
    )
    route: RouteResult = Field(
        ..., description="Routing result.", examples=[RouteResult(endpoint="external_api", requires_masking=True, description="마스킹 후 전송")]
    )
    response: str | None = Field(
        default=None, description="Final LLM response text.", examples=["이메일 초안: ..."]
    )
