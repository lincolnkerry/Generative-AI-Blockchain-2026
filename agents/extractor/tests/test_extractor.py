"""Tests for agents.extractor core functionality."""

from __future__ import annotations


from agents.extractor import ExtractionRecord
from agents.extractor.extractor import _validate_record
from agents.extractor.schemas import _ExtractedItem


class TestValidateRecord:
    def test_valid_record(self):
        text = "주민등록번호 901212-1234567 기재"
        item = _ExtractedItem(
            category="RESIDENT_REGISTRATION_NUMBER",
            span="901212-1234567",
            confidence=0.98,
            start=text.find("901212-1234567"),
            end=text.find("901212-1234567") + len("901212-1234567"),
        )
        record = _validate_record(item, text)
        assert record is not None
        assert record.category == "RESIDENT_REGISTRATION_NUMBER"

    def test_invalid_tag_format(self):
        item = _ExtractedItem(category="camelCase", span="text", confidence=0.9, start=0, end=4)
        assert _validate_record(item, "some text") is None

    def test_low_confidence(self):
        item = _ExtractedItem(category="VALID_TAG", span="text", confidence=0.3, start=0, end=4)
        assert _validate_record(item, "some text") is None

    def test_span_not_found(self):
        item = _ExtractedItem(category="VALID_TAG", span="nonexistent", confidence=0.9, start=0, end=11)
        assert _validate_record(item, "some text") is None


class TestExtractionRecord:
    def test_make_placeholder(self):
        record = ExtractionRecord(
            category="RESIDENT_REGISTRATION_NUMBER", span="901212-1234567",
            confidence=0.98, start=6, end=20,
        )
        assert record.make_placeholder(1) == "[RESIDENT_REGISTRATION_NUMBER#1]"
