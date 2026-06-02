"""Privacy Router — Masker package.

Masking and hydration with fail-fast contracts.  The Masker handles
both phases of the sensitive-data lifecycle.

Public API
----------
Masker
    Main masking/hydration engine.
MaskingContract
    Immutable contract linking the two phases.
MaskingResult
    Output of :meth:`Masker.mask`.
HydrationResult
    Output of :meth:`Masker.hydrate`.
HydrationError
    Raised when hydration encounters unresolvable placeholders.

Examples
--------
>>> from agents.masker import Masker
>>> masker = Masker()
>>> result = masker.mask("hello", [])
>>> result.masked_text
'hello'
"""

from .masker import HydrationError, Masker
from .schemas import HydrationResult, MaskingContract, MaskingResult

__all__ = [
    "Masker",
    "MaskingContract",
    "MaskingResult",
    "HydrationResult",
    "HydrationError",
]
