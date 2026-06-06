"""Per-Record Evaluator — selective masking decision engine.

Evaluates each extracted record individually to determine whether
masking it would break the query's meaning (load-bearing). Produces
per-record assessments that enable selective masking.

Examples
--------
>>> evaluator = PerRecordEvaluator()
>>> result = evaluator.evaluate(
...     text="안녕, 나는 광주과학기술원에 재학 중인 김동현이야...",
...     records=[
...         {"category": "STUDENT_AFFILIATION", "span": "광주과학기술원에 재학 중인 김동현"},
...         {"category": "UNPUBLISHED_RESEARCH_CONCEPT", "span": "contextual distillation"},
...     ],
... )
>>> result.any_load_bearing
False
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from agents.llm import call_llm_structured, load_prompt, render_prompt

from .schemas import PerRecordEvaluation

# ── Constants ────────────────────────────────────────────────────────────────

_PROMPT_PATH = Path(__file__).parent / "evaluate.prompt"
"""Path to the dotpromptz prompt file."""

_DEFAULT_EVALUATOR: PerRecordEvaluator | None = None
"""Module-level singleton."""


# ── PerRecordEvaluator ───────────────────────────────────────────────────────


class PerRecordEvaluator:
    """Evaluates each extracted record for load-bearing status.

    Unlike the Judge which makes a binary decision on the WHOLE query,
    this evaluator reasons about each record individually: "if I mask
    ONLY this span, does the user's request still make sense?"

    Parameters
    ----------
    model : str or None
        Override the model identifier. If None, uses the model from
        ``evaluate.prompt``.

    Examples
    --------
    >>> evaluator = PerRecordEvaluator()
    >>> result = evaluator.evaluate(
    ...     text="안녕, 나는 광주과학기술원에 재학 중인 김동현이야...",
    ...     records=[
    ...         {"category": "STUDENT_AFFILIATION", "span": "광주과학기술원에 재학 중인 김동현"},
    ...     ],
    ... )
    >>> result.recommended_action
    'selective_mask'
    """

    def __init__(self, model: str | None = None) -> None:
        self._prompt = load_prompt(str(_PROMPT_PATH))
        self._model = model or self._prompt["model"]

    # ── Public API ──────────────────────────────────────────────────────────

    def evaluate(
        self,
        text: str,
        records: list[dict[str, Any]],
    ) -> PerRecordEvaluation:
        """Evaluate each record for load-bearing status.

        Parameters
        ----------
        text : str
            The original user text.
        records : list[dict[str, Any]]
            Extracted records from the Extractor. Each dict must have
            ``category`` and ``span`` keys.

        Returns
        -------
        PerRecordEvaluation
            Per-record assessments and recommended action.

        Examples
        --------
        >>> evaluator = PerRecordEvaluator()
        >>> result = evaluator.evaluate(
        ...     text="주민등록번호 901212-1234567을 포함한 이메일을 작성해줘.",
        ...     records=[{"category": "RESIDENT_REGISTRATION_NUMBER", "span": "901212-1234567"}],
        ... )
        >>> result.recommended_action
        'selective_mask'
        """
        slim_records = [
            {"category": r["category"], "span": r["span"]} for r in records
        ]

        rendered = render_prompt(
            self._prompt["template"],
            text=text,
            records=json.dumps(slim_records, ensure_ascii=False, indent=2),
        )
        messages = [{"role": "user", "content": rendered}]

        return call_llm_structured(
            messages,
            PerRecordEvaluation,
            model=self._model,
            max_tokens=2048,
        )


# ── Module-level convenience ─────────────────────────────────────────────────


def evaluate(text: str, records: list[dict[str, Any]]) -> PerRecordEvaluation:
    """One-shot evaluation using the shared singleton.

    Parameters
    ----------
    text : str
        Original user text.
    records : list[dict[str, Any]]
        Extracted records (category + span).

    Returns
    -------
    PerRecordEvaluation
        Per-record assessments.
    """
    global _DEFAULT_EVALUATOR
    if _DEFAULT_EVALUATOR is None:
        _DEFAULT_EVALUATOR = PerRecordEvaluator()
    return _DEFAULT_EVALUATOR.evaluate(text=text, records=records)
