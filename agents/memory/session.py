"""Sliding-window session memory for Privacy Router demo.

Stores recent interactions per session so agents can access prior
context when making masking/per-record decisions.

For demo: in-memory dict with deque (sliding window).
Production: swap for Redis or DB-backed store.
"""

from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass, field
from typing import Any


@dataclass
class SessionEntry:
    """One interaction stored in the sliding window.

    Attributes
    ----------
    text : str
        Original user text.
    records : list[dict]
        Extracted sensitive records (category + span).
    per_record_eval : dict or None
        PerRecordEvaluation serialized to dict (if evaluator ran).
    masking_decision : str
        Final decision: ``"mask_all"``, ``"selective_mask"``, ``"process_locally"``.
    """

    text: str
    records: list[dict[str, Any]] = field(default_factory=list)
    per_record_eval: dict[str, Any] | None = None
    masking_decision: str = "mask_all"


class SlidingWindowMemory:
    """In-memory sliding-window session store.

    Each session keeps at most ``window_size`` recent entries.
    Oldest entries are evicted when the window is full.

    Parameters
    ----------
    window_size : int
        Maximum entries per session (default 5).

    Examples
    --------
    >>> mem = SlidingWindowMemory(window_size=3)
    >>> mem.add("s1", SessionEntry(text="hello"))
    >>> mem.add("s1", SessionEntry(text="world"))
    >>> len(mem.get("s1"))
    2
    >>> mem.get_context("s1")
    '---\nuser: hello\n---\nuser: world'
    """

    def __init__(self, window_size: int = 5) -> None:
        self._sessions: dict[str, deque[SessionEntry]] = defaultdict(
            lambda: deque(maxlen=window_size)
        )
        self.window_size = window_size

    def add(self, session_id: str, entry: SessionEntry) -> None:
        """Append an entry to the session's sliding window."""
        self._sessions[session_id].append(entry)

    def get(self, session_id: str) -> list[SessionEntry]:
        """Return all entries for a session (oldest first)."""
        return list(self._sessions.get(session_id, []))

    def get_context(self, session_id: str, n: int | None = None) -> str:
        """Return last N entries formatted as context string.

        Parameters
        ----------
        session_id : str
            Session identifier.
        n : int or None
            Number of recent entries to include. None = all.

        Returns
        -------
        str
            Formatted context, or empty string if no entries.
        """
        entries = self.get(session_id)
        if n is not None:
            entries = entries[-n:]

        if not entries:
            return ""

        lines = []
        for entry in entries:
            lines.append("---")
            lines.append(f"user: {entry.text}")
            if entry.records:
                recs = ", ".join(
                    f"{r.get('category', '?')}:{r.get('span', '?')}"
                    for r in entry.records
                )
                lines.append(f"detected: [{recs}]")
            if entry.masking_decision:
                lines.append(f"decision: {entry.masking_decision}")
        return "\n".join(lines)

    def clear(self, session_id: str) -> None:
        """Remove all entries for a session."""
        self._sessions.pop(session_id, None)


# Module-level singleton for demo use
_default_memory: SlidingWindowMemory | None = None


def get_memory() -> SlidingWindowMemory:
    """Return the shared sliding-window memory singleton."""
    global _default_memory
    if _default_memory is None:
        _default_memory = SlidingWindowMemory()
    return _default_memory
