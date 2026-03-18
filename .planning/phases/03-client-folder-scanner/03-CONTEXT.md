# Phase 3: Client Folder Scanner - Context

**Gathered:** 2026-03-18
**Status:** Ready for planning

<domain>
## Phase Boundary

Enable the user to point the system at a client folder via the sidebar, scan it automatically
(recursive), see all files classified by type on a dedicated Scanner page, and trigger Pipeline A
processing for FatturaXML files via a prominent CTA button. No accounting logic in this phase.

Pipeline A implementation is Phase 4. Phase 3 defines the trigger interface (stub) and wires the
UI; Phase 4 fills in the processing logic.

</domain>

<decisions>
## Implementation Decisions

### Folder Selection UX
- Folder selector lives in the **sidebar**, below the navigation buttons: a `st.text_input` for the
  path + a `Scansiona` button
- The sidebar selector is always visible regardless of current page — user can switch clients from
  anywhere
- Clicking `Scansiona` sets `current_page = 'scanner'` and navigates to the Scanner page
- Scanner is a **new page** added to `app.py` routing and to the sidebar nav list (between
  Configurazione and Fatture)
- Scanning is **always recursive** (`rglob`) — no configuration checkbox needed; client folders
  typically have `fatture/`, `estratti_conto/`, `contratti/` subdirectories

### FatturaXML Classification
- Classification uses **content peek**: read the first ~200 bytes of each `.xml` file and check
  whether the root element is `FatturaElettronica` — reuse existing logic from
  `core/file_processors.py` (already implemented there)
- A generic `.xml` file that is NOT FatturaPA goes into the `Altro` category, not `FatturaXML`
- Six categories as required by SCAN-01: FatturaXML, PDF, CSV, DOCX, TXT, Altro

### Scan Results Display
- Scanner page layout: **summary metric cards** at the top (one `st.metric` per non-empty
  category), then **`st.expander` per category** listing filenames + file sizes
- The FatturaXML expander opens by default (`expanded=True`); others start collapsed
- Each file entry shows: filename, size in KB, relative path within the client folder

### Pipeline A Auto-trigger (SCAN-03)
- After scanning, the Scanner page shows a prominent **CTA button**: `▶ Avvia elaborazione (N
  fatture)` where N = number of FatturaXML files found
- The button calls `pipeline_a.process_folder(client_folder)` — **stub defined in Phase 3**,
  fully implemented in Phase 4
- "Automatic" means no manual file selection required — the user confirms once with the button,
  not file by file
- Scan results are stored in `st.session_state['scan_results']` (a dict keyed by category,
  values are lists of `Path` objects); cleared and replaced on each new scan

### Client Folder Persistence
- The selected folder path is **persisted to `data/config.yaml`** using the existing
  `save_company_config()` / `load_company_config()` pattern (same file, new key
  `client_folder_path`)
- On app startup, `initialize_session_state()` reads `client_folder_path` from config and
  populates `st.session_state['client_folder_path']`
- Single active folder — overwriting on change; no recent-folders list needed in v1

### Claude's Discretion
- Exact sidebar layout spacing (separator placement, expander label)
- Error state design when folder doesn't exist or has no readable files
- Scanner page header design and empty-state message when no FatturaXML files are found

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Requirements
- `.planning/REQUIREMENTS.md` §Client Folder Scanner — SCAN-01, SCAN-02, SCAN-03 define exact
  acceptance criteria and the six classification categories

### Files to create
- `scanner/client_folder_scanner.py` — new module: ClientFolderScanner class
- `scanner/__init__.py` — module init
- `pipeline/pipeline_a.py` — stub only in Phase 3 (process_folder interface); Phase 4 implements
- `pipeline/__init__.py` — module init

### Files to modify (read before touching)
- `app.py` — add `scanner` to nav and routing; add sidebar folder selector; add
  `client_folder_path` to `initialize_session_state()`; add Scanner page routing block
- `config/settings.py` — extend `load_company_config()` / `save_company_config()` to handle
  `client_folder_path` key (no structural change, just awareness of new key)
- `ui/pages/` — new `scanner.py` page module for the Scanner page renderer

### Files confirmed NOT needing changes
- `core/file_processors.py` — reuse `is_xml_file()`, `extract_text_from_xml()` (content peek),
  `is_document_file()`, `get_file_extension()`; no changes to this file
- `rag/adapters/local_folder.py` — `rglob` pattern is the model; no changes needed, scanner
  implements its own simpler version
- `swarm/context.py` — `client_folder: Path` field already exists; no changes needed

### Project-level context
- `.planning/PROJECT.md` §Constraints — data locality, sequential processing, human-in-the-loop
- `.planning/STATE.md` §Decisions — Phase 2 swarm decisions; ProcessingContext field layout
- `.planning/phases/02-swarm-architecture/02-CONTEXT.md` — ProcessingContext schema and agent
  error-handling contract

No external specs — requirements fully captured in REQUIREMENTS.md and decisions above.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `core/file_processors.py` `is_xml_file()`, `is_document_file()`, `get_file_extension()`:
  extension detection functions — import directly into ClientFolderScanner
- `core/file_processors.py` `extract_text_from_xml()` lines 135-183: already implements root
  element peek for FatturaElettronica detection — replicate the peek logic (read bytes, parse root
  tag) without calling the full extractor (scanner only classifies, doesn't read content)
- `rag/adapters/local_folder.py` `load_documents()`: `rglob` recursive scanning pattern to follow
- `config/settings.py` `load_company_config()` / `save_company_config()`: use as-is to persist
  `client_folder_path` — no changes needed to these functions
- `config/constants.py` `SUPPORTED_EXTENSIONS`, `FATTURE_DIR`, `DOCUMENTI_DIR`: reference for
  category taxonomy and default paths

### Established Patterns
- Sidebar section: `st.text_input` + `st.button` already used for Ollama URL config in app.py
  sidebar — follow same pattern for folder selector
- Page routing: `st.session_state["current_page"] = "scanner"` + `st.rerun()` — same as existing
  nav button pattern
- Lazy init: `st.session_state.get("scan_results")` checked before rendering Scanner page results
- `st.metric` + `st.expander`: used in onboarding.py KB stats section — same component approach
- Error messages: `st.error()`, `st.warning()`, `st.info()` — consistent with rest of app

### Integration Points
- `app.py` `initialize_session_state()`: add `client_folder_path` and `scan_results` defaults
- `app.py` sidebar block: add folder selector section between nav buttons and LLM config expander
- `app.py` routing: add `elif current_page == "scanner":` block importing `render_scanner` from
  `ui/pages/scanner.py`
- `app.py` nav `pages` dict: add `"scanner": ("📁", "Scanner")` entry

</code_context>

<specifics>
## Specific Ideas

- FatturaXML expander opens by default (expanded=True) because that's the primary reason for
  scanning — the user wants to see invoices immediately
- The CTA button label should show the count: "Avvia elaborazione (12 fatture)" — zero cognitive
  load, the user knows exactly what will run

</specifics>

<deferred>
## Deferred Ideas

- Recent folders list (last 5 used) — Phase 3 is single-folder only; multi-client quick-switch
  deferred to a later milestone when multiple accountants or large client rosters are in scope
- Scan filtering (exclude hidden files, gitignore patterns) — not needed for v1 client folders
- Pipeline B auto-trigger (for PDF/DOCX documents) — Pipeline B is milestone 2

</deferred>

---

*Phase: 03-client-folder-scanner*
*Context gathered: 2026-03-18*
