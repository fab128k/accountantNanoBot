---
phase: 04-pipeline-a-ingestion
plan: 01
subsystem: database, pipeline
tags: [sqlite, csv-parsing, fattura-pa, pipeline, decimal, iban, prima-nota, tdd]

# Dependency graph
requires:
  - phase: 03-client-folder-scanner
    provides: ScanResult dataclass with files dict keyed by category
  - phase: 01-stack-cleanup
    provides: SQLite native db.py, openai SDK setup
  - phase: 02-swarm-architecture
    provides: ProcessingContext pattern, RegistrazionePrimaNota.from_suggestion()

provides:
  - PipelineA.process_folder(scan_result, company_piva, db_path) -> PipelineResult
  - InvoiceResult, BankMovementResult, PipelineResult dataclasses
  - BankStatementParser with Italian CSV format auto-detection
  - BankMovement dataclass with Decimal importo (positive=income, negative=expense)
  - iban_coa_mapping table + get/save_iban_coa_mapping() CRUD
  - movimenti_bancari table + salva_movimento_bancario()
  - 47 new tests covering all four PIPE requirements

affects:
  - 04-02 (UI plan that consumes InvoiceResult/BankMovementResult for review workflow)
  - future Pipeline B (same db_path isolation pattern for test safety)

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "db_path optional parameter for test isolation (avoids touching production DB)"
    - "TDD: RED tests created before implementation, then GREEN after"
    - "Local imports inside process_folder() to prevent circular dependencies"
    - "TYPE_CHECKING guard for ScanResult/FatturaPA/BankMovement type hints"
    - "_parse_italian_decimal: regex strips thousands separators before Decimal()"

key-files:
  created:
    - pipeline/csv_bank_parser.py
    - tests/test_pipeline_a.py
    - tests/test_bank_parser.py
  modified:
    - accounting/db.py
    - pipeline/pipeline_a.py
    - pipeline/__init__.py
    - tests/test_scanner.py

key-decisions:
  - "db_path parameter added to process_folder() to support test isolation without mocking"
  - "Accrediti/Addebiti column detection uses has_accrediti+has_addebiti flags before falling back to single Importo column"
  - "IBAN pattern regex requires 11-30 alphanumeric chars after 2-letter country + 2 digits (matches real IBANs)"
  - "_detect_header_row requires BOTH keyword in header row AND date pattern in NEXT row for reliable detection"
  - "TestDeduplication passes db_path to isolate from production DB — no monkeypatching needed"
  - "test_scanner.py TestPipelineAStub replaced with TestPipelineAImport — stub is gone, import tests added"

patterns-established:
  - "Pipeline result objects are pure data (no DB writes) — all persistence is human-gated in UI layer"
  - "CSVs skipped silently on parse exception — pipeline is a library, not a CLI"
  - "IBAN-CoA mapping defaults to C.IV.1 (Depositi bancari) when no custom mapping exists"

requirements-completed: [PIPE-01, PIPE-02, PIPE-03, PIPE-04]

# Metrics
duration: 6min
completed: 2026-03-20
---

# Phase 4 Plan 01: Pipeline A Core Summary

**PipelineA.process_folder() with Italian CSV bank parsing, IBAN-to-CoA mapping, invoice dedup, and 47 passing TDD tests covering all four PIPE requirements**

## Performance

- **Duration:** 6 min
- **Started:** 2026-03-20T11:53:25Z
- **Completed:** 2026-03-20T12:00:00Z
- **Tasks:** 3
- **Files modified:** 7

## Accomplishments
- Extended SQLite schema with iban_coa_mapping + movimenti_bancari tables and three new CRUD functions
- Implemented BankStatementParser with Italian semicolon CSV auto-detection: finds header row by keyword+date-pattern heuristic, extracts IBAN from metadata header rows, handles Accrediti/Addebiti dual-column and single Importo column layouts
- Implemented PipelineA.process_folder() processing FatturaXML (new/gia_importata/parse_error statuses) and CSV (BankMovementResult with prima nota suggestions using IBAN-CoA mapping)
- Full TDD: 47 new tests GREEN alongside 35 pre-existing tests (82 total, zero failures)

## Task Commits

1. **Task 1: DB schema + test scaffolds** - `2e70346` (feat)
2. **Task 2: BankStatementParser implementation** - `a0f0e08` (feat)
3. **Task 3: PipelineA.process_folder() implementation** - `ec03f72` (feat)

## Files Created/Modified
- `accounting/db.py` - Added iban_coa_mapping + movimenti_bancari tables, get_iban_coa_mapping(), save_iban_coa_mapping(), salva_movimento_bancario()
- `pipeline/csv_bank_parser.py` - New: BankMovement dataclass, _parse_italian_decimal(), BankStatementParser with full Italian CSV support
- `pipeline/pipeline_a.py` - Replaced stub: full PipelineA.process_folder() + InvoiceResult, BankMovementResult, PipelineResult dataclasses
- `pipeline/__init__.py` - Added exports for BankStatementParser, BankMovement, InvoiceResult, BankMovementResult, PipelineResult
- `tests/test_pipeline_a.py` - New: TestDBSchema, TestIBANMapping, TestBankMovementSave (GREEN), TestInvoicePipeline, TestDeduplication
- `tests/test_bank_parser.py` - New: TestItalianDecimalParsing, TestFormatDetection, TestBankStatementParser, TestCanonicalCSV, TestOFXStub
- `tests/test_scanner.py` - Updated TestPipelineAStub -> TestPipelineAImport (removed NotImplementedError test)

## Decisions Made
- `db_path` optional parameter added to `process_folder()` for test isolation without monkeypatching — TestDeduplication passes a tmp_path DB to avoid touching production DB.
- `_detect_header_row()` requires both keyword match in header row AND date pattern in the following row — prevents false positives on metadata rows that happen to contain "Data".
- Accrediti/Addebiti detection takes precedence over single Importo column — more specific match wins.
- Zero importo movements produce a GENERICO registrazione with a single row (non-bilanciata by design) — these are informational only.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Updated test_scanner.py to remove now-invalid stub test**
- **Found during:** Task 3 (PipelineA implementation)
- **Issue:** `TestPipelineAStub::test_process_folder_raises_not_implemented` expected `NotImplementedError` from `process_folder(tmp_path)`. After replacing the stub with the real implementation, this test would fail with a different error (wrong argument type for `scan_result`).
- **Fix:** Replaced `TestPipelineAStub` with `TestPipelineAImport` that tests the import contract (`PipelineA`, `InvoiceResult`, `PipelineResult` all importable). The old stub test is no longer meaningful.
- **Files modified:** `tests/test_scanner.py`
- **Verification:** `pytest tests/ -x -q` passes all 82 tests
- **Committed in:** `ec03f72` (Task 3 commit)

---

**Total deviations:** 1 auto-fixed (Rule 1 - Bug)
**Impact on plan:** Required for test suite correctness — old test validated stub behavior that no longer exists.

## Issues Encountered
None — implementation matched plan spec exactly. The `_detect_header_row` heuristic was designed carefully to handle both zero-metadata and multi-row-metadata CSV formats.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- All four PIPE requirements (PIPE-01..04) have backend logic and passing tests
- InvoiceResult/BankMovementResult dataclasses ready for consumption by 04-02 UI plan
- IBAN-CoA mapping table exists and is queryable — UI can expose mapping editor
- No blockers

---
*Phase: 04-pipeline-a-ingestion*
*Completed: 2026-03-20*
