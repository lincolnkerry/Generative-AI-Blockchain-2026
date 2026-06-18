"""Unit tests for agents.masker.contract_store — DB-backed masking persistence.

Requires: PostgreSQL running (docker compose up db).
"""

from __future__ import annotations


import db.models  # noqa: F401 — must import before init_db to register all models
from db.session import init_db, get_session
from agents.masker.contract_store import ContractStore
from db.models import MaskingSession, MaskingRecord

init_db()


class TestContractStoreCreateSession:
    """Test session creation."""

    def test_create_session(self):
        store = ContractStore()
        session_id = store.create_session(
            chat_id="test-chat-1",
            input_hash="abc123",
            record_count=2,
            policy_action="mask_and_send",
        )
        assert session_id is not None

        # Verify in DB
        db = get_session()
        try:
            session = db.get(MaskingSession, session_id)
            assert session is not None
            assert session.chat_id == "test-chat-1"
            assert session.record_count == 2
            assert session.is_active is True
        finally:
            db.close()


class TestContractStoreSaveAndLoad:
    """Test saving records and loading contracts."""

    def test_save_and_load(self):
        store = ContractStore()
        session_id = store.create_session(
            chat_id="test-chat-2",
            input_hash="def456",
            record_count=1,
            policy_action="mask_and_send",
        )

        records = [
            {"category": "RESIDENT_REGISTRATION_NUMBER", "span": "901212-1234567"},
        ]
        placeholder_map = {"[RESIDENT_REGISTRATION_NUMBER#a1b2c3d4]": "901212-1234567"}

        store.save_records(session_id, records, placeholder_map)

        # Load and verify
        contract = store.load_contract(session_id)
        assert contract is not None
        assert contract.count == 1
        assert "[RESIDENT_REGISTRATION_NUMBER#a1b2c3d4]" in contract.placeholder_map

    def test_span_is_encrypted_in_db(self):
        store = ContractStore()
        session_id = store.create_session(
            chat_id="test-chat-3",
            input_hash="ghi789",
            record_count=1,
            policy_action="mask_and_send",
        )

        records = [{"category": "PHONE", "span": "010-1234-5678"}]
        placeholder_map = {"[PHONE#xyz12345]": "010-1234-5678"}
        store.save_records(session_id, records, placeholder_map)

        # Check raw DB — span should NOT be plaintext
        db = get_session()
        try:
            record = db.query(MaskingRecord).filter(
                MaskingRecord.session_id == session_id
            ).first()
            assert record is not None
            assert record.span != "010-1234-5678"  # encrypted, not plaintext
        finally:
            db.close()

        # But loading should decrypt
        contract = store.load_contract(session_id)
        assert contract is not None
        assert contract.placeholder_map["[PHONE#xyz12345]"] == "010-1234-5678"


class TestContractStoreDeactivate:
    """Test session deactivation."""

    def test_deactivate_session(self):
        store = ContractStore()
        session_id = store.create_session(
            chat_id="test-chat-4",
            input_hash="jkl012",
            record_count=0,
            policy_action="allow",
        )

        store.deactivate_session(session_id)

        db = get_session()
        try:
            session = db.get(MaskingSession, session_id)
            assert session.is_active is False
        finally:
            db.close()

        # Loading deactivated session returns None
        contract = store.load_contract(session_id)
        assert contract is None
