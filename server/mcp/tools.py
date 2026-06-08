"""Privacy Router Server — Unified MCP tool.

Single entry point for agent integration. Agents call `process` with
raw text; the tool extracts sensitive info, applies routing policy,
optionally masks and forwards to an LLM, and returns the result.

Configuration is read from .privacy-router.config.yaml at startup.
"""

from __future__ import annotations

import hashlib
import time
from pathlib import Path
from typing import Any

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("privacy-router")


def _load_config() -> dict[str, Any]:
    """Load Privacy Router configuration from YAML."""
    import yaml

    config_path = Path(__file__).resolve().parents[2] / ".privacy-router.config.yaml"
    if not config_path.exists():
        return {}
    text = config_path.read_text(encoding="utf-8")
    # Resolve ${VAR} from environment
    import os
    import re
    def _resolve_env(match: re.Match) -> str:
        var = match.group(1)
        default = match.group(3) if match.group(3) else ""
        return os.environ.get(var, default)
    text = re.sub(r"\$\{(\w+)(:([^}]*))?\}", _resolve_env, text)
    return yaml.safe_load(text) or {}


@mcp.tool()
def process(
    text: str,
    action: str = "auto",
    model: str | None = None,
    chat_id: str | None = None,
) -> dict:
    """Process a prompt through the Privacy Router pipeline.

    This is the single entry point for all agent integrations.
    The pipeline: Extract → Judge → Route → (optional) Mask → (optional) LLM.

    Args:
        text: The raw prompt to process.
        action: Override routing action. One of:
            - "auto" (default): run full pipeline, decide automatically
            - "classify": extract + judge only, no LLM call
            - "generate": force LLM call (mask if needed)
            - "allow": skip privacy checks, forward directly
            - "hydrate": hydrate content using a stored masking contract (requires chat_id)
        model: Override the generator model from config.
        chat_id: Optional chat/conversation ID for masking session tracking.
            If provided, masking contract is persisted to DB and can be
            retrieved later for hydration.

    Returns:
        dict with keys:
            - action_taken: str — what happened
            - content: str | None — LLM response (if generation happened)
            - records: list[dict] — extracted sensitive information records
            - policy_action: str — routing decision
            - is_sensitive: bool — whether sensitive info was detected
            - requires_masking: bool — whether masking was applied
            - model_used: str | None — model that was called
            - latency_ms: float — total processing time
            - masking_session_id: str | None — DB session ID (when masking applied)
            - masking_records: list[dict] — per-record masking details with UIDs
    """
    import hashlib as _hashlib

    from agents.router import PrivacyRouter
    from agents.masker import ContractStore, Masker
    from agents.llm import call_llm

    config = _load_config()
    t0 = time.time()
    contract_store = ContractStore()

    # ── Step 0: Hydrate action (no pipeline, just contract lookup) ──────────
    if action == "hydrate":
        if not chat_id:
            return {
                "action_taken": "error",
                "content": None,
                "records": [],
                "policy_action": "hydrate",
                "is_sensitive": False,
                "requires_masking": False,
                "model_used": None,
                "latency_ms": 0.0,
                "masking_session_id": None,
                "masking_records": [],
                "error": "chat_id required for hydrate action",
            }
        contract = contract_store.load_contract(chat_id)
        if not contract:
            return {
                "action_taken": "error",
                "content": None,
                "records": [],
                "policy_action": "hydrate",
                "is_sensitive": False,
                "requires_masking": False,
                "model_used": None,
                "latency_ms": 0.0,
                "masking_session_id": None,
                "masking_records": [],
                "error": f"Masking session not found or expired: {chat_id}",
            }
        masker = Masker()
        hydrated = masker.hydrate(text, contract)
        latency_ms = (time.time() - t0) * 1000
        return {
            "action_taken": "hydrated",
            "content": hydrated.hydrated_text,
            "records": [],
            "policy_action": "hydrate",
            "is_sensitive": False,
            "requires_masking": False,
            "model_used": None,
            "latency_ms": latency_ms,
            "masking_session_id": chat_id,
            "masking_records": [],
            "records_restored": hydrated.count,
        }

    # ── Step 1: Extract + Judge (always runs unless action=allow) ──────────
    if action == "allow":
        gen_model = model or config.get("generator", {}).get("model", "")
        gen_cfg = config.get("generator", {}).get("config", {})
        if gen_model:
            content = call_llm(text, model=gen_model, **gen_cfg)
        else:
            content = None
        latency_ms = (time.time() - t0) * 1000
        _log_usage("process", text, False, 0, "allow", gen_model, latency_ms)
        return {
            "action_taken": "allowed",
            "content": content,
            "records": [],
            "policy_action": "allow",
            "is_sensitive": False,
            "requires_masking": False,
            "model_used": gen_model or None,
            "latency_ms": latency_ms,
            "masking_session_id": None,
            "masking_records": [],
        }

    # Run Extractor → Router pipeline
    pr = PrivacyRouter()
    pipeline = pr.process(text)

    is_sensitive = (
        pipeline.sensitivity.get("is_sensitive", False)
        if isinstance(pipeline.sensitivity, dict)
        else getattr(pipeline.sensitivity, "is_sensitive", False)
    )

    records = [
        {
            "category": r.category,
            "span": r.span,
            "confidence": r.confidence,
            "is_load_bearing": r.is_load_bearing,
            "reasoning": r.reasoning,
        }
        for r in pipeline.records
    ]

    policy_action = (
        pipeline.judgment.policy_action
        if hasattr(pipeline.judgment, "policy_action")
        else pipeline.route.endpoint
    )

    # ── Step 2: If classify-only, return here ─────────────────────────────
    if action == "classify":
        latency_ms = (time.time() - t0) * 1000
        _log_usage("process", text, is_sensitive, len(records), "classify", None, latency_ms)
        return {
            "action_taken": "classified",
            "content": None,
            "records": records,
            "policy_action": policy_action,
            "is_sensitive": is_sensitive,
            "requires_masking": False,
            "model_used": None,
            "latency_ms": latency_ms,
            "masking_session_id": None,
            "masking_records": [],
        }

    # ── Step 3: Apply routing decision ────────────────────────────────────
    if action == "generate":
        effective_action = "mask_and_send" if is_sensitive else "allow"
    else:
        effective_action = policy_action

    if effective_action == "prompt_user":
        latency_ms = (time.time() - t0) * 1000
        _log_usage("process", text, is_sensitive, len(records), "prompt_user", None, latency_ms)
        return {
            "action_taken": "prompt_user",
            "content": None,
            "records": records,
            "policy_action": "prompt_user",
            "is_sensitive": is_sensitive,
            "requires_masking": False,
            "model_used": None,
            "latency_ms": latency_ms,
            "masking_session_id": None,
            "masking_records": [],
            "description": "사용자 확인이 필요합니다. 민감 정보가 포함되어 있습니다.",
        }

    # ── Step 4: Mask if needed ────────────────────────────────────────────
    masked_text = text
    masking_result = None
    masking_session_id = None
    masking_records_out = []
    requires_masking = effective_action in ("mask_and_send", "selective_mask")

    if requires_masking and pipeline.records:
        masker = Masker()
        record_dicts = [
            {"category": r.category, "span": r.span, "start": r.start, "end": r.end}
            for r in pipeline.records
        ]
        masking_result = masker.mask(text, record_dicts)
        masked_text = masking_result.masked_text

        # Persist to DB
        input_hash = _hashlib.sha256(text.encode()).hexdigest()[:16]
        masking_session_id = contract_store.create_session(
            chat_id=chat_id,
            input_hash=input_hash,
            record_count=len(records),
            policy_action=effective_action,
        )
        contract_store.save_records(
            session_id=masking_session_id,
            records=records,
            placeholder_map=masking_result.contract.placeholder_map,
        )

        # Build masking_records for response
        for placeholder, original in masking_result.contract.placeholder_map.items():
            uid = _hashlib.sha256(original.encode()).hexdigest()[:8]
            matching = next((r for r in records if r["span"] == original), None)
            masking_records_out.append({
                "uid": uid,
                "category": matching["category"] if matching else "UNKNOWN",
                "placeholder": placeholder,
                "confidence": matching["confidence"] if matching else 0.0,
                "is_load_bearing": matching["is_load_bearing"] if matching else False,
            })

    # ── Step 5: Call LLM ──────────────────────────────────────────────────
    gen_model = model or config.get("generator", {}).get("model", "")
    gen_cfg = config.get("generator", {}).get("config", {})

    content = None
    if gen_model:
        try:
            content = call_llm(masked_text, model=gen_model, **gen_cfg)
        except Exception as e:
            content = f"[LLM 호출 실패: {e}]"

    # ── Step 6: Hydrate response ──────────────────────────────────────────
    if content and requires_masking and masking_result:
        masker = Masker()
        hydrated = masker.hydrate(content, masking_result.contract)
        content = hydrated.hydrated_text

    latency_ms = (time.time() - t0) * 1000
    action_taken = "generated" if content else "masked_and_sent"
    _log_usage("process", text, is_sensitive, len(records), effective_action, gen_model, latency_ms)

    return {
        "action_taken": action_taken,
        "content": content,
        "records": records,
        "policy_action": effective_action,
        "is_sensitive": is_sensitive,
        "requires_masking": requires_masking,
        "model_used": gen_model or None,
        "latency_ms": latency_ms,
        "masking_session_id": masking_session_id,
        "masking_records": masking_records_out,
    }


# ── Helpers ─────────────────────────────────────────────────────────────────


def _log_usage(
    event: str,
    text: str,
    is_sensitive: bool,
    record_count: int,
    policy_action: str,
    model: str | None,
    latency_ms: float,
) -> None:
    """Record a usage log entry."""
    try:
        from db.session import get_session
        from db.models import UsageLog

        input_hash = hashlib.sha256(text.encode()).hexdigest()[:16]
        session = get_session()
        try:
            entry = UsageLog(
                event=event,
                input_hash=input_hash,
                is_sensitive=is_sensitive,
                records_count=record_count,
                policy_action=policy_action,
                model=model,
                latency_ms=round(latency_ms, 1),
            )
            session.add(entry)
            session.commit()
        finally:
            session.close()
    except Exception:
        pass  # Never fail the request because of logging
