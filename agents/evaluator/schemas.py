"""Schemas for the Per-Record Evaluator.

Evaluates each extracted record individually: does masking THIS record
break the query's meaning? Produces per-record load-bearing assessments
that enable selective masking decisions.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class RecordAssessment(BaseModel):
    """Per-record load-bearing evaluation.

    Attributes
    ----------
    span : str
        The original sensitive span text.
    category : str
        SCREAMING_SNAKE_CASE category from the Extractor.
    is_load_bearing : bool
        True if masking this record would break the query's meaning.
    rationale : str
        Korean explanation of the assessment.

    Examples
    --------
    >>> ra = RecordAssessment(
    ...     span="광주과학기술원에 재학 중인 김동현",
    ...     category="STUDENT_AFFILIATION",
    ...     is_load_bearing=False,
    ...     rationale="이름과 소속을 몰라도 청킹 방법 조언은 가능하다",
    ... )
    """

    span: str = Field(
        ...,
        description="The original sensitive span text.",
        examples=["광주과학기술원에 재학 중인 김동현"],
    )
    category: str = Field(
        ...,
        description="SCREAMING_SNAKE_CASE category.",
        examples=["STUDENT_AFFILIATION"],
    )
    is_load_bearing: bool = Field(
        ...,
        description="True if masking this record breaks query meaning.",
        examples=[False, True],
    )
    rationale: str = Field(
        ...,
        description="Korean explanation of why this record is or is not load-bearing.",
        examples=["이름과 소속을 몰라도 청킹 방법 조언은 가능하다"],
    )


class PerRecordEvaluation(BaseModel):
    """Full output of the per-record evaluation phase.

    Attributes
    ----------
    record_assessments : list[RecordAssessment]
        Per-record load-bearing assessments.
    any_load_bearing : bool
        True if any record is load-bearing.
    recommended_action : str
        ``"selective_mask"``, ``"process_locally"``, or ``"allow"``.
    overall_rationale : str
        Korean explanation of the overall decision.

    Examples
    --------
    >>> ra = RecordAssessment(
    ...     span="contextual distillation", category="UNPUBLISHED_RESEARCH_CONCEPT",
    ...     is_load_bearing=False, rationale="연구 주제명은 몰라도 방법론 조언 가능",
    ... )
    >>> pe = PerRecordEvaluation(
    ...     record_assessments=[ra],
    ...     any_load_bearing=False,
    ...     recommended_action="selective_mask",
    ...     overall_rationale="모든 레코드가 load-bearing이 아니므로 마스킹 후 전송 가능",
    ... )
    """

    record_assessments: list[RecordAssessment] = Field(
        default_factory=list,
        description="Per-record load-bearing assessments.",
    )
    any_load_bearing: bool = Field(
        ...,
        description="True if any record is load-bearing.",
        examples=[False, True],
    )
    recommended_action: str = Field(
        ...,
        description="Recommended action: 'selective_mask', 'process_locally', or 'allow'.",
        examples=["selective_mask", "process_locally", "allow"],
    )
    overall_rationale: str = Field(
        ...,
        description="Korean explanation of the overall decision.",
        examples=["레코드 3이 load-bearing이므로 외부 전송 불가"],
    )
