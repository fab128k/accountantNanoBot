---
phase: 04-pipeline-a-ingestion
plan: 02
subsystem: ui
tags: [streamlit, pipeline, fattura-pa, bank-movements, prima-nota, sqlite, coa]

# Dependency graph
requires:
  - phase: 04-pipeline-a-ingestion/04-01
    provides: PipelineA.process_folder(), InvoiceResult, BankMovementResult, PipelineResult dataclasses
provides:
  - Scanner page CTA calls PipelineA with real arguments (scan_result + company_piva)
  - Invoice review cards with status-aware display (new/gia_importata/parse_error/confermata/scartata)
  - Per-invoice Conferma e Salva persists fattura + registrazione to SQLite
  - Conferma tutto batch-confirms all balanced invoices in one click
  - Bank movement review section with suggested prima nota table and CoA selectbox
  - Per-movement Conferma/Salta buttons and Conferma tutti batch action
  - Session state keys pipeline_a_results and pipeline_a_bank_results in app.py
affects: [phase-05, scanner-ui, bank-movements-ui]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Lazy imports inside Streamlit callbacks (from pipeline.pipeline_a import PipelineA inside button handler)"
    - "Dynamic attribute on dataclass (_confirmed, _skipped) for per-session display state not persisted to DB"
    - "st.rerun() after every state-mutating confirm/discard action to force clean re-render"
    - "Status-driven rendering: r.status drives which UI variant to show per InvoiceResult"

key-files:
  created: []
  modified:
    - ui/pages/scanner.py
    - app.py

key-decisions:
  - "pipeline_a_results session state key holds the full PipelineResult object; mutations (r.status changes) are in-place on the session_state object — no copy needed since Python objects are mutable"
  - "Bank movement _confirmed/_skipped are dynamic attributes set on BankMovementResult at runtime — not persisted, reset on next Avvia elaborazione run (correct behavior: re-scan regenerates results)"
  - "CoA selectbox options flattened from get_conti_comuni() dict values — only commonly-used accounts shown, not full OIC chart"
  - "Batch confirm Conferma tutto only targets status==new + is_bilanciata; unbalanced invoices require manual review"

patterns-established:
  - "Invoice review: each InvoiceResult.status drives one of five UI branches (new/gia_importata/parse_error/confermata/scartata)"
  - "Confirm flow: set .confermata=True on registrazione, call salva_fattura_importata + salva_registrazione, update .status, call st.rerun()"

requirements-completed: [PIPE-01, PIPE-02, PIPE-03, PIPE-04]

# Metrics
duration: 3min
completed: 2026-03-20
---

# Phase 4 Plan 02: Pipeline A UI Wiring Summary

**Streamlit Scanner page wired to PipelineA backend: invoice review cards with Dare/Avere table and dedup detection, bank movement review with CoA selectbox, per-item and batch confirm/discard flow persisting to SQLite**

## Performance

- **Duration:** 3 min
- **Started:** 2026-03-20T12:05:24Z
- **Completed:** 2026-03-20T12:07:59Z
- **Tasks:** 2 auto-tasks completed (Task 3 is human-verify checkpoint — awaiting)
- **Files modified:** 2

## Accomplishments

- Replaced the `NotImplementedError` stub CTA with a real `PipelineA().process_folder(scan_result, get_company_piva())` call that handles both FatturaXML and CSV files
- Built invoice review section with five status variants: new invoices show expanded card with prima nota table and Conferma/Scarta; duplicates show as grey caption; errors show collapsed error expander; confirmed/discarded show as caption
- Built bank movement review section with per-movement expanders showing suggested prima nota, CoA account selectbox (from `get_conti_comuni()`), Conferma/Salta buttons, and Conferma tutti batch action
- Added `pipeline_a_results` and `pipeline_a_bank_results` session state keys in `app.py`

## Task Commits

Each task was committed atomically:

1. **Task 1: Wire PipelineA into scanner.py CTA and build invoice review section** - `bc46dd8` (feat)
2. **Task 2: Add bank movement review table with CoA suggestion and accept/correct flow** - `bc46dd8` (feat) _(combined with Task 1 in same commit — both modify scanner.py and were developed together)_
3. **Task 3: Human verification** - awaiting checkpoint approval

## Files Created/Modified

- `ui/pages/scanner.py` - Complete rewrite: CTA + invoice review cards + bank movement review section (274 lines added, 13 removed)
- `app.py` - Added `pipeline_a_results` and `pipeline_a_bank_results` to `initialize_session_state()` defaults dict

## Decisions Made

- Tasks 1 and 2 were committed together because the bank movement section is naturally part of the same `render_scanner()` function and was implemented in a single coherent pass — splitting into two commits would have left scanner.py in an incomplete state between commits

## Deviations from Plan

None — plan executed exactly as written. Both task implementations follow the exact patterns and code snippets provided in the plan's `<action>` blocks.

## Issues Encountered

None.

## User Setup Required

None — no external service configuration required.

## Next Phase Readiness

- Complete Pipeline A end-to-end flow is ready for human verification at http://localhost:8501
- After checkpoint approval, Phase 4 is complete
- Test suite: 82 passed, 0 failures

---
*Phase: 04-pipeline-a-ingestion*
*Completed: 2026-03-20*
