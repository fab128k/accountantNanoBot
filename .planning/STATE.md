# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-03-18)

**Core value:** L'utente punta alla cartella cliente, scrive in chat cosa vuole, e riceve registrazioni contabili corrette e PDF pronti — senza toccare un singolo campo manualmente.
**Current focus:** Phase 1 — Stack Cleanup

## Current Position

Phase: 1 of 4 (Stack Cleanup)
Plan: 0 of TBD in current phase
Status: Ready to plan
Last activity: 2026-03-18 — Roadmap created; milestone 1 scoped into 4 phases

Progress: [░░░░░░░░░░] 0%

## Performance Metrics

**Velocity:**
- Total plans completed: 0
- Average duration: -
- Total execution time: 0 hours

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| - | - | - | - |

**Recent Trend:**
- Last 5 plans: -
- Trend: -

*Updated after each plan completion*

## Accumulated Context

### Decisions

Decisions are logged in PROJECT.md Key Decisions table.
Recent decisions affecting current work:

- Stack: LangChain, SQLAlchemy removed — openai SDK nativo + sqlite3 nativo already in use
- Stack: PyPDF2 deprecated, replacing with pypdf (same maintainer, drop-in)
- Stack: sentence-transformers needed for Italian-quality RAG embeddings (multilingual MiniLM)
- Architecture: Swarm pattern with ProcessingContext — agents are dumb, context carries state
- Architecture: Agents are sequential (not parallel) — hardware constraint 16GB/4GB VRAM

### Pending Todos

None yet.

### Blockers/Concerns

None yet.

## Session Continuity

Last session: 2026-03-18
Stopped at: Roadmap created, STATE.md initialized — ready to plan Phase 1
Resume file: None
