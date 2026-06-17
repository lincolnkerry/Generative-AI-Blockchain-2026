"""SQLModel-backed cache for extraction results and masking contracts."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime

from sqlmodel import Session, select

from db.models import ExtractionCache
from db.session import engine


def _text_hash(text: str) -> str:
    """MD5 hash of text (UTF-8 encoded)."""
    return hashlib.md5(text.encode("utf-8")).hexdigest()


class SQLiteKVCache:
    """Persistent cache using SQLModel ORM.

    Single table keyed by chat_id:
        - extraction: cached extraction result (updated per request)
        - contract: masking contract (persisted across follow-up requests)
    """

    # ── Extraction ───────────────────────────────────────────────────────

    def get_extraction(self, chat_id: str) -> dict | None:
        """Get cached extraction by chat_id."""
        with Session(engine) as session:
            entry = session.get(ExtractionCache, chat_id)
            if entry and entry.extraction:
                return json.loads(entry.extraction)
        return None

    def put_extraction(self, chat_id: str, text: str, extraction: dict) -> None:
        """Cache extraction result. Inserts or updates."""
        text_hash = _text_hash(text)
        with Session(engine) as session:
            entry = session.get(ExtractionCache, chat_id)
            if entry:
                entry.text_hash = text_hash
                entry.extraction = json.dumps(extraction, ensure_ascii=False)
                entry.updated_at = datetime.utcnow()
            else:
                entry = ExtractionCache(
                    chat_id=chat_id,
                    text_hash=text_hash,
                    extraction=json.dumps(extraction, ensure_ascii=False),
                )
                session.add(entry)
            session.commit()

    # ── Contract ─────────────────────────────────────────────────────────

    def get_contract(self, chat_id: str) -> dict | None:
        """Get masking contract by chat_id."""
        with Session(engine) as session:
            entry = session.get(ExtractionCache, chat_id)
            if entry and entry.contract:
                return json.loads(entry.contract)
        return None

    def put_contract(self, chat_id: str, contract: dict) -> None:
        """Store or update masking contract for chat_id."""
        with Session(engine) as session:
            entry = session.get(ExtractionCache, chat_id)
            if entry:
                entry.contract = json.dumps(contract, ensure_ascii=False)
                entry.updated_at = datetime.utcnow()
            else:
                entry = ExtractionCache(
                    chat_id=chat_id,
                    text_hash="",
                    contract=json.dumps(contract, ensure_ascii=False),
                )
                session.add(entry)
            session.commit()

    # ── Combined ─────────────────────────────────────────────────────────

    def get(self, chat_id: str) -> dict | None:
        """Get full cache entry (extraction + contract) by chat_id."""
        with Session(engine) as session:
            entry = session.get(ExtractionCache, chat_id)
            if entry:
                return {
                    "extraction": json.loads(entry.extraction) if entry.extraction else None,
                    "contract": json.loads(entry.contract) if entry.contract else None,
                }
        return None

    def put(self, chat_id: str, text: str, extraction: dict, contract: dict | None = None) -> None:
        """Store extraction and optional contract for chat_id."""
        text_hash = _text_hash(text)
        with Session(engine) as session:
            entry = session.get(ExtractionCache, chat_id)
            if entry:
                entry.text_hash = text_hash
                entry.extraction = json.dumps(extraction, ensure_ascii=False)
                if contract is not None:
                    entry.contract = json.dumps(contract, ensure_ascii=False)
                entry.updated_at = datetime.utcnow()
            else:
                entry = ExtractionCache(
                    chat_id=chat_id,
                    text_hash=text_hash,
                    extraction=json.dumps(extraction, ensure_ascii=False),
                    contract=json.dumps(contract, ensure_ascii=False) if contract else None,
                )
                session.add(entry)
            session.commit()

    # ── Maintenance ──────────────────────────────────────────────────────

    def delete(self, chat_id: str) -> bool:
        """Remove cache entry. Returns True if found."""
        with Session(engine) as session:
            entry = session.get(ExtractionCache, chat_id)
            if entry:
                session.delete(entry)
                session.commit()
                return True
        return False

    def clear(self) -> int:
        """Clear all entries. Returns count removed."""
        with Session(engine) as session:
            entries = session.exec(select(ExtractionCache)).all()
            count = len(entries)
            for entry in entries:
                session.delete(entry)
            session.commit()
            return count

    def cleanup(self, max_age_hours: int = 24) -> int:
        """Remove entries older than max_age_hours. Returns count removed."""
        from datetime import timedelta
        cutoff = datetime.utcnow() - timedelta(hours=max_age_hours)
        with Session(engine) as session:
            entries = session.exec(
                select(ExtractionCache).where(ExtractionCache.updated_at < cutoff)
            ).all()
            count = len(entries)
            for entry in entries:
                session.delete(entry)
            session.commit()
            return count

    @property
    def stats(self) -> dict:
        with Session(engine) as session:
            entries = session.exec(select(ExtractionCache)).all()
            total = len(entries)
            with_extraction = sum(1 for e in entries if e.extraction)
            with_contract = sum(1 for e in entries if e.contract)
            return {
                "total": total,
                "with_extraction": with_extraction,
                "with_contract": with_contract,
            }


# Singleton
_CACHE: SQLiteKVCache | None = None


def get_cache() -> SQLiteKVCache:
    """Get or create the default cache."""
    global _CACHE
    if _CACHE is None:
        _CACHE = SQLiteKVCache()
    return _CACHE
