"""Privacy Router Server — HTTP API routes.

Endpoints:
    ``GET  /v1/models``           — OpenAI-compatible model registry
    ``POST /v1/chat/completions``  — OpenAI-compatible chat (pipeline + forwarding)
    ``GET  /``                     — interactive web chat UI
"""

from __future__ import annotations
import logging

import yaml

import json
import time
import uuid
from pathlib import Path
from typing import Any

from fastapi import Depends, Request
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse

from agents.extractor import Extractor
from agents.masker import Masker
from agents.router import PrivacyRouter
from agents.router.schemas import PipelineResult, RouteResult
from server.api import STATIC_DIR
from server.api.main import app
from server.api.adapter import adapter_for
from server.config import get_config
from server.api.auth import require_auth
from server.observability import timed_span, pii_detected, pii_masked
import hashlib


# ── Helpers ──────────────────────────────────────────────────────────────────


def _extract_records(text: str) -> list[dict[str, str]]:
    """Extract sensitive records from text."""
    ext = Extractor()
    result = ext.extract(text)
    return [{"category": r.category, "span": r.span} for r in result.records]


def _make_chat_id() -> str:
    return f"chatcmpl-{uuid.uuid4().hex[:12]}"


def _resolve_api_base(model_id: str) -> str | None:
    """Resolve api_base for a model from config."""
    from config import resolve_model
    try:
        spec = resolve_model(get_config(), model_id)
        return spec.api_base
    except Exception:
        return None


def _log_usage(
    event: str,
    text: str,
    is_sensitive: bool,
    records_count: int,
    policy_action: str | None,
    model_used: str | None,
    latency_ms: float,
) -> None:
    """Record a usage log entry (never fails the request)."""
    try:
        from db.models import UsageLog
        from db.session import get_session

        session = get_session()
        try:
            log = UsageLog(
                event=event,
                input_hash=hashlib.sha256(text.encode()).hexdigest()[:16],
                is_sensitive=is_sensitive,
                records_count=records_count,
                policy_action=policy_action,
                model_used=model_used,
                latency_ms=latency_ms,
            )
            session.add(log)
            session.commit()
        finally:
            session.close()
    except Exception:
        pass


def _sensitivity_meta(pipeline: PipelineResult) -> dict[str, Any]:
    """Build privacy metadata from pipeline result."""
    records = [
        {"category": r.category, "span": r.span, "confidence": r.confidence,
         "is_essential": r.is_essential, "reasoning": r.reasoning}
        for r in pipeline.records
    ]
    return {
        "is_sensitive": pipeline.sensitivity.is_sensitive,
        "extraction_records": records,
        "policy_action": pipeline.judgment.policy_action,
        "route": pipeline.route.endpoint,
    }


def _chat_response(
    content: str,
    finish_reason: str = "stop",
    usage: dict[str, int] | None = None,
    privacy_meta: dict[str, Any] | None = None,
    status_code: int = 200,
) -> JSONResponse:
    """Build a standard chat completion JSON response."""
    return JSONResponse(
        status_code=status_code,
        content={
            "id": _make_chat_id(),
            "object": "chat.completion",
            "created": int(time.time()),
            "model": "privacy-router",
            "choices": [{
                "index": 0,
                "message": {"role": "assistant", "content": content},
                "finish_reason": finish_reason,
            }],
            "usage": usage or {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
            "privacy_router": privacy_meta or {},
        },
    )


def _error_response(status_code: int, message: str, error_type: str) -> JSONResponse:
    """Build a standard error JSON response."""
    return JSONResponse(
        status_code=status_code,
        content={"error": {"message": message, "type": error_type}},
    )


# ── GET /v1/models ───────────────────────────────────────────────────────────


@app.get("/v1/models")
async def list_models():
    """List available models from the config registry."""
    cfg = get_config()
    return {
        "object": "list",
        "data": [
            {
                "id": f"privacy-router/{m.id}",
                "object": "model",
                "created": 0,
                "owned_by": "privacy-router",
            }
            for m in cfg.models
        ],
    }


# ── GET /api/settings (public, for demo UI) ──────────────────────────────


@app.get("/api/settings")
async def get_settings():
    """Return agent config for the demo web UI (no auth required)."""
    cfg = get_config()
    return {
        "models": [
            {"id": m.id, "tier": m.tier, "cost_per_1m_tokens": m.cost_per_1m_tokens, "api_base": m.api_base}
            for m in cfg.models
        ],
        "extractor": {"model": cfg.extractor.model, "config": {"temperature": cfg.extractor.config.temperature, "max_tokens": cfg.extractor.config.max_tokens}},
        "judge": {"model": cfg.judge.model, "config": {"temperature": cfg.judge.config.temperature, "max_tokens": cfg.judge.config.max_tokens}},
        "generator": {"model": cfg.generator.model, "config": {"temperature": cfg.generator.config.temperature, "max_tokens": cfg.generator.config.max_tokens}},
        "local": {"model": cfg.local.model, "config": {"temperature": cfg.local.config.temperature, "max_tokens": cfg.local.config.max_tokens}},
    }

@app.post("/api/settings")
async def update_settings(request: Request):
    """Update agent config for the demo web UI. Persists to YAML."""
    import server.config as server_cfg
    body = await request.json()

    # Read the YAML file, update agent model fields, write back
    config_path = Path(".privacy-router.config.yaml")
    with open(config_path, "r") as f:
        raw = yaml.safe_load(f)

    for agent_name in ("extractor", "judge", "generator", "local"):
        if agent_name in body:
            entry = body[agent_name]
            if agent_name not in raw:
                raw[agent_name] = {}
            if "model" in entry:
                raw[agent_name]["model"] = entry["model"]

    with open(config_path, "w") as f:
        yaml.safe_dump(raw, f, allow_unicode=True, default_flow_style=False, sort_keys=False)

    # Invalidate the cached config so next read picks up changes
    server_cfg._config = None

    return {"status": "ok"}


# ── POST /v1/chat/completions ───────────────────────────────────────────────


@app.post("/v1/chat/completions")
async def chat_completions(request: Request, _auth: str = Depends(require_auth)):
    """OpenAI-compatible chat completions with privacy pipeline."""
    body = await request.json()
    cfg = get_config()
    messages: list[dict] = body.get("messages", [])
    temperature: float = body.get("temperature", 0.7)
    max_tokens: int = body.get("max_tokens", 256)
    stream: bool = body.get("stream", False)
    tools: list | None = body.get("tools")
    tool_choice: str | dict | None = body.get("tool_choice")

    user_text = " ".join(m["content"] for m in messages if m.get("role") == "user") \
        or " ".join(m["content"] for m in messages)

    # ── Resolve model ───────────────────────────────────────────────────
    raw_model: str = body.get("model", "")
    if raw_model.startswith("privacy-router/"):
        raw_model = raw_model[len("privacy-router/"):]
    backend_model = raw_model if raw_model else cfg.generator.model

    registered_ids = [m.id for m in cfg.models]
    if backend_model not in registered_ids:
        return _error_response(400, f"Model {backend_model!r} not registered. Available: {registered_ids}", "invalid_model")

    try:
        adapter = adapter_for(backend_model)
    except ValueError as exc:
        return _error_response(502, str(exc), "unknown_backend")

    backend_model = adapter.resolve_backend_model(backend_model)
    # ── Run pipeline ────────────────────────────────────────────────────
    with timed_span("pipeline", {"model": backend_model}) as span:
        pipeline = PrivacyRouter().process(user_text)
        policy = pipeline.route
        meta = _sensitivity_meta(pipeline)

        # Record PII metrics
        n_records = len(pipeline.records)
        if n_records:
            pii_detected.add(n_records)
        if policy.requires_masking:
            pii_masked.add(n_records)

        span.set_attribute("policy_action", policy.endpoint)
        span.set_attribute("pii_count", n_records)

        # Record usage log
        _log_usage("chat_completions", user_text, bool(n_records), n_records, policy.endpoint, backend_model, 0)

    # ── prompt_user ─────────────────────────────────────────────────────
    if policy.endpoint == "prompt":
        confirm = request.headers.get("X-Privacy-Router-Confirm", "").lower()
        if confirm not in ("true", "1"):
            records = [
                {
                    "category": r.category,
                    "span": r.span,
                    "confidence": r.confidence,
                    "is_essential": r.is_essential,
                    "reasoning": r.reasoning,
                }
                for r in pipeline.records
            ]
            meta["extraction_records"] = records
            meta["action_required"] = "confirm"
            meta["confirm_message"] = (
                "이 요청에는 민감한 정보가 포함되어 있습니다:\n\n"
                + "\n".join(f"  • {r['span']}" for r in records)
                + "\n\n이 정보를 마스킹하면 AI가 질문의 맥락을 이해할 수 없어\n"
                "유의미한 답변을 제공하기 어렵습니다.\n\n"
                "원본 텍스트를 외부 AI 서비스로 전송하면,\n"
                "위 정보가 해당 서비스에 전달됩니다."
            )
            return _chat_response(policy.description, privacy_meta=meta, status_code=409)

    # ── block ───────────────────────────────────────────────────────────
    if policy.endpoint == "blocked":
        records = _extract_records(user_text)
        meta["extraction_records"] = records
        detected = "\n".join(f"  • {r['span']}" for r in records)
        content = (
            "🚫 이 요청은 차단되었습니다.\n\n"
            f"탐지된 민감 정보:\n{detected}\n\n"
            "주민등록번호, 비밀번호 등 극도로 민감한 정보를 직접 질의하는 요청은\n"
            "외부 AI 서비스로 전송할 수 없습니다.\n\n"
            f"판단 근거: {policy.description}"
        )
        return _chat_response(content, privacy_meta=meta)

    # ── local_api — try local model, fallback to masked external ───────
    if policy.endpoint == "local_api":
        local_model = cfg.local.model
        local_adapter = adapter_for(local_model)
        local_resolved = local_adapter.resolve_backend_model(local_model)
        local_api_base = _resolve_api_base(local_model)

        # Try local model first (non-streaming only for local)
        if not stream:
            try:
                # Mask PII before sending to local model
                masked_messages = messages
                masking_session_id = None
                masking_records_out = []
                if n_records > 0:
                    ext = Extractor()
                    extraction = ext.extract(user_text)
                    records_dict = [r.model_dump() for r in extraction.records]
                    masker = Masker()
                    mask_result = masker.mask(user_text, records_dict)
                    from agents.masker import ContractStore
                    import hashlib as _hashlib
                    store = ContractStore()
                    input_hash = _hashlib.sha256(user_text.encode()).hexdigest()[:16]
                    masking_session_id = store.create_session(
                        chat_id=request.headers.get("x-chat-id"),
                        input_hash=input_hash,
                        record_count=len(extraction.records),
                        policy_action=policy.endpoint,
                    )
                    store.save_records(
                        session_id=masking_session_id,
                        records=records_dict,
                        placeholder_map=mask_result.contract.placeholder_map,
                    )
                    for placeholder, original in mask_result.contract.placeholder_map.items():
                        uid = _hashlib.sha256(original.encode()).hexdigest()[:8]
                        matching = next((r for r in extraction.records if r.span == original), None)
                        masking_records_out.append({
                            "uid": uid,
                            "category": matching.category if matching else "UNKNOWN",
                            "placeholder": placeholder,
                            "confidence": matching.confidence if matching else 0.0,
                            "is_essential": matching.is_essential if matching else False,
                        })
                    masked_messages = [
                        {**m, "content": mask_result.masked_text} if m.get("role") == "user" else m
                        for m in messages
                    ]
                    meta["masked_text"] = mask_result.masked_text
                    meta["masking_session_id"] = masking_session_id
                    meta["placeholder_map"] = masking_records_out

                local_kwargs: dict = {}
                if tools:
                    local_kwargs["tools"] = tools
                if tool_choice:
                    local_kwargs["tool_choice"] = tool_choice
                local_resp = local_adapter.call(
                    local_resolved, masked_messages,
                    cfg.local.config.temperature, cfg.local.config.max_tokens,
                    api_base=local_api_base, **local_kwargs,
                )
                local_msg = local_resp.choices[0].message
                local_content = local_msg.content or ""
                local_tool_calls = getattr(local_msg, "tool_calls", None)
                local_fmt = local_adapter.format_response(local_resp, local_content)
                meta["model_used"] = local_model

                # Handle tool calls in local_api response
                if local_tool_calls:
                    tc_list = []
                    for tc in local_tool_calls:
                        tc_dict = {"id": tc.id, "type": "function", "function": {"name": tc.function.name, "arguments": tc.function.arguments}}
                        tc_list.append(tc_dict)
                    return JSONResponse(
                        status_code=200,
                        content={
                            "id": _make_chat_id(),
                            "object": "chat.completion",
                            "created": int(time.time()),
                            "model": "privacy-router",
                            "choices": [{
                                "index": 0,
                                "message": {"role": "assistant", "content": None, "tool_calls": tc_list},
                                "finish_reason": "tool_calls",
                            }],
                            "usage": local_fmt["usage"],
                            "privacy_router": meta,
                        },
                    )

                return _chat_response(local_content, local_fmt["finish_reason"], local_fmt["usage"], meta)
            except Exception:
                logging.getLogger(__name__).debug('Local model fallback failed', exc_info=True)

        # Local model failed or streaming — fall through to mask_and_send below
        policy = RouteResult(
            endpoint="external_api",
            requires_masking=True,
            description=policy.description + " (local model unavailable, masked fallback)",
        )

    # ── mask_and_send / allow — forward to backend ──────────────────────
    contract: Masker | None = None
    forward_messages = messages
    masking_session_id = None
    masking_records_out = []
    if policy.requires_masking:
        ext = Extractor()
        extraction = ext.extract(user_text)
        records_dict = [r.model_dump() for r in extraction.records]
        masker = Masker()
        mask_result = masker.mask(user_text, records_dict)
        contract = mask_result.contract
        # Persist to ContractStore
        from agents.masker import ContractStore
        import hashlib as _hashlib
        store = ContractStore()
        input_hash = _hashlib.sha256(user_text.encode()).hexdigest()[:16]
        masking_session_id = store.create_session(
            chat_id=request.headers.get("x-chat-id"),
            input_hash=input_hash,
            record_count=len(extraction.records),
            policy_action=policy.endpoint,
        )
        store.save_records(
            session_id=masking_session_id,
            records=records_dict,
            placeholder_map=mask_result.contract.placeholder_map,
        )
        # Build masking_records for response
        for placeholder, original in mask_result.contract.placeholder_map.items():
            uid = _hashlib.sha256(original.encode()).hexdigest()[:8]
            matching = next((r for r in extraction.records if r.span == original), None)
            masking_records_out.append({
                "uid": uid,
                "category": matching.category if matching else "UNKNOWN",
                "placeholder": placeholder,
                "confidence": matching.confidence if matching else 0.0,
                "is_essential": matching.is_essential if matching else False,
            })
        meta["extraction_records"] = [{"category": r.category, "span": r.span, "confidence": r.confidence,
                           "is_essential": r.is_essential} for r in extraction.records]
        meta["original_text"] = user_text
        meta["masked_text"] = mask_result.masked_text
        meta["placeholders"] = [
            {"placeholder": p, "category": r.category, "span": r.span}
            for p, r in zip(mask_result.contract.placeholder_map.keys(), extraction.records)
        ]
        meta["masking_session_id"] = masking_session_id
        meta["placeholder_map"] = masking_records_out
        forward_messages = [
            {**m, "content": mask_result.masked_text} if m.get("role") == "user" else m
            for m in messages
        ]

    api_base = _resolve_api_base(backend_model)

    # ── Streaming ───────────────────────────────────────────────────────
    if stream:
        from server.api.streaming import StreamingHydrator

        hydrator = StreamingHydrator(contract)

        async def _stream():
            chunk_id = _make_chat_id()
            created = int(time.time())
            stream_kwargs: dict = {}
            if tools:
                stream_kwargs["tools"] = tools
            if tool_choice:
                stream_kwargs["tool_choice"] = tool_choice
            try:
                response = adapter.call(
                    backend_model, forward_messages,
                    temperature, max_tokens, api_base=api_base, stream=True, **stream_kwargs,
                )
                for part in response:
                    delta = part.choices[0].delta.content or ""
                    if not delta:
                        continue
                    for hydrated in hydrator.feed(delta):
                        yield f"data: {json.dumps({'id': chunk_id, 'object': 'chat.completion.chunk', 'created': created, 'model': 'privacy-router', 'choices': [{'index': 0, 'delta': {'content': hydrated}}]})}\n\n"
                for hydrated in hydrator.flush():
                    yield f"data: {json.dumps({'id': chunk_id, 'object': 'chat.completion.chunk', 'created': created, 'model': 'privacy-router', 'choices': [{'index': 0, 'delta': {'content': hydrated}}]})}\n\n"
                yield f"data: {json.dumps({'id': chunk_id, 'object': 'chat.completion.chunk', 'created': created, 'model': 'privacy-router', 'choices': [{'index': 0, 'delta': {}, 'finish_reason': 'stop'}]})}\n\n"
                yield "data: [DONE]\n\n"
            except Exception as exc:
                yield f"data: {json.dumps({'error': {'message': str(exc), 'type': 'backend_error'}})}\n\n"

        return StreamingResponse(_stream(), media_type="text/event-stream")

    # ── Non-streaming ───────────────────────────────────────────────────
    call_kwargs: dict = {}
    if tools:
        call_kwargs["tools"] = tools
    if tool_choice:
        call_kwargs["tool_choice"] = tool_choice
    try:
        response = adapter.call(backend_model, forward_messages, temperature, max_tokens, api_base=api_base, **call_kwargs)
        msg = response.choices[0].message
        content: str = msg.content or ""
        tool_calls = getattr(msg, "tool_calls", None)
        import sys as _dbg_sys
        print(f"DEBUG PROXY: content={repr(msg.content)[:100]}", file=_dbg_sys.stderr)
        print(f"DEBUG PROXY: tool_calls={tool_calls}", file=_dbg_sys.stderr)
        print(f"DEBUG PROXY: finish_reason={response.choices[0].finish_reason}", file=_dbg_sys.stderr)
        formatted = adapter.format_response(response, content)
    except Exception as exc:
        return _error_response(502, f"Backend model error: {exc}", "backend_error")

    # Hydrate (only for text content, not tool calls)
    if policy.requires_masking and contract and not tool_calls:
        try:
            hydrated = Masker().hydrate(content, contract)
            content = hydrated.hydrated_text
        except Exception:
            pass

    meta["model_used"] = backend_model

    # Build response with tool calls if present
    if tool_calls:
        tc_list = []
        for tc in tool_calls:
            tc_dict = {"id": tc.id, "type": "function", "function": {"name": tc.function.name, "arguments": tc.function.arguments}}
            tc_list.append(tc_dict)
        return JSONResponse(
            status_code=200,
            content={
                "id": _make_chat_id(),
                "object": "chat.completion",
                "created": int(time.time()),
                "model": "privacy-router",
                "choices": [{
                    "index": 0,
                    "message": {"role": "assistant", "content": None, "tool_calls": tc_list},
                    "finish_reason": "tool_calls",
                }],
                "usage": formatted["usage"],
                "privacy_router": meta,
            },
        )

    return _chat_response(content, formatted["finish_reason"], formatted["usage"], meta)


# ── GET / — landing page ─────────────────────────────────────────────────────


@app.get("/", response_class=HTMLResponse)
async def landing_page():
    """Serve the landing page."""
    html_path = STATIC_DIR / "index.html"
    if html_path.exists():
        return HTMLResponse(html_path.read_text())
    return HTMLResponse("<h1>Privacy Router</h1><p>Landing page not found.</p>")


# ── GET /demo — web chat UI ──────────────────────────────────────────────────


@app.get("/demo", response_class=HTMLResponse)
async def chat_ui():
    """Serve the interactive web chat UI."""
    html_path = STATIC_DIR / "demo.html"
    if html_path.exists():
        return HTMLResponse(html_path.read_text())
    return HTMLResponse("<h1>Privacy Router</h1><p>Chat UI not found.</p>")


@app.get("/admin", response_class=HTMLResponse)
async def admin_ui():
    """Serve the admin dashboard."""
    html_path = STATIC_DIR / "admin.html"
    if html_path.exists():
        return HTMLResponse(html_path.read_text())
    return HTMLResponse("<h1>Privacy Router Admin</h1><p>Admin UI not found.</p>")
# ── Dashboard Data API ─────────────────────────────────────────────────────


@app.get("/api/v1/dashboard-data")
async def dashboard_data():
    """Return all data needed for the usage log dashboard.

    Reads from the database and returns:
    - usage_logs: all log entries
    - masking_records: all masking records linked to sessions
    - masking_sessions: all masking sessions
    - summary: aggregated stats
    """
    from db.session import engine
    from sqlmodel import Session, text

    with Session(engine) as s:
        # Usage logs
        logs = s.exec(text(
            "SELECT id, event, input_hash, is_sensitive, records_count, "
            "policy_action, model_used, latency_ms, status_code, "
            "to_char(created_at, 'YYYY-MM-DD HH24:MI:SS') as created_at "
            "FROM usage_logs ORDER BY created_at"
        )).mappings().all()

        # Masking sessions with records
        sessions = s.exec(text(
            "SELECT ms.id, ms.input_hash, ms.record_count, ms.policy_action, "
            "to_char(ms.created_at, 'YYYY-MM-DD HH24:MI:SS') as created_at "
            "FROM masking_sessions ms ORDER BY ms.created_at"
        )).mappings().all()

        # Masking records
        records = s.exec(text(
            "SELECT mr.id, mr.session_id, mr.category, mr.span, mr.placeholder, "
            "mr.confidence, mr.is_essential "
            "FROM masking_records mr ORDER BY mr.confidence DESC"
        )).mappings().all()

        # Summary stats
        summary = s.exec(text(
            "SELECT "
            "COUNT(*) as total, "
            "SUM(CASE WHEN is_sensitive THEN 1 ELSE 0 END) as sensitive, "
            "SUM(CASE WHEN NOT is_sensitive THEN 1 ELSE 0 END) as safe, "
            "SUM(CASE WHEN policy_action IN ('local_api','route_to_local') THEN 1 ELSE 0 END) as routed_local, "
            "SUM(CASE WHEN policy_action IN ('external_api','mask_and_send') THEN 1 ELSE 0 END) as masked_sent, "
            "SUM(CASE WHEN policy_action = 'route_to_external' THEN 1 ELSE 0 END) as allowed "
            "FROM usage_logs"
        )).mappings().one()

        # Daily breakdown
        daily = s.exec(text(
            "SELECT "
            "to_char(created_at, 'MM-DD') as date, "
            "COUNT(*) as total, "
            "SUM(CASE WHEN is_sensitive THEN 1 ELSE 0 END) as sensitive, "
            "SUM(CASE WHEN NOT is_sensitive THEN 1 ELSE 0 END) as safe, "
            "SUM(CASE WHEN policy_action IN ('local_api','route_to_local') THEN 1 ELSE 0 END) as routed_local, "
            "SUM(CASE WHEN policy_action IN ('external_api','mask_and_send') THEN 1 ELSE 0 END) as masked_sent, "
            "SUM(CASE WHEN policy_action = 'route_to_external' THEN 1 ELSE 0 END) as allowed "
            "FROM usage_logs "
            "GROUP BY to_char(created_at, 'MM-DD') "
            "ORDER BY to_char(created_at, 'MM-DD')"
        )).mappings().all()

    # Group records by session_id
    records_by_session = {}
    for r in records:
        sid = r["session_id"]
        if sid not in records_by_session:
            records_by_session[sid] = []
        records_by_session[sid].append(dict(r))

    return JSONResponse({
        "summary": dict(summary),
        "daily": [dict(d) for d in daily],
        "logs": [dict(l) for l in logs],
        "sessions": [dict(s) for s in sessions],
        "records_by_session": records_by_session,
    })


# ── Catch-all static file server ─────────────────────────────────────────────

from fastapi.responses import FileResponse
import mimetypes


@app.get("/{path:path}")
async def serve_static(path: str):
    """Serve static files from the SvelteKit build directory."""
    file_path = STATIC_DIR / path
    if file_path.is_file():
        mime, _ = mimetypes.guess_type(str(file_path))
        return FileResponse(str(file_path), media_type=mime)
    # Try with .html extension for SvelteKit routes
    html_path = STATIC_DIR / f"{path}.html"
    if html_path.is_file():
        return HTMLResponse(html_path.read_text())
    # Fallback to index.html for SPA routing
    index = STATIC_DIR / "index.html"
    if index.exists():
        return HTMLResponse(index.read_text())
    return HTMLResponse("<h1>404</h1>", status_code=404)
