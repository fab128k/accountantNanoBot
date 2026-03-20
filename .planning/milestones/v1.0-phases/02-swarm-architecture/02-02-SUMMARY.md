---
phase: 02-swarm-architecture
plan: "02"
subsystem: agents
tags: [swarm, agents, orchestrator, BaseSwarmAgent, ProcessingContext, routing]

# Dependency graph
requires:
  - phase: 02-01
    provides: BaseSwarmAgent abstract class and ProcessingContext dataclass

provides:
  - FatturazioneAgent inheriting BaseSwarmAgent with process() for XML FatturaPA files
  - MemoriaAgent inheriting BaseSwarmAgent with process() for user_message RAG queries
  - _PlaceholderSwarmAgent for unimplemented domains (iva, bilancio, compliance, prima_nota)
  - Orchestrator.route_with_context() routing ProcessingContext through agent pipeline

affects: [pipeline-a-ingestion, pipeline-b-ingestion, client-folder-scanner]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "All concrete agents inherit BaseSwarmAgent and implement process()"
    - "process() never raises: errors appended to context.errors, context returned"
    - "route_with_context() delegates routing to existing keyword-based route() logic"
    - "_PlaceholderSwarmAgent as no-op concrete subclass for placeholder domains"

key-files:
  created: []
  modified:
    - agents/fatturazione_agent.py
    - agents/memoria_agent.py
    - agents/orchestrator.py

key-decisions:
  - "FatturazioneAgent.process() uses existing analizza_xml_bytes() — no new XML logic, reuses existing deterministic path"
  - "MemoriaAgent.process() calls ask() on user_message — integrates RAG transparently via existing BaseAccountingAgent infrastructure"
  - "_PlaceholderSwarmAgent defined at module level (not inside build_default_orchestrator) for reusability"
  - "route_with_context() reuses route() keyword matching — single source of truth for routing rules"
  - "TYPE_CHECKING guard for ProcessingContext in all agent files — prevents circular imports at runtime"

patterns-established:
  - "Agent migration pattern: change parent class import + add process() + preserve all existing methods unchanged"
  - "Swarm process() contract: write outputs to context.metadata, append errors to context.errors, always return context"

requirements-completed: [SWARM-03]

# Metrics
duration: 3min
completed: 2026-03-18
---

# Phase 02 Plan 02: Agent Migration Summary

**All 6 swarm agents (fatturazione, memoria, iva, bilancio, compliance, prima_nota) migrated to BaseSwarmAgent with process(), and Orchestrator extended with route_with_context() for context-based pipeline routing**

## Performance

- **Duration:** 3 min
- **Started:** 2026-03-18T17:28:53Z
- **Completed:** 2026-03-18T17:31:52Z
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments
- FatturazioneAgent and MemoriaAgent migrated from BaseAccountingAgent to BaseSwarmAgent, each implementing process() while preserving all existing specialized methods
- Four placeholder agents (iva, bilancio, compliance, prima_nota) migrated from BaseAccountingAgent instances to _PlaceholderSwarmAgent instances with no-op process()
- Orchestrator.route_with_context() added: routes a ProcessingContext to the correct agent using existing keyword logic, calls agent.process(), writes routed_to in metadata
- Zero UI regression: app.py, ui/pages/ untouched; route(), get_agent(), list_agents(), set_rag_manager() APIs all unchanged

## Task Commits

Each task was committed atomically:

1. **Task 1: Migrate FatturazioneAgent and MemoriaAgent to BaseSwarmAgent** - `a8d291a` (feat)
2. **Task 2: Add route_with_context() and migrate placeholder agents** - `c52412a` (feat)

**Plan metadata:** (docs commit — see final commit below)

## Files Created/Modified
- `agents/fatturazione_agent.py` - Now extends BaseSwarmAgent; added process() that calls analizza_xml_bytes() on XML current_file
- `agents/memoria_agent.py` - Now extends BaseSwarmAgent; added process() that calls ask() on metadata user_message
- `agents/orchestrator.py` - Added _PlaceholderSwarmAgent class; added route_with_context() method; migrated placeholder agent construction

## Decisions Made
- FatturazioneAgent.process() calls analizza_xml_bytes() (not processa_fattura()) — the non-LLM deterministic path is correct for pipeline use; LLM commentary is a separate step
- MemoriaAgent.process() calls ask() on user_message — routes naturally through existing RAG infrastructure
- _PlaceholderSwarmAgent defined at module level so it is importable and reusable if needed by future pipeline code
- route_with_context() delegates entirely to route() to avoid duplicating routing rules

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Complete swarm architecture foundation in place: ProcessingContext, BaseSwarmAgent, all 6 agents with process(), Orchestrator with route_with_context()
- Ready for Phase 3: Client Folder Scanner
- Ready for Phase 4: Pipeline A ingestion (pass ProcessingContext with current_file=xml_path through route_with_context())

---
*Phase: 02-swarm-architecture*
*Completed: 2026-03-18*
