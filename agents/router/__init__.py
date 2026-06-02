"""Privacy Router — Router package.

Execution layer and top-level orchestrator.  :class:`PrivacyRouter`
is the main entry point that chains Extractor → Judge → Router.

Public API
----------
PrivacyRouter
    Top-level pipeline orchestrator.
Router
    Pure execution layer (no LLM calls).
RouteResult
    Concrete routing result.
process
    Module-level convenience function.

Examples
--------
>>> from agents.router import PrivacyRouter
>>> pr = PrivacyRouter()
>>> result = pr.process("hello")
>>> result.route.endpoint
'external_api'
"""

from .router import PrivacyRouter, Router, process
from .schemas import RouteResult

__all__ = ["PrivacyRouter", "Router", "RouteResult", "process"]
