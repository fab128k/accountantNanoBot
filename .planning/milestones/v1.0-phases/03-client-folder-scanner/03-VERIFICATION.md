---
phase: 03-client-folder-scanner
verified: 2026-03-19T10:30:00Z
status: human_needed
score: 12/12 must-haves verified
human_verification:
  - test: "Sidebar folder selector visible on every page"
    expected: "st.text_input + Scansiona button visible in sidebar regardless of which page is active"
    why_human: "Streamlit runtime required — sidebar rendering cannot be tested in pytest"
  - test: "Scansiona button navigates to Scanner page and shows metric cards"
    expected: "After entering a folder path and clicking Scansiona, app navigates to Scanner page and shows one st.metric per non-empty category"
    why_human: "Streamlit session_state + st.rerun() behavior cannot be verified without a running app"
  - test: "FatturaXML expander opens by default, others collapsed"
    expected: "On Scanner page, FatturaXML expander is expanded=True; PDF/CSV/DOCX/TXT/Altro expanders start collapsed"
    why_human: "Streamlit expander expanded state is a runtime visual property"
  - test: "CTA button shows warning when clicked (Pipeline A stub)"
    expected: "Clicking 'Avvia elaborazione (N fatture)' triggers st.warning about Pipeline A not yet implemented (Phase 4)"
    why_human: "Button interaction and st.warning display require Streamlit runtime"
  - test: "Folder path persists across app restart"
    expected: "After restarting streamlit run app.py, the previously entered folder path is restored in the sidebar text input"
    why_human: "config.yaml persistence + session_state restoration requires full app lifecycle to verify"
---

# Phase 3: Client Folder Scanner — Verification Report

**Phase Goal:** Implement the Client Folder Scanner — a module that scans a local client folder, classifies files by type, and exposes a Streamlit UI for folder selection and ingestion trigger.
**Verified:** 2026-03-19T10:30:00Z
**Status:** human_needed
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths (Plan 01 — Scanner Core)

| # | Truth | Status | Evidence |
|---|-------|--------|---------|
| 1 | ClientFolderScanner.scan(folder) returns a ScanResult with files grouped into six categories: FatturaXML, PDF, CSV, DOCX, TXT, Altro | VERIFIED | `scanner/client_folder_scanner.py` lines 10+82-97; 12/12 tests pass |
| 2 | An XML file containing FatturaElettronica in its first 512 bytes is classified as FatturaXML; other XML files go to Altro | VERIFIED | `_is_fattura_xml()` line 42: `b"FatturaElettronica" in header`; `_classify()` line 66 dispatches .xml; test_fattura_xml_classified + test_generic_xml_to_altro pass |
| 3 | Scanning a non-existent folder returns an empty ScanResult (no exception raised) | VERIFIED | `scan()` line 91: `if not folder.exists() or not folder.is_dir(): return result`; test_missing_folder passes |
| 4 | Scanning is recursive — files in subdirectories are found | VERIFIED | `folder.rglob("*")` line 93; test_recursive passes (subdir/invoice.xml found) |
| 5 | PipelineA.process_folder() exists as a stub that raises NotImplementedError | VERIFIED | `pipeline/pipeline_a.py` line 27: `raise NotImplementedError(...)`; test_process_folder_raises_not_implemented passes |

### Observable Truths (Plan 02 — Scanner UI)

| # | Truth | Status | Evidence |
|---|-------|--------|---------|
| 6 | User can enter a folder path in the sidebar and click Scansiona from any page | VERIFIED (automated) + ? HUMAN | `app.py` line 418: `st.button("Scansiona"...)`; sidebar block present in `_render_sidebar()`; runtime behavior needs human |
| 7 | After clicking Scansiona, app navigates to Scanner page and shows classified file counts as metric cards | VERIFIED (automated) + ? HUMAN | `app.py` lines 429-432: scans + sets scan_results + sets current_page="scanner" + st.rerun(); `scanner.py` lines 28-30: metric cols; runtime needs human |
| 8 | Each non-empty category has an st.expander listing filenames, sizes in KB, and relative paths | VERIFIED (automated) + ? HUMAN | `scanner.py` lines 53-67: expanders with f.stat().st_size/1024 and f.relative_to(); runtime needs human |
| 9 | FatturaXML expander opens by default; other expanders start collapsed | VERIFIED (automated) + ? HUMAN | `scanner.py` line 57: `expanded=(cat == "FatturaXML")`; runtime visual behavior needs human |
| 10 | CTA button 'Avvia elaborazione (N fatture)' appears when FatturaXML files exist | VERIFIED (automated) + ? HUMAN | `scanner.py` lines 36-46: `if n_fatture > 0: st.button(f"Avvia elaborazione ({n_fatture} fatture)"...)`; runtime needs human |
| 11 | Clicking the CTA calls PipelineA.process_folder() and shows warning that it is not yet implemented | VERIFIED (automated) + ? HUMAN | `scanner.py` lines 42-46: imports PipelineA, calls process_folder, catches NotImplementedError with st.warning; runtime needs human |
| 12 | The folder path is persisted to data/config.yaml and restored on app restart | VERIFIED (automated) + ? HUMAN | `app.py` lines 78-90: restores from config + initializes sidebar_folder_input; lines 420-427: saves via save_company_config; persistence across restart needs human |

**Score:** 12/12 truths have evidence in code; 5 require human runtime verification for full confidence.

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|---------|--------|---------|
| `scanner/client_folder_scanner.py` | ClientFolderScanner + ScanResult + _classify + _is_fattura_xml + CATEGORIES | VERIFIED | 98 lines; all 5 expected exports present; no stubs |
| `scanner/__init__.py` | Re-exports ClientFolderScanner, ScanResult | VERIFIED | Lines 4-6: `from .client_folder_scanner import ClientFolderScanner, ScanResult` |
| `pipeline/pipeline_a.py` | PipelineA stub with process_folder raising NotImplementedError | VERIFIED | 31 lines; raises NotImplementedError with Phase 4 message; does not raise on import |
| `pipeline/__init__.py` | Re-exports PipelineA | VERIFIED | Lines 4-6: `from .pipeline_a import PipelineA` |
| `tests/test_scanner.py` | 12+ unit tests covering all behaviors | VERIFIED | 160 lines; 12 test methods; 4 test classes; all pass |
| `ui/pages/scanner.py` | render_scanner() function — full Scanner page renderer | VERIFIED | 68 lines (>50 min); render_scanner() present; all expected elements present |
| `app.py` | Sidebar folder selector, scanner nav, routing, session state | VERIFIED | All 4 integration points confirmed (session state, pages dict, sidebar, routing) |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `scanner/client_folder_scanner.py` | `pathlib.Path.rglob` | `folder.rglob("*")` in scan() | WIRED | Line 93: `for path in sorted(folder.rglob("*"))` |
| `scanner/client_folder_scanner.py` | `_is_fattura_xml` | `_classify` dispatches .xml files | WIRED | Line 66: `return "FatturaXML" if _is_fattura_xml(path) else "Altro"` |
| `tests/test_scanner.py` | `scanner/client_folder_scanner.py` | imports and exercises ClientFolderScanner | WIRED | 9 test methods use `from scanner.client_folder_scanner import ClientFolderScanner` |
| `app.py` | `scanner/client_folder_scanner.py` | Scansiona button imports + calls ClientFolderScanner().scan() | WIRED | Lines 421-430: lazy import inside button handler; `scanner.scan(Path(folder_input))` |
| `app.py` | `ui/pages/scanner.py` | routing block imports render_scanner | WIRED | Lines 524-526: `elif current_page == "scanner":` + `from ui.pages.scanner import render_scanner` |
| `ui/pages/scanner.py` | `pipeline/pipeline_a.py` | CTA button imports PipelineA + calls process_folder() | WIRED | Lines 42-44: lazy import inside button handler; catches NotImplementedError |
| `app.py` | `config/settings.py` | Scansiona button saves client_folder_path | WIRED | Lines 420+427: `from config.settings import ... save_company_config`; `save_company_config(cfg)` |
| `app.py` | `st.session_state` | initialize_session_state sets client_folder_path and scan_results defaults | WIRED | Lines 70-71: `"client_folder_path": ""`; `"scan_results": None`; lines 89-91: sidebar_folder_input init |

### Requirements Coverage

| Requirement | Source Plans | Description | Status | Evidence |
|-------------|-------------|-------------|--------|---------|
| SCAN-01 | 03-01-PLAN (primary), 03-02-PLAN | Esiste scanner/client_folder_scanner.py che data una cartella restituisce lista strutturata di file classificati per tipo | SATISFIED | File exists; 6 categories implemented; 8 tests cover classification; all pass |
| SCAN-02 | 03-02-PLAN (primary) | L'utente può selezionare la cartella cliente da UI Streamlit (sidebar); sistema avvia scansione e mostra file per categoria | SATISFIED (needs human confirm) | Sidebar selector wired in app.py; render_scanner() implements metric cards + expanders; runtime visual behavior flagged for human |
| SCAN-03 | 03-01-PLAN + 03-02-PLAN | Dopo la scansione, il sistema avvia automaticamente Pipeline A per i file FatturaXML trovati | SATISFIED — NOTE: "automatic" means single-button CTA (not file-by-file), as defined in 03-CONTEXT.md line 50-51 | PipelineA stub exists; CTA button wired in scanner.py; catches NotImplementedError |

**Note on SCAN-03 wording:** REQUIREMENTS.md says "avvia automaticamente...senza intervento manuale." The implementation requires one CTA button click. This is intentional per 03-CONTEXT.md (line 50-51): "Automatic means no manual file selection required — the user confirms once with the button, not file by file." Phase 4 will implement the actual processing. The stub + CTA satisfies Phase 3's scope of the requirement.

**Orphaned requirements check:** No Phase 3 requirements appear in REQUIREMENTS.md that are not covered by plans 03-01 or 03-02.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| `pipeline/pipeline_a.py` | 27 | `raise NotImplementedError` in `process_folder()` | Info | Intentional stub; documented for Phase 4; CTA catches it and shows user-facing warning |

No unintentional stubs, TODOs, console-only handlers, or empty returns found in any phase 3 file.

No Streamlit imports found in `scanner/` or `pipeline/` packages — confirmed pure Python.

### Human Verification Required

#### 1. Sidebar Folder Selector Visible on All Pages

**Test:** Start the app (`streamlit run app.py`), navigate between Dashboard, Configurazione, Fatture, Prima Nota. On each page, check that the sidebar shows the "Cartella Cliente" section with a text input and "Scansiona" button below the nav buttons.
**Expected:** The folder selector block is visible and interactive on every page.
**Why human:** Streamlit sidebar rendering and widget visibility across page navigation cannot be verified in pytest.

#### 2. Scansiona Button Triggers Navigation and Shows Metric Cards

**Test:** Enter a folder path containing mixed files (e.g. some .pdf, .txt, and one .xml with FatturaElettronica content) in the sidebar text input. Click "Scansiona."
**Expected:** The app navigates to the Scanner page. Metric cards appear at the top showing file counts per non-empty category (e.g. FatturaXML: 1, PDF: 2, TXT: 1).
**Why human:** st.rerun() + session_state update + page navigation require a running Streamlit instance.

#### 3. FatturaXML Expander Open By Default, Others Collapsed

**Test:** With scan results showing multiple categories, observe the expander state on first load of the Scanner page.
**Expected:** FatturaXML expander is open (expanded); PDF, CSV, DOCX, TXT, Altro expanders are collapsed.
**Why human:** Streamlit expander initial state is a runtime visual property.

#### 4. CTA Button Shows Phase 4 Warning

**Test:** With FatturaXML files in scan results, click the "Avvia elaborazione (N fatture)" button.
**Expected:** A yellow st.warning message appears: "Pipeline A non ancora implementata (Phase 4). PipelineA.process_folder() is not yet implemented. See Phase 4 for full implementation."
**Why human:** Button click interaction and st.warning display require Streamlit runtime.

#### 5. Folder Path Persists Across App Restart

**Test:** Enter a folder path, click Scansiona. Stop the app (Ctrl+C). Restart it (streamlit run app.py).
**Expected:** The sidebar text input is pre-populated with the previously entered folder path.
**Why human:** config.yaml write + read cycle across app lifecycle cannot be tested in pytest without mocking the full Streamlit session initialization sequence.

### Gaps Summary

No gaps. All automated checks pass completely:
- 12/12 scanner unit tests green
- 35/35 full test suite green (no regressions)
- All 7 artifacts exist, are substantive (not stubs), and are wired
- All 8 key links confirmed present in code
- All 3 requirements (SCAN-01, SCAN-02, SCAN-03) have implementation evidence
- Zero anti-patterns blocking goal (NotImplementedError in PipelineA is intentional and caught)

Human verification is required for 5 Streamlit runtime behaviors that cannot be tested in pytest. These are UI rendering and interaction behaviors, not structural concerns — the code structure supporting all of them is verified.

---

_Verified: 2026-03-19T10:30:00Z_
_Verifier: Claude (gsd-verifier)_
