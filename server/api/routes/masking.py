"""Masking session and hydration API endpoints.

Provides REST API for:
- GET /api/v1/masking/{session_id} — retrieve masking session details
- POST /api/v1/masking/{session_id}/hydrate — hydrate content using stored contract
"""

from __future__ import annotations

from fastapi import HTTPException

from server.api.main import app


@app.get("/api/v1/masking/{session_id}")
async def get_masking_session(session_id: str) -> dict:
    """Retrieve masking session details.

    Returns session metadata and per-record masking details
    (category, placeholder, confidence, is_load_bearing).
    Original values are NEVER returned — only metadata.
    """
    from db.session import get_session
    from db.models import MaskingSession, MaskingRecord

    db = get_session()
    try:
        session = db.get(MaskingSession, session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Masking session not found")

        records = db.query(MaskingRecord).filter(
            MaskingRecord.session_id == session_id
        ).all()

        return {
            "session_id": session.id,
            "chat_id": session.chat_id,
            "input_hash": session.input_hash,
            "record_count": session.record_count,
            "policy_action": session.policy_action,
            "is_active": session.is_active,
            "created_at": session.created_at.isoformat() if session.created_at else None,
            "expires_at": session.expires_at.isoformat() if session.expires_at else None,
            "records": [
                {
                    "uid": r.uid,
                    "category": r.category,
                    "placeholder": r.placeholder,
                    "confidence": r.confidence,
                    "is_load_bearing": r.is_load_bearing,
                }
                for r in records
            ],
        }
    finally:
        db.close()


@app.post("/api/v1/masking/{session_id}/hydrate")
async def hydrate_content(session_id: str, body: dict) -> dict:
    """Hydrate content using a stored masking contract.

    Args:
        body: {"content": "text with [CATEGORY#uid] placeholders"}

    Returns:
        {"hydrated": "text with original values restored"}
    """
    from agents.masker import ContractStore, Masker

    content = body.get("content", "")
    if not content:
        raise HTTPException(status_code=400, detail="content field required")

    store = ContractStore()
    contract = store.load_contract(session_id)
    if not contract:
        raise HTTPException(status_code=404, detail="Masking session not found or expired")

    masker = Masker()
    result = masker.hydrate(content, contract)

    return {
        "hydrated": result.hydrated_text,
        "session_id": session_id,
        "records_restored": result.count,
    }
