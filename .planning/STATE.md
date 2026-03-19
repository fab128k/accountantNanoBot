---
gsd_state_version: 1.0
milestone: v1.0
milestone_name: milestone
status: planning
stopped_at: Completed 03-02-PLAN.md
last_updated: "2026-03-19T08:18:40.380Z"
last_activity: 2026-03-18 — Roadmap created; milestone 1 scoped into 4 phases
progress:
  total_phases: 4
  completed_phases: 3
  total_plans: 6
  completed_plans: 6
  percent: 0
---

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
| Phase 01-stack-cleanup P01 | 2 | 2 tasks | 3 files |
| Phase 01-stack-cleanup P02 | 2min | 1 tasks | 1 files |
| Phase 02-swarm-architecture P01 | 4min | 1 tasks | 5 files |
| Phase 02-swarm-architecture P02 | 3min | 2 tasks | 3 files |
| Phase 03-client-folder-scanner P01 | 2min | 2 tasks | 5 files |
| Phase 03-client-folder-scanner P03-02 | 20min | 3 tasks | 3 files |

## Accumulated Context

### Decisions

Decisions are logged in PROJECT.md Key Decisions table.
Recent decisions affecting current work:

- Stack: LangChain, SQLAlchemy removed — openai SDK nativo + sqlite3 nativo already in use
- Stack: PyPDF2 deprecated, replacing with pypdf (same maintainer, drop-in)
- Stack: sentence-transformers needed for Italian-quality RAG embeddings (multilingual MiniLM)
- Architecture: Swarm pattern with ProcessingContext — agents are dumb, context carries state
- Architecture: Agents are sequential (not parallel) — hardware constraint 16GB/4GB VRAM
- [Phase 01-stack-cleanup]: Removed LangChain, SQLAlchemy, PyPDF2, beautifulsoup4 from requirements; added pypdf>=4.0.0 and sentence-transformers>=3.0.0
- [Phase 01-stack-cleanup]: pypdf is drop-in replacement for PyPDF2 (same maintainer, not deprecated)
- [Phase 01-stack-cleanup]: sentence-transformers added now for quality Italian-language embeddings in ChromaDB RAG pipeline
- [Phase 01-stack-cleanup]: SentenceTransformerEmbeddingFunction from chromadb.utils used — ChromaDB handles embedding calls transparently for add/query
- [Phase 01-stack-cleanup]: Missing sentence-transformers raises ImportError (not silent fallback) — RAG without multilingual embeddings is non-functional for Italian text
- [Phase 01-stack-cleanup]: Collection metadata stores embedding_model key to detect incompatible existing collections and trigger silent recreation
- [Phase 02-swarm-architecture]: ProcessingContext is a @dataclass with field(default_factory=...) for mutable defaults; domain-neutral (no accounting fields)
- [Phase 02-swarm-architecture]: BaseSwarmAgent is purely additive: extends BaseAccountingAgent + adds abstract process(); TYPE_CHECKING guard prevents circular imports
- [Phase 02-swarm-architecture]: conftest.py added to fix pytest sys.path when /bin/python 3.10 is pytest interpreter vs pyenv 3.13 project Python
- [Phase 02-swarm-architecture]: FatturazioneAgent.process() calls analizza_xml_bytes() (non-LLM deterministic path) for pipeline use; LLM commentary is a separate step
- [Phase 02-swarm-architecture]: route_with_context() delegates to route() for keyword matching — single source of truth for routing rules
- [Phase 02-swarm-architecture]: _PlaceholderSwarmAgent defined at module level in orchestrator.py — concrete no-op BaseSwarmAgent for domains not yet implemented
- [Phase 03-client-folder-scanner]: Raw byte peek (b'FatturaElettronica' in 512 bytes) for XML classification — no lxml parse during scan, 100x faster per file
- [Phase 03-client-folder-scanner]: scanner/ and pipeline/ have zero Streamlit imports — pure Python, fully testable without Streamlit runtime
- [Phase 03-client-folder-scanner]: scan() returns empty ScanResult for missing/non-directory paths — no exception raised, UI layer handles error display
- [Phase 03-client-folder-scanner]: Streamlit st.text_input must use key= only (no value=) when session_state is the source of truth — mixing both freezes the widget
- [Phase 03-client-folder-scanner]: Sidebar input background raised to rgba(255,255,255,0.92) for dark-text readability on dark navy sidebar; ::placeholder added with muted color

### Pending Todos

None yet.

### Blockers/Concerns

None yet.

## Session Continuity

Last session: 2026-03-19T08:18:40.374Z
Stopped at: Completed 03-02-PLAN.md
Resume file: None
