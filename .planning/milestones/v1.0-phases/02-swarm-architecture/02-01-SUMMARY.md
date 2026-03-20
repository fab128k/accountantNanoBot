---
phase: 02-swarm-architecture
plan: 01
subsystem: architecture
tags: [swarm, dataclass, abc, python, agents, pipeline]

# Dependency graph
requires:
  - phase: 01-stack-cleanup
    provides: Clean requirements.txt with openai SDK native + pypdf + sentence-transformers; agents/base_agent.py using openai SDK directly
provides:
  - swarm/context.py — ProcessingContext dataclass (client_folder, current_file, errors, metadata)
  - swarm/base.py — BaseSwarmAgent ABC extending BaseAccountingAgent with abstract process()
  - swarm/__init__.py — public package re-exporting ProcessingContext and BaseSwarmAgent
  - conftest.py — pytest sys.path fixture for cross-interpreter test compatibility
affects:
  - 02-02 (agent migration — FatturazioneAgent and MemoriaAgent gain process())
  - 02-03 (orchestrator gains route_with_context())
  - All future pipeline plans that use ProcessingContext as shared state carrier

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "ProcessingContext dataclass as shared mutable state flowing through agent pipeline"
    - "BaseSwarmAgent ABC pattern — additive inheritance over BaseAccountingAgent"
    - "TYPE_CHECKING guard for ProcessingContext in base.py to prevent circular imports at runtime"
    - "field(default_factory=...) for mutable dataclass defaults (errors list, metadata dict)"

key-files:
  created:
    - swarm/__init__.py
    - swarm/context.py
    - swarm/base.py
    - conftest.py
    - tests/test_swarm_foundation.py
  modified: []

key-decisions:
  - "ProcessingContext is a @dataclass (not plain class) — free __repr__, __eq__, clean field syntax"
  - "errors and metadata use field(default_factory=...) to ensure per-instance mutable containers"
  - "Context is NOT accounting-aware at base level — agents write domain outputs into metadata dict under agreed keys"
  - "BaseSwarmAgent is purely additive — extends BaseAccountingAgent, adds only process() abstractmethod, no __init__ override"
  - "TYPE_CHECKING guard for ProcessingContext in base.py mirrors agents/base_agent.py pattern (used for KnowledgeBaseManager)"
  - "conftest.py added to fix pytest sys.path when pytest binary uses /bin/python 3.10 but project uses pyenv 3.13"

patterns-established:
  - "Swarm pipeline pattern: agents receive ProcessingContext, mutate metadata/errors, return same instance"
  - "Error accumulation: agents append to context.errors rather than raising exceptions from process()"
  - "TDD cycle for new modules: write failing tests → commit RED → implement → all tests pass GREEN → commit"

requirements-completed: [SWARM-01, SWARM-02]

# Metrics
duration: 4min
completed: 2026-03-18
---

# Phase 2 Plan 01: Swarm Architecture Foundation Summary

**ProcessingContext dataclass and BaseSwarmAgent ABC — the shared state container and abstract agent interface for the entire swarm pipeline**

## Performance

- **Duration:** 4 min
- **Started:** 2026-03-18T17:21:21Z
- **Completed:** 2026-03-18T17:25:00Z
- **Tasks:** 1 (TDD: 2 commits — RED + GREEN)
- **Files modified:** 5 (3 new swarm package files + conftest.py + test file)

## Accomplishments

- `swarm/context.py`: ProcessingContext dataclass with client_folder, current_file (optional), errors (list), metadata (dict) — fully importable, mutable defaults via factory
- `swarm/base.py`: BaseSwarmAgent ABC extending BaseAccountingAgent, adds abstract `process(context) -> ProcessingContext` method — cannot be instantiated directly
- `swarm/__init__.py`: public re-exports so `from swarm import ProcessingContext, BaseSwarmAgent` works
- `conftest.py`: adds project root to sys.path fixing pytest cross-interpreter (/bin/python 3.10 vs pyenv 3.13) compatibility
- 23 TDD tests all passing covering fields, mutability, isolation, abstract enforcement, inheritance, and import paths

## Task Commits

Each task was committed atomically:

1. **Task 1 (RED): swarm foundation failing tests** - `c11d00c` (test)
2. **Task 1 (GREEN): swarm foundation implementation** - `b2d4e29` (feat)

_Note: TDD task — two commits (RED failing tests → GREEN implementation)_

## Files Created/Modified

- `swarm/context.py` — ProcessingContext @dataclass: client_folder Path, current_file Optional[Path], errors list[str], metadata dict
- `swarm/base.py` — BaseSwarmAgent(BaseAccountingAgent, ABC) with abstract process() method; TYPE_CHECKING guard for circular-import-safe type hints
- `swarm/__init__.py` — Package init re-exporting ProcessingContext and BaseSwarmAgent; defines __all__
- `conftest.py` — Pytest sys.path fix for cross-Python-version compatibility
- `tests/test_swarm_foundation.py` — 23 tests covering all acceptance criteria

## Decisions Made

- Used `@dataclass` decorator per 02-CONTEXT.md decision — not a plain class.
- `errors` and `metadata` use `field(default_factory=...)` — critical for preventing the classic shared-mutable-default bug across instances.
- `ProcessingContext` is kept domain-neutral at the base level — no accounting-specific fields. Agents write into `metadata["registrazione_suggerita"]`, etc.
- TYPE_CHECKING guard in `swarm/base.py` for ProcessingContext import mirrors the exact pattern used in `agents/base_agent.py` for KnowledgeBaseManager — consistent style, avoids runtime circular import.
- `conftest.py` added (Rule 3 auto-fix) to resolve pytest using `/bin/python` (3.10) while project is pyenv 3.13 — without it all tests fail with ModuleNotFoundError even though files exist.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Added conftest.py for pytest sys.path compatibility**
- **Found during:** Task 1 (GREEN phase — tests still failing after files created)
- **Issue:** pytest binary `/home/admaiora/.local/bin/pytest` uses `/bin/python` (Python 3.10 system interpreter); project files are in pyenv 3.13's site-packages path. The `swarm/` directory was not on Python 3.10's `sys.path`, causing `ModuleNotFoundError: No module named 'swarm'` despite the package existing.
- **Fix:** Created `conftest.py` at project root that inserts the project root into `sys.path` before tests run. This is the standard pytest pattern for monorepo/non-installed packages.
- **Files modified:** `conftest.py` (new)
- **Verification:** All 23 tests pass after fix; `python -c "from swarm import ProcessingContext"` also passes with project Python
- **Committed in:** b2d4e29 (Task 1 GREEN commit)

---

**Total deviations:** 1 auto-fixed (1 blocking)
**Impact on plan:** conftest.py is a test infrastructure prerequisite — without it no tests can run. No scope creep; zero changes to any production code path.

## Issues Encountered

None beyond the conftest.py fix documented above.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- `swarm/` package is complete and importable with zero circular imports
- `ProcessingContext` and `BaseSwarmAgent` ready for plan 02-02: migrate FatturazioneAgent and MemoriaAgent to extend BaseSwarmAgent and implement `process()`
- `agents/base_agent.py`, `agents/fatturazione_agent.py`, `agents/memoria_agent.py`, `agents/orchestrator.py` are all unmodified — additive migration starts in next plan

---
*Phase: 02-swarm-architecture*
*Completed: 2026-03-18*

## Self-Check: PASSED

All created files verified on disk. All commits confirmed in git log.
