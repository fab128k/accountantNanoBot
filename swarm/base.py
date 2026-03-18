# swarm/base.py
# AccountantNanoBot — Abstract base class for swarm pipeline agents
# ============================================================================
# BaseSwarmAgent adds a single abstract method, process(), on top of the
# existing BaseAccountingAgent. All specialized agents (FatturazioneAgent,
# MemoriaAgent, etc.) will extend this class so they can participate in the
# swarm pipeline via route_with_context().
#
# Design decisions (from 02-CONTEXT.md):
# - Extends BaseAccountingAgent (additive pattern — does not replace it).
# - process() is an @abstractmethod: every concrete agent MUST implement it.
# - No __init__ override — BaseAccountingAgent.__init__ is inherited intact.
# - TYPE_CHECKING guard for ProcessingContext mirrors the pattern already used
#   in agents/base_agent.py for KnowledgeBaseManager, preventing circular
#   imports at runtime while preserving static-analysis type hints.
# ============================================================================

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from agents.base_agent import BaseAccountingAgent

if TYPE_CHECKING:
    from swarm.context import ProcessingContext


class BaseSwarmAgent(BaseAccountingAgent, ABC):
    """
    Abstract base class for all swarm pipeline agents.

    Extends :class:`agents.base_agent.BaseAccountingAgent` with the
    ``process()`` contract required by the swarm pipeline. Every concrete
    agent must implement ``process()`` to participate in
    ``route_with_context()`` calls.

    Inherited from BaseAccountingAgent:
        - ``name``, ``model``, ``system_prompt``, ``temperature``, ``base_url``
        - ``ask()`` / ``stream_ask()`` for LLM interaction
        - ``set_rag_manager()`` / ``_get_rag_context()`` for RAG access

    Subclass contract:
        - Implement ``process(context) -> ProcessingContext``
        - Write domain outputs into ``context.metadata`` under agreed keys
        - Append error strings to ``context.errors`` on failure (do not raise)
        - Always return the context (same instance, mutated in place)
    """

    @abstractmethod
    def process(self, context: "ProcessingContext") -> "ProcessingContext":
        """
        Process the current state and return the (possibly modified) context.

        Args:
            context: The shared :class:`~swarm.context.ProcessingContext`
                flowing through the pipeline.

        Returns:
            The same context instance with outputs written into
            ``context.metadata`` and any errors appended to
            ``context.errors``.
        """
        ...
