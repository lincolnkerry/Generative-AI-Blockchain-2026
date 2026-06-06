"""Per-Record Evaluator — selective masking decision engine.

Public API:
    - PerRecordEvaluator: evaluates each record for load-bearing status
    - evaluate: one-shot convenience function
    - PerRecordEvaluation: output model
    - RecordAssessment: per-record assessment model
"""

from .evaluator import PerRecordEvaluator, evaluate
from .schemas import PerRecordEvaluation, RecordAssessment

__all__ = [
    "PerRecordEvaluator",
    "evaluate",
    "PerRecordEvaluation",
    "RecordAssessment",
]
