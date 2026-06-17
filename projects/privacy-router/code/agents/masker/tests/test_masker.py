"""Tests for agents.masker — crypto, contract_store, masking and hydration.

Crypto and contract_store unit tests are self-contained (no external deps).
"""

import hashlib
import os

import pytest

from agents.masker import HydrationError, Masker, MaskingContract
from agents.masker.crypto import encrypt_field, decrypt_field, generate_key, _get_fernet
from agents.masker.contract_store import ContractStore


# ── crypto.py ────────────────────────────────────────────────────────────────


class TestCryptoEncryptDecrypt:
    """Fernet encrypt/decrypt round-trip and edge cases."""

    def test_round_trip(self):
        original = "901212-1234567"
        assert decrypt_field(encrypt_field(original)) == original

    def test_empty_string_passthrough(self):
        assert encrypt_field("") == ""
        assert decrypt_field("") == ""

    def test_ciphertext_differs_from_plaintext(self):
        encrypted = encrypt_field("hello")
        assert encrypted != "hello"
        assert encrypted != ""

    def test_different_inputs_different_ciphertext(self):
        """Fernet uses random IV, so same plaintext produces different ciphertext."""
        a = encrypt_field("hello")
        b = encrypt_field("hello")
        # Both decrypt to the same value, but ciphertexts differ (random IV)
        assert decrypt_field(a) == decrypt_field(b) == "hello"

    def test_korean_text(self):
        original = "홍길동 주민등록번호 901212-1234567"
        assert decrypt_field(encrypt_field(original)) == original

    def test_long_text(self):
        original = "A" * 10000
        assert decrypt_field(encrypt_field(original)) == original

    def test_special_characters(self):
        original = "!@#$%^&*()_+-=[]{}|;':\",./<>?"
        assert decrypt_field(encrypt_field(original)) == original

    def test_unicode_emojis(self):
        original = "🔒 sensitive 🔑 data 🛡️"
        assert decrypt_field(encrypt_field(original)) == original


class TestCryptoKeyHandling:
    """Test key management and _get_fernet behavior."""

    def test_generate_key_returns_base64_fernet_key(self):
        key = generate_key()
        assert isinstance(key, str)
        assert len(key) > 0
        # Should be usable as a Fernet key
        from cryptography.fernet import Fernet
        f = Fernet(key.encode())
        assert f.decrypt(f.encrypt(b"test")) == b"test"

    def test_get_fernet_uses_env_key(self, monkeypatch):
        """When MASKING_ENCRYPTION_KEY is set, _get_fernet uses it."""
        key = generate_key()
        monkeypatch.setenv("MASKING_ENCRYPTION_KEY", key)
        f = _get_fernet()
        token = f.encrypt(b"test_payload")
        assert f.decrypt(token) == b"test_payload"

    def test_get_fernet_generates_key_when_env_empty(self, monkeypatch):
        """When MASKING_ENCRYPTION_KEY is empty, a random key is generated."""
        monkeypatch.delenv("MASKING_ENCRYPTION_KEY", raising=False)
        f = _get_fernet()
        # Should be able to encrypt/decrypt
        token = f.encrypt(b"test")
        assert f.decrypt(token) == b"test"

    def test_encrypt_decrypt_consistent_with_same_env_key(self, monkeypatch):
        """Encrypt and decrypt use the same key when env var is set."""
        key = generate_key()
        monkeypatch.setenv("MASKING_ENCRYPTION_KEY", key)
        encrypted = encrypt_field("secret-data")
        monkeypatch.setenv("MASKING_ENCRYPTION_KEY", key)  # ensure same key
        assert decrypt_field(encrypted) == "secret-data"

    def test_env_key_with_whitespace_stripped(self, monkeypatch):
        """Key from env has whitespace stripped."""
        key = generate_key()
        monkeypatch.setenv("MASKING_ENCRYPTION_KEY", f"  {key}  ")
        encrypted = encrypt_field("test")
        assert decrypt_field(encrypted) == "test"


# ── contract_store.py ────────────────────────────────────────────────────────


class TestContractStoreUidFor:
    """Test ContractStore._uid_for — pure deterministic UID generation."""

    def test_uid_for_valid_record(self):
        store = ContractStore()
        record = {"category": "RESIDENT_REGISTRATION_NUMBER", "span": "901212-1234567"}
        uid = store._uid_for(record)
        assert uid.startswith("RESIDENT_REGISTRATION_NUMBER_")
        expected_hash = hashlib.sha256("901212-1234567".encode()).hexdigest()[:8]
        assert uid == f"RESIDENT_REGISTRATION_NUMBER_{expected_hash}"

    def test_uid_for_none_returns_unknown(self):
        store = ContractStore()
        assert store._uid_for(None) == "unknown"

    def test_uid_for_deterministic(self):
        store = ContractStore()
        record = {"category": "PHONE", "span": "010-1234-5678"}
        uid1 = store._uid_for(record)
        uid2 = store._uid_for(record)
        assert uid1 == uid2

    def test_uid_for_different_records_different_uids(self):
        store = ContractStore()
        r1 = {"category": "PHONE", "span": "010-1111-1111"}
        r2 = {"category": "PHONE", "span": "010-2222-2222"}
        assert store._uid_for(r1) != store._uid_for(r2)

    def test_uid_for_different_categories_different_prefixes(self):
        store = ContractStore()
        r1 = {"category": "PHONE", "span": "010-1234-5678"}
        r2 = {"category": "EMAIL", "span": "010-1234-5678"}
        assert store._uid_for(r1) != store._uid_for(r2)

    def test_uid_for_missing_category(self):
        store = ContractStore()
        record = {"span": "value"}
        uid = store._uid_for(record)
        assert uid.startswith("UNKNOWN_")

    def test_uid_for_missing_span(self):
        store = ContractStore()
        record = {"category": "TEST"}
        uid = store._uid_for(record)
        hash_prefix = hashlib.sha256("".encode()).hexdigest()[:8]
        assert uid == f"TEST_{hash_prefix}"

    def test_uid_for_empty_record(self):
        """Empty dict is falsy, so _uid_for returns 'unknown' (same as None)."""
        store = ContractStore()
        assert store._uid_for({}) == "unknown"

    def test_ttl_default(self):
        store = ContractStore()
        assert store._ttl.total_seconds() == 24 * 3600

    def test_ttl_custom(self):
        store = ContractStore(ttl_hours=48)
        assert store._ttl.total_seconds() == 48 * 3600


# ── MaskingContract ──────────────────────────────────────────────────────────


class TestMaskingContract:
    def test_validate_response_all_resolved(self):
        contract = MaskingContract(
            placeholder_map={"[RRN#1]": "901212-1234567", "[PHONE#1]": "010-1234-5678"},
            count=2,
        )
        unresolved = contract.validate_response("번호 [RRN#1]과 [PHONE#1]")
        assert unresolved == []

    def test_validate_response_has_unresolved(self):
        contract = MaskingContract(
            placeholder_map={"[RRN#1]": "901212-1234567"},
            count=1,
        )
        unresolved = contract.validate_response("번호 [RRN#1]과 [UNKNOWN_TAG#1]")
        assert "[UNKNOWN_TAG#1]" in unresolved

    def test_validate_response_no_placeholders(self):
        contract = MaskingContract(placeholder_map={"[RRN#1]": "val"}, count=1)
        unresolved = contract.validate_response("no placeholders here")
        assert unresolved == []

    def test_validate_response_empty_text(self):
        contract = MaskingContract(placeholder_map={"[RRN#1]": "val"}, count=1)
        unresolved = contract.validate_response("")
        assert unresolved == []


# ── Masker ───────────────────────────────────────────────────────────────────


class TestMasker:
    def test_mask_single_span(self):
        masker = Masker()
        text = "주민등록번호 901212-1234567 기재"
        records = [
            {"category": "RESIDENT_REGISTRATION_NUMBER", "span": "901212-1234567", "start": 7, "end": 21},
        ]
        result = masker.mask(text, records)
        assert "[RESIDENT_REGISTRATION_NUMBER#" in result.masked_text
        assert "901212-1234567" not in result.masked_text
        assert result.contract.count == 1

    def test_mask_multiple_spans(self):
        masker = Masker()
        text = "주민번호 901212-1234567 전화 010-9876-5432"
        records = [
            {"category": "RESIDENT_REGISTRATION_NUMBER", "span": "901212-1234567", "start": 5, "end": 19},
            {"category": "MOBILE_PHONE_NUMBER", "span": "010-9876-5432", "start": 23, "end": 36},
        ]
        result = masker.mask(text, records)
        assert "[RESIDENT_REGISTRATION_NUMBER#" in result.masked_text
        assert "[MOBILE_PHONE_NUMBER#" in result.masked_text
        assert "901212-1234567" not in result.masked_text
        assert "010-9876-5432" not in result.masked_text

    def test_mask_span_not_found_skips(self):
        masker = Masker()
        result = masker.mask("hello world", [{"category": "TEST", "span": "nonexistent", "start": 0, "end": 11}])
        assert result.masked_text == "hello world"  # span not found → skipped
        assert result.contract.count == 0

    def test_hydrate_restores(self):
        masker = Masker()
        contract = MaskingContract(
            placeholder_map={"[RRN#1]": "901212-1234567", "[PHONE#1]": "010-1234-5678"},
            count=2,
        )
        result = masker.hydrate("번호 [RRN#1]과 [PHONE#1]입니다.", contract)
        assert result.hydrated_text == "번호 901212-1234567과 010-1234-5678입니다."
        assert result.placeholders_restored == 2

    def test_hydrate_unresolved_fails(self):
        masker = Masker()
        contract = MaskingContract(placeholder_map={"[RRN#1]": "901212-1234567"}, count=1)
        with pytest.raises(HydrationError):
            masker.hydrate("번호 [RRN#1]과 [UNKNOWN#1]입니다.", contract)

    def test_full_roundtrip(self):
        masker = Masker()
        original = "주민번호 901212-1234567 전화 010-9876-5432"
        records = [
            {"category": "RESIDENT_REGISTRATION_NUMBER", "span": "901212-1234567", "start": 5, "end": 19},
            {"category": "MOBILE_PHONE_NUMBER", "span": "010-9876-5432", "start": 23, "end": 36},
        ]
        result = masker.mask(original, records)
        llm_response = f"처리 완료: {result.masked_text}"
        hydrated = masker.hydrate(llm_response, result.contract)
        assert "901212-1234567" in hydrated.hydrated_text
        assert "[RESIDENT_REGISTRATION_NUMBER#1]" not in hydrated.hydrated_text

    def test_selective_mask(self):
        masker = Masker()
        text = "주민번호 901212-1234567 전화 010-9876-5432"
        records = [
            {"category": "RESIDENT_REGISTRATION_NUMBER", "span": "901212-1234567", "start": 5, "end": 19},
            {"category": "MOBILE_PHONE_NUMBER", "span": "010-9876-5432", "start": 23, "end": 36},
        ]
        # Only mask the first record (index 0)
        result = masker.selective_mask(text, records, [0])
        assert "[RESIDENT_REGISTRATION_NUMBER#" in result.masked_text
        assert "010-9876-5432" in result.masked_text  # second record NOT masked
        assert result.contract.count == 1

    def test_selective_mask_empty_indices(self):
        masker = Masker()
        text = "hello world"
        records = [{"category": "TEST", "span": "world", "start": 6, "end": 11}]
        result = masker.selective_mask(text, records, [])
        assert result.masked_text == "hello world"
        assert result.contract.count == 0

    def test_hydrate_no_placeholders(self):
        masker = Masker()
        contract = MaskingContract(placeholder_map={}, count=0)
        result = masker.hydrate("plain text", contract)
        assert result.hydrated_text == "plain text"
        assert result.placeholders_restored == 0

    def test_hydration_error_contains_unresolved(self):
        masker = Masker()
        contract = MaskingContract(placeholder_map={}, count=0)
        with pytest.raises(HydrationError) as exc_info:
            masker.hydrate("[UNKNOWN#1]", contract)
        assert "[UNKNOWN#1]" in exc_info.value.unresolved