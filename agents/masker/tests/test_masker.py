"""Tests for agents.masker."""

import pytest

from agents.masker import HydrationError, Masker, MaskingContract


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


class TestMasker:
    def test_mask_single_span(self):
        masker = Masker()
        text = "주민등록번호 901212-1234567 기재"
        records = [
            {"category": "RESIDENT_REGISTRATION_NUMBER", "span": "901212-1234567", "start": 7, "end": 21},
        ]
        result = masker.mask(text, records)
        assert result.masked_text == "주민등록번호 [RESIDENT_REGISTRATION_NUMBER#1] 기재"
        assert result.contract.count == 1

    def test_mask_multiple_spans(self):
        masker = Masker()
        text = "주민번호 901212-1234567 전화 010-9876-5432"
        records = [
            {"category": "RESIDENT_REGISTRATION_NUMBER", "span": "901212-1234567", "start": 5, "end": 19},
            {"category": "MOBILE_PHONE_NUMBER", "span": "010-9876-5432", "start": 23, "end": 36},
        ]
        result = masker.mask(text, records)
        assert "[RESIDENT_REGISTRATION_NUMBER#1]" in result.masked_text
        assert "[MOBILE_PHONE_NUMBER#1]" in result.masked_text
        assert "901212-1234567" not in result.masked_text

    def test_mask_span_not_found_raises(self):
        masker = Masker()
        with pytest.raises(ValueError):
            masker.mask("hello world", [{"category": "TEST", "span": "nonexistent", "start": 0, "end": 11}])

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
