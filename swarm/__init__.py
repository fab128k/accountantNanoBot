# swarm/__init__.py
# AccountantNanoBot — Swarm package public API
# ============================================================================
# Re-exports the two public classes so callers can use the convenient forms:
#
#   from swarm import ProcessingContext
#   from swarm import BaseSwarmAgent
#
# Both are also importable from their own modules (swarm.context and
# swarm.base) for cases where explicit module paths are preferred.
# ============================================================================

from .context import ProcessingContext
from .base import BaseSwarmAgent

__all__ = ["ProcessingContext", "BaseSwarmAgent"]
