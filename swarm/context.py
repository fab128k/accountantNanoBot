# swarm/context.py
# AccountantNanoBot — Shared processing context for the swarm pipeline
# ============================================================================
# ProcessingContext is a lightweight dataclass that flows through the agent
# pipeline. It carries the client folder path, the file currently being
# processed, accumulated error strings, and a free-form metadata dict where
# agents write their domain outputs (e.g. registrazione_suggerita, iva_data).
#
# Design decisions (from 02-CONTEXT.md):
# - Use @dataclass (not plain class) for free __repr__, __eq__, and clean field
#   declaration syntax.
# - errors and metadata use field(default_factory=...) so each instance gets
#   its own independent mutable container — no shared-state bugs.
# - Context is NOT accounting-aware at this level. Agents write domain results
#   into metadata under agreed-upon keys. This keeps the base class stable
#   while allowing each agent to evolve its output schema independently.
# ============================================================================

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class ProcessingContext:
    """
    Shared state container that flows through the swarm agent pipeline.

    Agents receive this context, do their work, write outputs into
    ``metadata``, append any problems to ``errors``, and return it.
    The caller (pipeline or UI adapter) inspects ``errors`` after each step.

    Attributes:
        client_folder: Root directory of the client's document folder.
        current_file: The specific file being processed in the current step,
            or None when the operation is folder-wide.
        errors: Accumulator for non-fatal error strings. Agents MUST append
            here rather than raising exceptions from process().
        metadata: Free-form dict for inter-agent communication. Each agent
            writes outputs under agreed keys (e.g.
            ``metadata['registrazione_suggerita']``).
    """

    client_folder: Path
    current_file: Optional[Path] = None
    errors: list[str] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)
