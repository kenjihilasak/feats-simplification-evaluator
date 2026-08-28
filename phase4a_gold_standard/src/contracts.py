"""Compatibility re-export for the canonical Phase 4a data contracts."""

from __future__ import annotations

try:
    from .data_contracts import *  # noqa: F401,F403
except ImportError:
    from data_contracts import *  # noqa: F401,F403
