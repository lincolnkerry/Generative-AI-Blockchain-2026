"""Root conftest.py — adds project root to sys.path for monorepo imports."""

from __future__ import annotations

import sys
from pathlib import Path

# Add project root so that `agents.*`, `server.*`, `db.*` imports work
_ROOT = Path(__file__).resolve().parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))
