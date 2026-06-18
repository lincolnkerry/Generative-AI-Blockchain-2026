"""Session memory package.

Public API:
    - SlidingWindowMemory: in-memory sliding-window session store
    - SessionEntry: one interaction in the window
    - get_memory: shared singleton
"""

from .session import SessionEntry, SlidingWindowMemory, get_memory

__all__ = ["SlidingWindowMemory", "SessionEntry", "get_memory"]
