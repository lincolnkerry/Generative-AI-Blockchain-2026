"""Two-Phase Extractor — ensemble extraction with second-pass critic.

Phase 1: Standard extraction with the primary prompt.
Phase 2: Critic pass that finds what Phase 1 missed.

This eliminates the single-point-of-failure problem: even when
the primary Extractor misses contextual secrets, the critic
catches them before they're permanently lost.
"""

from __future__ import annotations

import json
from pathlib import Path

from agents.extractor.extractor import Extractor
from agents.extractor.schemas import ExtractionRecord, ExtractionResult, Sensitivity
from agents.llm import call_llm_structured, load_prompt, render_prompt

from .schemas import CriticOutput

_CRITIC_PROMPT_PATH = Path(__file__).parent / "critic.prompt"


class TwoPhaseExtractor:
    """Extractor with a second-pass critic to catch missed secrets.

    Phase 1 runs the standard Extractor. Phase 2 feeds the
    original text + already-tagged spans to a critic that asks:
    "Is there any sensitive information still present that was
    not captured?"

    Parameters
    ----------
    model : str or None
        Override the model identifier for both phases.

    Examples
    --------
    >>> ext = TwoPhaseExtractor()
    >>> result = ext.extract("주민등록번호 901212-1234567")
    >>> len(result.records) >= 1
    True
    """

    def __init__(self, model: str | None = None) -> None:
        self._extractor = Extractor(model=model)
        prompt_dict = load_prompt(str(_CRITIC_PROMPT_PATH))
        self._critic_model = model or prompt_dict["model"]
        self._critic_template = prompt_dict["template"]

    def extract(self, text: str) -> ExtractionResult:
        """Run two-phase extraction.

        Parameters
        ----------
        text : str
            Raw input text.

        Returns
        -------
        ExtractionResult
            Merged records from both phases.
        """
        # Phase 1: Standard extraction
        phase1 = self._extractor.extract(text)

        if not text or not text.strip():
            return phase1

        # Phase 2: Critic — find what Phase 1 missed
        tagged_spans = [r.span for r in phase1.records]
        try:
            rendered = render_prompt(
                self._critic_template,
                text=text,
                tagged_spans=json.dumps(tagged_spans, ensure_ascii=False),
            )
            messages = [{"role": "user", "content": rendered}]
            critic_out = call_llm_structured(
                messages, CriticOutput, model=self._critic_model, max_tokens=2048
            )
        except Exception:
            # Critic failed — return Phase 1 results as-is
            return phase1

        if not critic_out.found_missed:
            return phase1

        # Merge: Phase 1 records + Phase 2 missed records
        # Merge: Phase 1 records + Phase 2 missed records
        all_records = list(phase1.records)
        existing_spans = {r.span for r in all_records}

        for item in critic_out.missed_records:
            if item.span in existing_spans:
                continue  # duplicate
            found = text.find(item.span)
            if found == -1:
                continue  # hallucinated span
            all_records.append(
                ExtractionRecord(
                    category=item.category,
                    span=item.span,
                    confidence=item.confidence,
                    start=found,
                    end=found + len(item.span),
                    detection_type=item.detection_type,
                    reasoning=item.reasoning,
                )
            )
            existing_spans.add(item.span)

        return ExtractionResult(
            sensitivity=Sensitivity(
                is_sensitive=len(all_records) > 0 or phase1.sensitivity.is_sensitive,
                rationale=phase1.sensitivity.rationale,
            ),
            records=all_records,
        )
