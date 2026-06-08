"""ContractStore — Persistence for masking contracts.

Stores masking sessions and records in PostgreSQL. Each masking
operation creates a session with a unique ID. Records store
placeholder-to-hash mappings (original values are NEVER stored).

Usage:
    store = ContractStore()
    session_id = store.create_session(chat_id="user-123", input_hash="abc...", record_count=2)
    store.save_records(session_id, records)
    contract = store.load_contract(session_id)
"""

from __future__ import annotations

import hashlib
import uuid
from datetime import datetime, timedelta
from typing import Any

from .schemas import MaskingContract


class ContractStore:
    """Persists masking contracts to PostgreSQL.

    Each masking operation creates a session. Records store
    placeholder-to-hash mappings. Original values are NEVER stored.
    """

    def __init__(self, ttl_hours: int = 24) -> None:
        self._ttl = timedelta(hours=ttl_hours)

    def create_session(
        self,
        chat_id: str | None,
        input_hash: str,
        record_count: int,
        policy_action: str,
    ) -> str:
        """Create a new masking session. Returns session_id."""
        from db.session import get_session
        from db.models import MaskingSession

        session_id = str(uuid.uuid4())
        db = get_session()
        try:
            session = MaskingSession(
                id=session_id,
                chat_id=chat_id,
                input_hash=input_hash,
                record_count=record_count,
                policy_action=policy_action,
                is_active=True,
                expires_at=datetime.utcnow() + self._ttl,
            )
            db.add(session)
            db.commit()
        finally:
            db.close()
        return session_id

    def save_records(
        self,
        session_id: str,
        records: list[dict[str, Any]],
        placeholder_map: dict[str, str],
    ) -> None:
        """Save masking records for a session.

        Args:
            session_id: The masking session ID.
            records: Extraction records from the pipeline.
            placeholder_map: Mapping of placeholders to original values.
        """
        from db.session import get_session
        from db.models import MaskingRecord
        from .crypto import encrypt_field

        db = get_session()
        try:
            for placeholder, original_value in placeholder_map.items():
                # Find the matching record
                matching = next(
                    (r for r in records if f"[{r['category']}#{self._uid_for(r)}]" == placeholder),
                    None,
                )
                value_hash = hashlib.sha256(original_value.encode()).hexdigest()
                uid = self._uid_for(matching) if matching else value_hash[:8]

                record = MaskingRecord(
                    session_id=session_id,
                    uid=uid,
                    category=matching["category"] if matching else "UNKNOWN",
                    placeholder=placeholder,
                    value_hash=value_hash,
                    span=encrypt_field(original_value),
                    confidence=matching.get("confidence", 0.0) if matching else 0.0,
                    is_load_bearing=matching.get("is_load_bearing", False) if matching else False,
                )
                db.add(record)
            db.commit()
        finally:
            db.close()

    def load_contract(self, session_id: str) -> MaskingContract | None:
        """Load a masking contract from the database.

        Returns None if session not found or expired.
        """
        from db.session import get_session
        from db.models import MaskingRecord, MaskingSession
        from .crypto import decrypt_field

        db = get_session()
        try:
            session = db.get(MaskingSession, session_id)
            if not session or not session.is_active:
                return None
            if session.expires_at and session.expires_at < datetime.utcnow():
                return None

            records = db.query(MaskingRecord).filter(
                MaskingRecord.session_id == session_id
            ).all()

            if not records:
                return None
            placeholder_map = {r.placeholder: decrypt_field(r.span) for r in records}
            return MaskingContract(
                placeholder_map=placeholder_map,
                count=len(placeholder_map),
            )
        finally:
            db.close()

    def deactivate_session(self, session_id: str) -> None:
        """Mark a session as inactive."""
        from db.session import get_session
        from db.models import MaskingSession

        db = get_session()
        try:
            session = db.get(MaskingSession, session_id)
            if session:
                session.is_active = False
                db.commit()
        finally:
            db.close()

    def _uid_for(self, record: dict[str, Any] | None) -> str:
        """Generate a deterministic UID for a record."""
        if not record:
            return "unknown"
        category = record.get("category", "UNKNOWN")
        span = record.get("span", "")
        hash_prefix = hashlib.sha256(span.encode()).hexdigest()[:8]
        return f"{category}_{hash_prefix}"
