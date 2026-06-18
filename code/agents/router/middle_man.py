"""Middle-Man Agent — Stateless interactive extraction review."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from agents.extractor.schemas import ExtractionResult, ExtractionRecord
from agents.router.schemas import PipelineResult


# ── User Decision Types ─────────────────────────────────────────────────────


class UserAction(str, Enum):
    """Actions the user can take on extraction results."""
    ACCEPT = "accept"  # Accept the default action
    OVERRIDE = "override"  # Override specific records
    STRATEGY = "strategy"  # Change routing strategy
    CANCEL = "cancel"  # Cancel the request


class RoutingStrategy(str, Enum):
    """User-selectable routing strategies."""
    AUTO = "auto"  # Let the system decide (default)
    MASK_ALL = "mask_all"  # Mask all sensitive records
    BLOCK_ALL = "block_all"  # Block all (use local model)
    ALLOW_ALL = "allow_all"  # Allow all (send to external)


@dataclass
class RecordOverride:
    """User override for a specific record."""
    record_index: int
    is_essential: bool | None = None
    remove: bool = False


@dataclass
class UserDecision:
    """User's decision on extraction results."""
    action: UserAction
    strategy: RoutingStrategy = RoutingStrategy.AUTO
    overrides: list[RecordOverride] = field(default_factory=list)
    notes: str = ""


# ── Extraction Summary ──────────────────────────────────────────────────────


@dataclass
class ExtractionSummary:
    """Summary of extraction results for user presentation."""
    is_sensitive: bool
    record_count: int
    essential_count: int
    records: list[dict]
    default_action: str
    confidence_avg: float
    low_confidence_records: list[int]


# ── Middle-Man Agent ────────────────────────────────────────────────────────


class MiddleManAgent:
    """Stateless agent that presents extraction results and handles user decisions.

    Flow:
    1. User sends text
    2. Extractor detects sensitive information
    3. MiddleManAgent summarizes results
    4. User reviews and optionally overrides
    5. MiddleManAgent applies decisions and routes
    """

    def __init__(self, confidence_threshold: float = 0.7):
        self.confidence_threshold = confidence_threshold

    def summarize(self, extraction: ExtractionResult) -> ExtractionSummary:
        """Create a user-friendly summary of extraction results."""
        records = extraction.records
        essential_count = sum(1 for r in records if r.is_essential)
        confidences = [r.confidence for r in records if r.confidence > 0]
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0

        low_conf = [
            i for i, r in enumerate(records)
            if r.confidence < self.confidence_threshold
        ]

        # Determine default action
        if not extraction.sensitivity.is_sensitive:
            default_action = "allow (no sensitive info)"
        elif essential_count > 0:
            default_action = "block (has essential records)"
        else:
            default_action = "mask (non-essential only)"

        return ExtractionSummary(
            is_sensitive=extraction.sensitivity.is_sensitive,
            record_count=len(records),
            essential_count=essential_count,
            records=[
                {
                    "index": i,
                    "category": r.category,
                    "span": r.span,
                    "is_essential": r.is_essential,
                    "confidence": r.confidence,
                }
                for i, r in enumerate(records)
            ],
            default_action=default_action,
            confidence_avg=avg_confidence,
            low_confidence_records=low_conf,
        )

    def format_for_user(self, summary: ExtractionSummary) -> str:
        """Format extraction summary for user display."""
        lines = []
        lines.append("=== Privacy Router — Extraction Results ===")
        lines.append(f"Sensitive: {summary.is_sensitive}")
        lines.append(f"Records: {summary.record_count} ({summary.essential_count} essential)")
        lines.append(f"Avg Confidence: {summary.confidence_avg:.1%}")
        lines.append(f"Default Action: {summary.default_action}")
        lines.append("")

        if summary.records:
            lines.append("Detected Records:")
            for r in summary.records:
                ess = "essential" if r["is_essential"] else "non-essential"
                conf = f"{r['confidence']:.0%}"
                lines.append(f"  [{r['index']}] {r['category']}: '{r['span']}' ({ess}, {conf})")

        if summary.low_confidence_records:
            lines.append("")
            lines.append(f"⚠️  Low confidence records: {summary.low_confidence_records}")
            lines.append("   These may need manual review.")

        return "\n".join(lines)

    def apply_decision(
        self,
        extraction: ExtractionResult,
        decision: UserDecision,
    ) -> tuple[list[ExtractionRecord], str]:
        """Apply user decision to extraction results.

        Returns:
            (modified_records, routing_action)
        """
        records = list(extraction.records)

        # Apply overrides
        for override in decision.overrides:
            if override.remove:
                records[override.record_index] = None
            elif override.is_essential is not None:
                records[override.record_index].is_essential = override.is_essential

        # Remove marked records
        records = [r for r in records if r is not None]

        # Determine routing action
        if decision.strategy == RoutingStrategy.AUTO:
            if not extraction.sensitivity.is_sensitive:
                action = "route_to_external"
            elif any(r.is_essential for r in records):
                action = "route_to_local"
            else:
                action = "mask_and_send"
        elif decision.strategy == RoutingStrategy.MASK_ALL:
            action = "mask_and_send"
        elif decision.strategy == RoutingStrategy.BLOCK_ALL:
            action = "route_to_local"
        elif decision.strategy == RoutingStrategy.ALLOW_ALL:
            action = "route_to_external"
        else:
            action = "route_to_external"

        return records, action

    def process_with_decision(
        self,
        extraction: ExtractionResult,
        decision: UserDecision | None = None,
    ) -> PipelineResult:
        """Process extraction with optional user decision."""
        from agents.router import Router

        if decision is None:
            records = extraction.records
            if not extraction.sensitivity.is_sensitive:
                action = "route_to_external"
            elif any(r.is_essential for r in records):
                action = "route_to_local"
            else:
                action = "mask_and_send"
        else:
            records, action = self.apply_decision(extraction, decision)

        router = Router()
        route = router.resolve(action)

        essential_count = sum(1 for r in records if r.is_essential)
        rationale = f"essential: {essential_count}/{len(records)} records"

        from agents.judge import Judgment, MeaningfulnessAssessment
        judgment = Judgment(
            meaningful_after_masking=MeaningfulnessAssessment(
                is_meaningful_after_masking=(action not in ("route_to_local", "prompt_user")),
                rationale=rationale,
            ),
            policy_action=action,
            strategy=route.description,
            rationale=rationale,
        )

        mask_indices = (
            list(range(len(records)))
            if action in ("mask_and_send", "selective_mask")
            else []
        )

        return PipelineResult(
            sensitivity=extraction.sensitivity,
            judgment=judgment,
            route=route,
            records=records,
            mask_indices=mask_indices,
        )


# ── Convenience Functions ───────────────────────────────────────────────────

_MIDDLE_MAN: MiddleManAgent | None = None


def get_middle_man() -> MiddleManAgent:
    """Get or create the default middle-man agent."""
    global _MIDDLE_MAN
    if _MIDDLE_MAN is None:
        _MIDDLE_MAN = MiddleManAgent()
    return _MIDDLE_MAN


def summarize_extraction(extraction: ExtractionResult) -> ExtractionSummary:
    """Summarize extraction results for user presentation."""
    return get_middle_man().summarize(extraction)


def format_extraction_for_user(extraction: ExtractionResult) -> str:
    """Format extraction results for user display."""
    return get_middle_man().format_for_user(get_middle_man().summarize(extraction))


def process_with_decision(
    extraction: ExtractionResult,
    decision: UserDecision | None = None,
) -> PipelineResult:
    """Process extraction with optional user decision."""
    return get_middle_man().process_with_decision(extraction, decision)
