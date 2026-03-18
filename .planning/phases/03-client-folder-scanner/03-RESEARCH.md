# Phase 3: Client Folder Scanner - Research

**Researched:** 2026-03-18
**Domain:** Python pathlib (rglob), Streamlit session state / sidebar UX, XML content peek
**Confidence:** HIGH

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- Folder selector lives in the **sidebar**, below the navigation buttons: a `st.text_input` for the
  path + a `Scansiona` button
- The sidebar selector is always visible regardless of current page — user can switch clients from
  anywhere
- Clicking `Scansiona` sets `current_page = 'scanner'` and navigates to the Scanner page
- Scanner is a **new page** added to `app.py` routing and to the sidebar nav list (between
  Configurazione and Fatture)
- Scanning is **always recursive** (`rglob`) — no configuration checkbox needed; client folders
  typically have `fatture/`, `estratti_conto/`, `contratti/` subdirectories
- Classification uses **content peek**: read the first ~200 bytes of each `.xml` file and check
  whether the root element is `FatturaElettronica` — reuse existing logic from
  `core/file_processors.py` (already implemented there)
- A generic `.xml` file that is NOT FatturaPA goes into the `Altro` category, not `FatturaXML`
- Six categories as required by SCAN-01: FatturaXML, PDF, CSV, DOCX, TXT, Altro
- Scanner page layout: **summary metric cards** at the top (one `st.metric` per non-empty
  category), then **`st.expander` per category** listing filenames + file sizes
- The FatturaXML expander opens by default (`expanded=True`); others start collapsed
- Each file entry shows: filename, size in KB, relative path within the client folder
- After scanning, the Scanner page shows a prominent **CTA button**: `▶ Avvia elaborazione (N
  fatture)` where N = number of FatturaXML files found
- The button calls `pipeline_a.process_folder(client_folder)` — **stub defined in Phase 3**,
  fully implemented in Phase 4
- "Automatic" means no manual file selection required — the user confirms once with the button,
  not file by file
- Scan results are stored in `st.session_state['scan_results']` (a dict keyed by category,
  values are lists of `Path` objects); cleared and replaced on each new scan
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

### Deferred Ideas (OUT OF SCOPE)
- Recent folders list (last 5 used) — Phase 3 is single-folder only; multi-client quick-switch
  deferred to a later milestone when multiple accountants or large client rosters are in scope
- Scan filtering (exclude hidden files, gitignore patterns) — not needed for v1 client folders
- Pipeline B auto-trigger (for PDF/DOCX documents) — Pipeline B is milestone 2
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| SCAN-01 | `scanner/client_folder_scanner.py` returns structured file list classified into FatturaXML, PDF, CSV, DOCX, TXT, Altro | `pathlib.rglob("*")` + extension dispatch + XML content peek (lxml already in requirements); `ScanResult` dataclass keyed by category |
| SCAN-02 | User selects client folder from Streamlit sidebar; app shows classified file list without writing code | `st.text_input` + `st.button` in sidebar (exact pattern already in `app.py` for Ollama URL); `st.metric` + `st.expander` in `ui/pages/scanner.py` (pattern in `onboarding.py`) |
| SCAN-03 | After scan, Pipeline A starts automatically for FatturaXML files — user confirms once via CTA button | Stub `pipeline/pipeline_a.py` exposes `process_folder(client_folder: Path)`; Scanner page renders CTA button gated on `len(scan_results["FatturaXML"]) > 0` |
</phase_requirements>

---

## Summary

Phase 3 is a pure Python + Streamlit UI exercise — no new external dependencies are required. All
tools are already in `requirements.txt` (pathlib is stdlib, lxml is already installed for FatturaPA
parsing, Streamlit is the existing UI framework).

The core component is `ClientFolderScanner`, a simple class that walks a directory tree with
`Path.rglob("*")`, dispatches each file by extension into one of six categories, and performs a
cheap 200-byte content peek for `.xml` files to distinguish FatturaPA from generic XML. The peek
logic is already implemented in `core/file_processors.py` (`extract_text_from_xml`) and only needs
to be extracted into a lightweight classification helper — no full parsing, no content extraction.

The Streamlit integration follows patterns already established in the codebase. The sidebar folder
selector mirrors the existing Ollama URL `st.text_input` in `app.py`. The Scanner page result
display mirrors the `st.metric` + `st.expander` pattern already used in `onboarding.py`. The
Pipeline A stub is a single-function module that satisfies SCAN-03 without implementing any
processing logic (that is Phase 4's job).

**Primary recommendation:** Implement `ClientFolderScanner` as a pure Python dataclass-based
module with no Streamlit coupling; keep all rendering in `ui/pages/scanner.py`. Wire sidebar and
routing in `app.py` following the exact patterns already present.

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| pathlib (stdlib) | Python 3.12+ | Recursive directory walking (`rglob`), Path objects | Already used throughout codebase; zero-cost |
| lxml | >=5.0.0 | XML root-tag peek for FatturaPA detection | Already in requirements; fastest XML parser in Python |
| streamlit | >=1.28.0 | Sidebar widgets, `st.metric`, `st.expander`, `st.rerun()` | Already the UI framework |
| pyyaml | >=6.0 | Persist `client_folder_path` to `data/config.yaml` | Already used by `config/settings.py` |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| xml.etree.ElementTree (stdlib) | Python 3.12+ | Fallback XML peek if lxml unavailable | Already used as fallback in `extract_text_from_xml` |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| `rglob("*")` + manual filter | `os.walk()` | `rglob` is more idiomatic with Path objects and already the pattern in `local_folder.py`; `os.walk()` adds no benefit here |
| lxml for content peek | Read raw bytes + regex | Raw bytes + `b'FatturaElettronica'` search is simpler for a 200-byte peek and avoids full XML parse; see Code Examples section |

**Installation:** No new packages needed. All dependencies already in `requirements.txt`.

## Architecture Patterns

### Recommended Project Structure
```
scanner/
├── __init__.py              # exports ClientFolderScanner, ScanResult
└── client_folder_scanner.py # ClientFolderScanner class + ScanResult dataclass

pipeline/
├── __init__.py              # exports PipelineA
└── pipeline_a.py            # PipelineA stub — process_folder() interface only

ui/pages/
└── scanner.py               # render_scanner() — all Streamlit rendering logic
```

### Pattern 1: ScanResult Dataclass Keyed by Category

**What:** A `ScanResult` dataclass holds a dict mapping category name to list of `Path` objects,
plus a `client_folder` reference for computing relative paths in the UI.

**When to use:** This structure is consumed directly by the Scanner page — each category key maps
to one `st.expander`.

**Example:**
```python
# scanner/client_folder_scanner.py
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List

CATEGORIES = ["FatturaXML", "PDF", "CSV", "DOCX", "TXT", "Altro"]

@dataclass
class ScanResult:
    client_folder: Path
    files: Dict[str, List[Path]] = field(
        default_factory=lambda: {cat: [] for cat in CATEGORIES}
    )

    def total(self) -> int:
        return sum(len(v) for v in self.files.values())

    def count(self, category: str) -> int:
        return len(self.files.get(category, []))
```

### Pattern 2: FatturaXML Content Peek Without Full Parse

**What:** Read only the first 512 bytes of an XML file as raw bytes and search for the
`FatturaElettronica` tag. This avoids a full XML parse during scanning (which would be slow on
large folders) while being accurate enough for classification.

**When to use:** For every `.xml` file encountered during `rglob`.

**Example:**
```python
# scanner/client_folder_scanner.py — classification helper

def _is_fattura_xml(path: Path) -> bool:
    """
    Returns True if the file is a FatturaPA XML.
    Reads first 512 bytes only — no full parse.
    """
    try:
        with open(path, "rb") as f:
            header = f.read(512)
        return b"FatturaElettronica" in header
    except OSError:
        return False
```

This approach is consistent with the pattern already used in `core/file_processors.py` lines
156-158, where `etree.QName(root.tag).localname` is checked — but our version is cheaper because
it skips lxml entirely for the scanner's classification step.

### Pattern 3: Extension-Based Category Dispatch

**What:** A mapping from file extension to category string used in the scanner loop.

**Example:**
```python
# scanner/client_folder_scanner.py

_EXT_TO_CATEGORY: Dict[str, str] = {
    ".pdf":  "PDF",
    ".csv":  "CSV",
    ".docx": "DOCX",
    ".txt":  "TXT",
    # .xml handled separately via content peek
}

def _classify(path: Path) -> str:
    ext = path.suffix.lower()
    if ext == ".xml":
        return "FatturaXML" if _is_fattura_xml(path) else "Altro"
    return _EXT_TO_CATEGORY.get(ext, "Altro")
```

### Pattern 4: ClientFolderScanner.scan() Method

**What:** The main entry point. Returns a `ScanResult`. Skips hidden files (dot-prefixed).

**Example:**
```python
class ClientFolderScanner:
    def scan(self, folder: Path) -> ScanResult:
        result = ScanResult(client_folder=folder)
        if not folder.exists() or not folder.is_dir():
            return result  # empty result; caller checks total() == 0
        for path in sorted(folder.rglob("*")):
            if path.is_file() and not path.name.startswith("."):
                category = _classify(path)
                result.files[category].append(path)
        return result
```

### Pattern 5: Sidebar Folder Selector (app.py integration)

**What:** Insert the folder selector into the existing `with st.sidebar:` block, between the nav
buttons section and the LLM config expander. Follow the exact pattern of the Ollama URL
`st.text_input` already in place.

**Example:**
```python
# app.py — inside `with st.sidebar:` block, after nav buttons section

st.markdown("---")
st.markdown("### Cartella Cliente")
folder_input = st.text_input(
    "Percorso cartella",
    value=st.session_state.get("client_folder_path", ""),
    placeholder="/home/user/clienti/rossi_srl",
    key="sidebar_folder_input",
    label_visibility="collapsed",
)
if st.button("Scansiona", use_container_width=True, type="primary"):
    st.session_state["client_folder_path"] = folder_input
    # Persist to config.yaml
    from config.settings import load_company_config, save_company_config
    cfg = load_company_config()
    cfg["client_folder_path"] = folder_input
    save_company_config(cfg)
    # Run scan
    from scanner.client_folder_scanner import ClientFolderScanner
    scanner = ClientFolderScanner()
    result = scanner.scan(Path(folder_input))
    st.session_state["scan_results"] = result
    st.session_state["current_page"] = "scanner"
    st.rerun()
```

### Pattern 6: Pipeline A Stub

**What:** A minimal stub module that defines the interface Pipeline A will implement in Phase 4.
It must exist so `scanner.py` can import it without errors. It must NOT raise on import.

**Example:**
```python
# pipeline/pipeline_a.py

from pathlib import Path


class PipelineA:
    """
    Pipeline A — ingestion of FatturaXML files.
    Full implementation in Phase 4.
    This stub satisfies the import contract required by the Scanner page CTA.
    """

    def process_folder(self, client_folder: Path) -> None:
        """
        Placeholder. Phase 4 will implement:
        - Find all FatturaXML in scan_results
        - Parse via FatturaPAParser
        - Generate prima nota suggestions
        - Store results for UI review
        """
        raise NotImplementedError(
            "PipelineA.process_folder() is not yet implemented. "
            "See Phase 4 for full implementation."
        )
```

### Pattern 7: Scanner Page render_scanner()

**What:** Full rendering of the Scanner page, consuming `st.session_state['scan_results']`.

**Example:**
```python
# ui/pages/scanner.py

import streamlit as st
from pathlib import Path


def render_scanner():
    st.title("Scanner Cartella Cliente")

    scan_result = st.session_state.get("scan_results")
    if scan_result is None:
        st.info("Nessuna scansione eseguita. Seleziona una cartella dalla barra laterale.")
        return

    # Summary metric cards — one per non-empty category
    categories_with_files = [
        (cat, scan_result.count(cat))
        for cat in ["FatturaXML", "PDF", "CSV", "DOCX", "TXT", "Altro"]
        if scan_result.count(cat) > 0
    ]
    if not categories_with_files:
        st.warning("Nessun file trovato nella cartella selezionata.")
        return

    cols = st.columns(len(categories_with_files))
    for col, (cat, count) in zip(cols, categories_with_files):
        col.metric(cat, count)

    st.caption(f"Totale: {scan_result.total()} file — {scan_result.client_folder}")

    # CTA button for Pipeline A
    n_fatture = scan_result.count("FatturaXML")
    if n_fatture > 0:
        if st.button(f"Avvia elaborazione ({n_fatture} fatture)", type="primary"):
            from pipeline.pipeline_a import PipelineA
            try:
                PipelineA().process_folder(scan_result.client_folder)
            except NotImplementedError as e:
                st.warning(f"Pipeline A non ancora implementata (Phase 4). {e}")
    else:
        st.info("Nessun file FatturaXML trovato. Pipeline A non disponibile.")

    st.divider()

    # Expanders per category
    for cat in ["FatturaXML", "PDF", "CSV", "DOCX", "TXT", "Altro"]:
        files = scan_result.files.get(cat, [])
        if not files:
            continue
        with st.expander(f"{cat} ({len(files)})", expanded=(cat == "FatturaXML")):
            for f in files:
                size_kb = f.stat().st_size / 1024
                rel = f.relative_to(scan_result.client_folder)
                st.text(f"{f.name}  |  {size_kb:.1f} KB  |  {rel.parent}")
```

### Anti-Patterns to Avoid

- **Calling lxml in the scan loop:** Full XML parse of every file during scanning is 10-100x
  slower than a raw byte search. Classification must be a content peek only, not a full parse.
- **Storing file content in scan_results:** `scan_results` must hold only `Path` objects and
  metadata (size). Content extraction happens in Pipeline A, not the scanner.
- **Running scan inside a Streamlit form:** `st.form` delays state writes until submission and
  prevents `st.rerun()` calls mid-form. The sidebar folder selector uses individual `st.button`,
  not `st.form`.
- **Importing `ui/pages/scanner.py` in `ClientFolderScanner`:** The scanner module must have
  zero Streamlit dependency. It is a pure Python class that can be imported and tested without
  Streamlit.
- **Raising exceptions from scan():** If the folder path is invalid, return an empty `ScanResult`.
  Let the UI render the appropriate error via `st.error()`. Never raise from the scanner.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Recursive directory walk | Custom `os.walk` + manual filter | `Path.rglob("*")` | Already the pattern in `rag/adapters/local_folder.py`; cleaner with Path objects |
| XML root detection | Full parse to identify FatturaPA | 512-byte raw bytes search for `b"FatturaElettronica"` | Content peek already proven in `core/file_processors.py`; 100x faster than lxml parse |
| File size formatting | Custom bytes → KB converter | `path.stat().st_size / 1024` | One-liner; no library needed |
| Sidebar state | Custom state class | `st.session_state` dict | Already the pattern for all app state |
| Config persistence | Custom file format | Existing `save_company_config()` pattern with `pyyaml` | One new key in existing YAML file; no schema change |

**Key insight:** Every piece of infrastructure this phase needs already exists in the codebase.
The entire phase is wiring together existing utilities plus minimal new code.

## Common Pitfalls

### Pitfall 1: st.rerun() Called Outside Button Callback
**What goes wrong:** If `st.rerun()` is called unconditionally (not inside an `if st.button(...):`
block), the app enters an infinite rerun loop.
**Why it happens:** Streamlit re-executes the entire script on every rerun; `st.rerun()` outside
a conditional triggers it again immediately.
**How to avoid:** Always gate `st.rerun()` inside `if st.button(...):` or `if st.form_submit_button(...):`.
**Warning signs:** Browser tab freezes or Streamlit shows "rerunning" indefinitely.

### Pitfall 2: Session State Key Written in Sidebar, Read in Page Before Rerun
**What goes wrong:** The sidebar writes `st.session_state["scan_results"]` and immediately renders
the scanner page in the same script run — but the page renders before `st.rerun()` fires, showing
stale state.
**Why it happens:** Streamlit executes top to bottom; the routing block at the bottom of `app.py`
runs in the same pass as the sidebar block.
**How to avoid:** After writing to session_state in the sidebar button handler, call `st.rerun()`
so the next pass picks up the new state.

### Pitfall 3: Path.relative_to() Raises ValueError
**What goes wrong:** `file.relative_to(client_folder)` raises `ValueError` if the file is not
actually inside `client_folder` (e.g. symlinks pointing outside the tree).
**Why it happens:** `relative_to()` does a pure prefix check on the path string, not filesystem
resolution.
**How to avoid:** Wrap in a try/except when computing relative paths for display:
```python
try:
    rel = f.relative_to(scan_result.client_folder)
except ValueError:
    rel = f  # show absolute path as fallback
```

### Pitfall 4: Binary Files Misclassified as TXT
**What goes wrong:** Files with no recognised extension fall into `Altro`, but files ending in
`.txt` that are actually binary (e.g. mislabeled exports) will be listed as TXT.
**Why it happens:** The classifier uses extension only for non-XML files.
**How to avoid:** For this phase, extension-based classification is acceptable per SCAN-01 spec.
No binary detection is required. Document this as a known limitation.

### Pitfall 5: stat() Called on Path That No Longer Exists
**What goes wrong:** `f.stat().st_size` raises `FileNotFoundError` if a file is deleted between
scan time and render time.
**Why it happens:** The scan result caches `Path` objects, not stat results. The file system can
change between scan and display.
**How to avoid:** Wrap `f.stat()` in try/except in `render_scanner()`:
```python
try:
    size_kb = f.stat().st_size / 1024
except OSError:
    size_kb = 0.0
```

### Pitfall 6: CSV Category Missing from SUPPORTED_EXTENSIONS
**What goes wrong:** `config/constants.py` `SUPPORTED_EXTENSIONS` dict does not list `.csv`.
The scanner's `_EXT_TO_CATEGORY` mapping must define it independently.
**Why it happens:** CSV files are not used in the RAG pipeline, so they were not added to the
constants file.
**How to avoid:** The scanner defines its own `_EXT_TO_CATEGORY` dict in
`scanner/client_folder_scanner.py`. It does not read from `SUPPORTED_EXTENSIONS`.

## Code Examples

Verified patterns from existing codebase:

### Existing rglob Pattern (from rag/adapters/local_folder.py, lines 68-72)
```python
# Source: rag/adapters/local_folder.py
if self.recursive:
    files = []
    for ext in self.extensions:
        files.extend(folder.rglob(f"*{ext}"))
```
The scanner uses `rglob("*")` instead (walk everything, filter by suffix) to gather all files in
one pass rather than one pass per extension.

### Existing XML Root Check (from core/file_processors.py, lines 155-158)
```python
# Source: core/file_processors.py
from lxml import etree
root = etree.fromstring(file_bytes)
local_name = etree.QName(root.tag).localname if root.tag.startswith('{') else root.tag
if local_name == "FatturaElettronica":
    ...
```
The scanner replaces this with a raw byte search to avoid loading lxml per file during scanning.

### Existing config.yaml Persist Pattern (from config/settings.py, lines 76-86)
```python
# Source: config/settings.py
def save_company_config(config: Dict[str, Any]) -> bool:
    with open(COMPANY_CONFIG_FILE, "w", encoding="utf-8") as f:
        yaml.dump(config, f, allow_unicode=True, default_flow_style=False)
    return True
```
Phase 3 adds `client_folder_path` as a new top-level key. No schema change needed:
`load_company_config()` already merges with `_DEFAULT_COMPANY_CONFIG` using `{**defaults, **config}`,
so new keys round-trip transparently.

### Existing Sidebar Pattern (from app.py, lines 421-428)
```python
# Source: app.py
ollama_url = st.text_input(
    "URL Ollama",
    value=st.session_state.get("ollama_base_url", OLLAMA_BASE_URL),
    key="ollama_url_input",
)
if ollama_url != st.session_state.get("ollama_base_url"):
    st.session_state["ollama_base_url"] = ollama_url
```
The folder selector follows this same `st.text_input` + state-write pattern, but adds a dedicated
`st.button("Scansiona")` rather than reacting to input changes.

### Existing Metric + Expander Pattern (from ui/pages/onboarding.py, lines 203-208)
```python
# Source: ui/pages/onboarding.py
col1, col2, col3 = st.columns(3)
col1.metric("Documenti", stats.get("document_count", 0))
col2.metric("Chunk", stats.get("chunk_count", 0))
col3.metric("Dimensione", f"{stats.get('total_chars', 0):,} chars")
```
The Scanner page uses the same pattern for category totals, using dynamic column count based on
non-empty categories.

### Page Routing Pattern (from app.py, lines 380-386)
```python
# Source: app.py
if st.button(
    f"{icon} {label}",
    key=f"nav_{page_id}",
    use_container_width=True,
    type="primary" if st.session_state.get("current_page") == page_id else "secondary",
):
    st.session_state["current_page"] = page_id
    st.rerun()
```
The `scanner` page entry is added to the `pages` dict. The `Scansiona` sidebar button also sets
`current_page = "scanner"` before `st.rerun()`.

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `os.walk()` + string join | `pathlib.Path.rglob("*")` | Python 3.4+ | Already used in project; `Path` objects are first-class |
| Full XML parse for type detection | 512-byte content peek | — | 10-100x faster for scan-time classification |

**Deprecated/outdated:**
- PyPDF2: already replaced with pypdf in Phase 1 — not relevant to this phase
- LangChain: already removed in Phase 1 — not relevant to this phase

## Open Questions

1. **CSV classification false positives**
   - What we know: `.csv` extension maps to CSV category by convention
   - What's unclear: Some accounting software exports TSV files with `.csv` extension, or Excel
     exports as `.csv` with semicolon delimiter. The scanner classifies by extension only.
   - Recommendation: Accept this for v1 — the scanner's job is classification, not validation.
     Pipeline A (Phase 4) will handle format detection when it actually reads the file.

2. **Very large client folders (thousands of files)**
   - What we know: `rglob("*")` is synchronous and blocks the Streamlit thread during scanning
   - What's unclear: How large the largest real client folder will be in practice
   - Recommendation: For Phase 3, synchronous scan is acceptable (typical accounting folders
     have dozens to hundreds of files). If performance becomes an issue in Phase 4+, wrap in
     `st.spinner("Scansione in corso...")` which is already standard in the codebase.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest (collected at `/home/admaiora/.local/bin/pytest`) |
| Config file | `conftest.py` (project root — adds root to sys.path) |
| Quick run command | `/home/admaiora/.local/bin/pytest tests/test_scanner.py -x -q` |
| Full suite command | `/home/admaiora/.local/bin/pytest tests/ -q` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| SCAN-01 | `ClientFolderScanner.scan()` returns `ScanResult` with correct category keys | unit | `/home/admaiora/.local/bin/pytest tests/test_scanner.py::TestClientFolderScanner -x -q` | Wave 0 |
| SCAN-01 | FatturaXML files (with `FatturaElettronica` header) classified as FatturaXML | unit | `/home/admaiora/.local/bin/pytest tests/test_scanner.py::TestClassification::test_fattura_xml_classified -x -q` | Wave 0 |
| SCAN-01 | Generic XML (no FatturaElettronica) classified as Altro | unit | `/home/admaiora/.local/bin/pytest tests/test_scanner.py::TestClassification::test_generic_xml_to_altro -x -q` | Wave 0 |
| SCAN-01 | CSV, PDF, DOCX, TXT each go to their correct categories | unit | `/home/admaiora/.local/bin/pytest tests/test_scanner.py::TestClassification::test_extension_dispatch -x -q` | Wave 0 |
| SCAN-01 | Scanning non-existent folder returns empty ScanResult (no raise) | unit | `/home/admaiora/.local/bin/pytest tests/test_scanner.py::TestScannerEdgeCases::test_missing_folder -x -q` | Wave 0 |
| SCAN-01 | Recursive scan finds files in subdirectories | unit | `/home/admaiora/.local/bin/pytest tests/test_scanner.py::TestClientFolderScanner::test_recursive -x -q` | Wave 0 |
| SCAN-02 | `render_scanner()` is importable without Streamlit runtime errors | import smoke | manual — Streamlit UI not testable in pytest | manual-only |
| SCAN-03 | `pipeline_a.PipelineA.process_folder()` raises `NotImplementedError` (stub contract) | unit | `/home/admaiora/.local/bin/pytest tests/test_scanner.py::TestPipelineAStub -x -q` | Wave 0 |
| SCAN-03 | `pipeline_a` module is importable without errors | unit | `/home/admaiora/.local/bin/pytest tests/test_scanner.py::TestPipelineAStub::test_import -x -q` | Wave 0 |

Note: SCAN-02 (Streamlit sidebar/page rendering) is manual-only — `render_scanner()` and the
sidebar block cannot be exercised in pytest without a running Streamlit server.

### Sampling Rate
- **Per task commit:** `/home/admaiora/.local/bin/pytest tests/test_scanner.py -x -q`
- **Per wave merge:** `/home/admaiora/.local/bin/pytest tests/ -q`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/test_scanner.py` — covers SCAN-01 (scanner classification), SCAN-03 (pipeline stub)
- [ ] No new conftest.py or fixture changes needed — existing `conftest.py` already handles sys.path

## Sources

### Primary (HIGH confidence)
- Direct codebase read: `core/file_processors.py` — existing XML content peek and extension helpers
- Direct codebase read: `app.py` — existing sidebar patterns, nav routing, session_state patterns
- Direct codebase read: `config/settings.py` — existing `load_company_config` / `save_company_config`
- Direct codebase read: `rag/adapters/local_folder.py` — existing `rglob` pattern
- Direct codebase read: `swarm/context.py` — `client_folder: Path` field already defined
- Direct codebase read: `ui/pages/onboarding.py` — `st.metric` + `st.expander` pattern
- Direct codebase read: `config/constants.py` — `SUPPORTED_EXTENSIONS`, `FATTURE_DIR`, `DOCUMENTI_DIR`
- Direct codebase read: `tests/test_swarm_foundation.py` — test style conventions for this project
- Python stdlib docs: `pathlib.Path.rglob` — standard since Python 3.5

### Secondary (MEDIUM confidence)
- Streamlit docs pattern (verified in codebase): `st.session_state`, `st.rerun()`, `st.expander(expanded=True)`

### Tertiary (LOW confidence)
- None

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all libraries already in use in the project
- Architecture: HIGH — patterns verified directly in existing codebase files
- Pitfalls: HIGH — derived from reading actual Streamlit execution model and existing code

**Research date:** 2026-03-18
**Valid until:** 2026-06-18 (stable libraries, no fast-moving ecosystem)
