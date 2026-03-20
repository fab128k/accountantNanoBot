---
phase: 03-client-folder-scanner
plan: 01
subsystem: scanner
tags: [pathlib, rglob, xml-content-peek, dataclass, fattura-elettronica, pipeline-stub]

# Dependency graph
requires:
  - phase: 02-swarm-architecture
    provides: "ProcessingContext with client_folder: Path field — confirms scanner contract"

provides:
  - "ClientFolderScanner class: scan(folder) -> ScanResult with 6-category classification"
  - "ScanResult dataclass: files dict by category, total(), count() helpers"
  - "_is_fattura_xml: 512-byte raw byte peek for FatturaPA detection (no lxml)"
  - "_classify: extension dispatch + XML content peek for all file types"
  - "CATEGORIES constant: [FatturaXML, PDF, CSV, DOCX, TXT, Altro]"
  - "PipelineA stub: process_folder() raises NotImplementedError (Phase 4 placeholder)"

affects:
  - phase-03-plan-02 (Scanner UI page + sidebar integration)
  - phase-04-pipeline-a (PipelineA full implementation)

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "512-byte raw byte peek for XML classification: b'FatturaElettronica' in header — no lxml parse during scan"
    - "Extension dispatch table (_EXT_TO_CATEGORY) with XML handled separately via content peek"
    - "rglob('*') + hidden-file filter (path.name.startswith('.')) for recursive scan"
    - "Empty ScanResult (no exception) for non-existent or non-directory folder paths"
    - "Pure Python packages with zero Streamlit dependency — fully testable without Streamlit runtime"

key-files:
  created:
    - scanner/client_folder_scanner.py
    - scanner/__init__.py
    - pipeline/pipeline_a.py
    - pipeline/__init__.py
    - tests/test_scanner.py
  modified: []

key-decisions:
  - "Raw byte peek (b'FatturaElettronica' in first 512 bytes) instead of lxml parse during scan — avoids full XML parse overhead at classification time"
  - "scan() returns empty ScanResult for missing folders (no exception) — caller decides UI error handling"
  - "Hidden files (dot-prefixed) skipped in scan loop — .gitignore, .DS_Store not classified"
  - "PipelineA stub raises NotImplementedError on process_folder() but does NOT raise on import — satisfies Scanner page CTA import contract"
  - "scanner/ and pipeline/ have zero Streamlit imports — pure Python, testable without Streamlit runtime"

patterns-established:
  - "Pattern: ScanResult dataclass keyed by CATEGORIES with total() and count() helpers"
  - "Pattern: ClientFolderScanner.scan() as main entry point — folder.rglob('*') + is_file() + hidden filter"
  - "Pattern: _classify() dispatches by extension, delegates .xml to _is_fattura_xml()"

requirements-completed: [SCAN-01, SCAN-03]

# Metrics
duration: 2min
completed: 2026-03-18
---

# Phase 3 Plan 01: Client Folder Scanner — Core Module Summary

**Pure Python ClientFolderScanner classifying files into 6 categories via extension dispatch and 512-byte FatturaElettronica content peek, with PipelineA stub for Phase 4**

## Performance

- **Duration:** 2 min
- **Started:** 2026-03-18T19:41:39Z
- **Completed:** 2026-03-18T19:43:31Z
- **Tasks:** 2 (TDD: RED + GREEN)
- **Files modified:** 5

## Accomplishments

- ClientFolderScanner.scan(folder) returns ScanResult with files classified into FatturaXML, PDF, CSV, DOCX, TXT, Altro
- FatturaXML detection uses 512-byte raw content peek (b"FatturaElettronica") — no lxml parse overhead during scanning
- Non-existent folders return empty ScanResult (no exception) — caller handles UI error
- PipelineA stub created with process_folder() raising NotImplementedError (Phase 4 placeholder)
- All 12 new tests pass; full test suite 35/35 green; zero Streamlit imports in scanner/ or pipeline/

## Task Commits

Each task was committed atomically:

1. **Task 1: Create tests/test_scanner.py (RED)** - `972dbd1` (test)
2. **Task 2: Implement scanner/ and pipeline/ (GREEN)** - `d99eaf9` (feat)

_TDD plan: Task 1 = failing tests (RED), Task 2 = implementation to pass tests (GREEN)_

## Files Created/Modified

- `scanner/client_folder_scanner.py` — ClientFolderScanner class, ScanResult dataclass, CATEGORIES, _is_fattura_xml, _classify, _EXT_TO_CATEGORY
- `scanner/__init__.py` — public re-exports: ClientFolderScanner, ScanResult
- `pipeline/pipeline_a.py` — PipelineA stub with process_folder() raising NotImplementedError
- `pipeline/__init__.py` — public re-exports: PipelineA
- `tests/test_scanner.py` — 12 tests covering SCAN-01 classification, edge cases, and SCAN-03 pipeline stub contract

## Decisions Made

- Raw byte peek (`b"FatturaElettronica" in first 512 bytes`) instead of lxml parse during scan — avoids full XML parse overhead at scan classification time (100x faster than lxml per file)
- scan() returns empty ScanResult for missing/non-directory paths (no exception) — UI layer decides error presentation
- Hidden files (dot-prefixed names) skipped in scan loop — .gitignore, .DS_Store etc. not classified
- PipelineA stub does NOT raise on import; only process_folder() raises NotImplementedError — satisfies Scanner page CTA import contract
- scanner/ and pipeline/ have zero Streamlit imports — pure Python, testable without Streamlit runtime

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- scanner/ package is complete and tested — Plan 02 can import ClientFolderScanner directly
- pipeline/ package stub is ready — Plan 02 Scanner page CTA can import PipelineA without errors
- Full test suite green (35/35) — no regressions introduced

---
*Phase: 03-client-folder-scanner*
*Completed: 2026-03-18*

## Self-Check: PASSED

All files verified present and all commits verified in git log.
