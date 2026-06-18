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


from unittest.mock import MagicMock, patch

from agents.extractor.schemas import ExtractionResult, Sensitivity, CriticOutput, _CriticItem
from agents.extractor.two_phase import TwoPhaseExtractor


def _make_phase1_result(
    records=None, is_sensitive=True, rationale="탐지됨"
) -> ExtractionResult:
    """Build a minimal Phase-1 ExtractionResult."""
    return ExtractionResult(
        sensitivity=Sensitivity(is_sensitive=is_sensitive, rationale=rationale),
        records=records or [],
    )


_PHASE1_RECORD = ExtractionRecord(
    category="RESIDENT_REGISTRATION_NUMBER",
    span="901212-1234567",
    confidence=0.98,
    start=6,
    end=20,
)

_CRITIC_PROMPT_DICT = {
    "model": "openrouter/mistralai/ministral-3b-2512",
    "template": "test template {{text}} {{tagged_spans}}",
}


class TestTwoPhaseExtractorInit:
    """TwoPhaseExtractor construction."""

    @patch("agents.extractor.two_phase.load_prompt", return_value=_CRITIC_PROMPT_DICT)
    @patch("agents.extractor.two_phase.Extractor")
    def test_default_model(self, mock_extractor_cls, mock_load_prompt):
        ext = TwoPhaseExtractor()
        mock_extractor_cls.assert_called_once_with(model=None)
        assert ext._critic_model == "openrouter/mistralai/ministral-3b-2512"
        assert ext._critic_template == "test template {{text}} {{tagged_spans}}"

    @patch("agents.extractor.two_phase.load_prompt", return_value=_CRITIC_PROMPT_DICT)
    @patch("agents.extractor.two_phase.Extractor")
    def test_custom_model(self, mock_extractor_cls, mock_load_prompt):
        ext = TwoPhaseExtractor(model="custom/model")
        mock_extractor_cls.assert_called_once_with(model="custom/model")
        assert ext._critic_model == "custom/model"


class TestTwoPhaseExtractorExtract:
    """TwoPhaseExtractor.extract() behaviour."""

    @staticmethod
    def _make_ext(phase1_result):
        """Build a TwoPhaseExtractor whose Phase-1 returns *phase1_result*."""
        mock_extractor = MagicMock()
        mock_extractor.extract.return_value = phase1_result
        with (
            patch("agents.extractor.two_phase.load_prompt", return_value=_CRITIC_PROMPT_DICT),
            patch("agents.extractor.two_phase.Extractor", return_value=mock_extractor),
        ):
            return TwoPhaseExtractor()

    def test_empty_text_returns_phase1(self):
        """Empty / whitespace-only text bypasses Phase 2."""
        phase1 = _make_phase1_result(records=[], is_sensitive=False, rationale="빈 텍스트입니다.")
        ext = self._make_ext(phase1)
        result = ext.extract("")
        assert result is phase1

    def test_blank_text_returns_phase1(self):
        phase1 = _make_phase1_result(records=[], is_sensitive=False, rationale="빈 텍스트입니다.")
        ext = self._make_ext(phase1)
        result = ext.extract("   \n  ")
        assert result is phase1

    def test_critic_exception_returns_phase1(self):
        """When the critic LLM call raises, fall back to Phase 1."""
        phase1 = _make_phase1_result(records=[_PHASE1_RECORD])
        ext = self._make_ext(phase1)
        with (
            patch("agents.extractor.two_phase.render_prompt", return_value="rendered"),
            patch("agents.extractor.two_phase.call_llm_structured", side_effect=RuntimeError("LLM down")),
        ):
            result = ext.extract("주민등록번호 901212-1234567 기재")
        assert result is phase1
        assert len(result.records) == 1

    def test_critic_finds_nothing(self):
        """found_missed=False → return Phase 1 as-is."""
        phase1 = _make_phase1_result(records=[_PHASE1_RECORD])
        ext = self._make_ext(phase1)
        with (
            patch("agents.extractor.two_phase.render_prompt", return_value="rendered"),
            patch("agents.extractor.two_phase.call_llm_structured", return_value=CriticOutput(found_missed=False, missed_records=[])),
        ):
            result = ext.extract("주민등록번호 901212-1234567 기재")
        assert result is phase1
        assert len(result.records) == 1

    def test_critic_finds_new_record(self):
        """Critic finds a span Phase 1 missed → merged result."""
        text = "주민등록번호 901212-1234567 기재, 연락처 010-1234-5678"
        phase1 = _make_phase1_result(records=[_PHASE1_RECORD])
        ext = self._make_ext(phase1)
        critic = CriticOutput(
            found_missed=True,
            missed_records=[
                _CriticItem(
                    category="MOBILE_PHONE_NUMBER",
                    span="010-1234-5678",
                    confidence=0.95,
                    detection_type="pattern",
                    reasoning="핸드폰 번호",
                ),
            ],
        )
        with (
            patch("agents.extractor.two_phase.render_prompt", return_value="rendered"),
            patch("agents.extractor.two_phase.call_llm_structured", return_value=critic),
        ):
            result = ext.extract(text)
        assert len(result.records) == 2
        categories = {r.category for r in result.records}
        assert "RESIDENT_REGISTRATION_NUMBER" in categories
        assert "MOBILE_PHONE_NUMBER" in categories
        assert result.sensitivity.is_sensitive is True

    def test_critic_duplicate_span_skipped(self):
        """Critic reports a span already in Phase 1 → deduplicated."""
        text = "주민등록번호 901212-1234567 기재"
        phase1 = _make_phase1_result(records=[_PHASE1_RECORD])
        ext = self._make_ext(phase1)
        critic = CriticOutput(
            found_missed=True,
            missed_records=[
                _CriticItem(
                    category="RESIDENT_REGISTRATION_NUMBER",
                    span="901212-1234567",
                    confidence=0.99,
                ),
            ],
        )
        with (
            patch("agents.extractor.two_phase.render_prompt", return_value="rendered"),
            patch("agents.extractor.two_phase.call_llm_structured", return_value=critic),
        ):
            result = ext.extract(text)
        assert len(result.records) == 1

    def test_critic_hallucinated_span_skipped(self):
        """Critic reports a span not in the original text → skipped."""
        text = "주민등록번호 901212-1234567 기재"
        phase1 = _make_phase1_result(records=[_PHASE1_RECORD])
        ext = self._make_ext(phase1)
        critic = CriticOutput(
            found_missed=True,
            missed_records=[
                _CriticItem(
                    category="EMAIL_ADDRESS",
                    span="ghost@example.com",
                    confidence=0.9,
                ),
            ],
        )
        with (
            patch("agents.extractor.two_phase.render_prompt", return_value="rendered"),
            patch("agents.extractor.two_phase.call_llm_structured", return_value=critic),
        ):
            result = ext.extract(text)
        assert len(result.records) == 1
        assert result.records[0].category == "RESIDENT_REGISTRATION_NUMBER"

    def test_critic_adds_to_empty_phase1(self):
        """Phase 1 found nothing, critic finds something."""
        text = "이메일 test@example.com 입니다"
        phase1 = _make_phase1_result(records=[], is_sensitive=False, rationale="민감 정보 없음")
        ext = self._make_ext(phase1)
        critic = CriticOutput(
            found_missed=True,
            missed_records=[
                _CriticItem(
                    category="EMAIL_ADDRESS",
                    span="test@example.com",
                    confidence=0.92,
                    detection_type="pattern",
                ),
            ],
        )
        with (
            patch("agents.extractor.two_phase.render_prompt", return_value="rendered"),
            patch("agents.extractor.two_phase.call_llm_structured", return_value=critic),
        ):
            result = ext.extract(text)
        assert len(result.records) == 1
        assert result.records[0].category == "EMAIL_ADDRESS"
        assert result.sensitivity.is_sensitive is True

    def test_critic_multiple_missed_records(self):
        """Critic returns multiple new spans — all merged."""
        text = "김철수 010-1234-5678, email test@co.kr"
        phase1 = _make_phase1_result(records=[], is_sensitive=False, rationale="없음")
        ext = self._make_ext(phase1)
        critic = CriticOutput(
            found_missed=True,
            missed_records=[
                _CriticItem(category="MOBILE_PHONE_NUMBER", span="010-1234-5678", confidence=0.95),
                _CriticItem(category="EMAIL_ADDRESS", span="test@co.kr", confidence=0.9),
            ],
        )
        with (
            patch("agents.extractor.two_phase.render_prompt", return_value="rendered"),
            patch("agents.extractor.two_phase.call_llm_structured", return_value=critic),
        ):
            result = ext.extract(text)
        assert len(result.records) == 2
        spans = {r.span for r in result.records}
        assert "010-1234-5678" in spans
        assert "test@co.kr" in spans