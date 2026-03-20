# Phase 4: Pipeline A Ingestion - Research

**Researched:** 2026-03-20
**Domain:** FatturaPA XML ingestion, CSV bank statement parsing, double-entry bookkeeping suggestion, human review UI
**Confidence:** HIGH (all findings based on direct code inspection of the existing codebase)

---

## Summary

Phase 4 completes the first end-to-end ingestion loop of the system: XML invoices from a scanned client
folder flow through the existing deterministic parser, produce prima nota suggestions, and land in a
human-review UI before being committed to SQLite. Bank statements follow the same pattern with a new
CSV parser.

The good news: almost everything needed already exists. `FatturaPAParser.to_prima_nota_suggestion()`
returns a fully structured dict. `RegistrazionePrimaNota.from_suggestion()` materialises it. `db.py`
has `fattura_gia_importata()` for SHA256 deduplication and `salva_registrazione()` for confirmed saves.
The FatturazioneAgent has `analizza_xml_bytes()` — a pure deterministic path with zero LLM dependency
— which is exactly what a batch pipeline should call.

Phase 4 is primarily integration and UI work, not new algorithm work. The main gaps are: (1) wiring
`PipelineA.process_folder()` to call the parser for every file in `ScanResult.files["FatturaXML"]` and
store results in session_state for review, (2) building `pipeline/bank_statement_parser.py` for CSV/OFX,
(3) adding a `pipeline_a_results` review page/section to the Scanner UI, and (4) adding a lightweight
`iban_coa_mapping` table to SQLite for the IBAN→CoA suggestion feature.

**Primary recommendation:** Implement Pipeline A as a pure-Python in-process function (no threads,
no async) that accumulates `InvoiceResult` and `BankMovementResult` objects into a list stored in
`st.session_state["pipeline_a_results"]`. The Scanner page then renders a review loop over that list.
Processing is fast enough (pure XML parsing) to run synchronously in the Streamlit UI thread for the
batch sizes a single accountant will handle.

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| PIPE-01 | `pipeline/pipeline_a.py` reads all FatturaXML files, parses each via FatturaPAParser, generates prima nota suggestion per invoice | `FatturaPAParser.to_prima_nota_suggestion()` + `RegistrazionePrimaNota.from_suggestion()` already fully implemented. Pipeline only needs to iterate `ScanResult.files["FatturaXML"]` and collect results. |
| PIPE-02 | Already-imported invoices (same SHA256 hash) silently skipped — user sees "already imported" marker, not error | `accounting.db.fattura_gia_importata(xml_bytes)` already implemented. Pipeline calls it per file; result tagged `status="gia_importata"` in the result struct. |
| PIPE-03 | `pipeline/bank_statement_parser.py` parses CSV (data, descrizione, importo, saldo columns) and OFX into structured bank movements | Does not exist yet. Real CSV files use semicolon separator and Italian decimal format (`-25,10`). OFX is low priority (no OFX files found in real client folders). |
| PIPE-04 | System suggests prima nota entry per bank movement using IBAN→CoA mapping; user accepts/corrects before save | IBAN→CoA mapping table does not exist in DB. Needs new `iban_coa_mapping` SQLite table. Suggestion logic is straightforward: debit bank account (C.IV.1), credit/debit counterpart from mapping. |
</phase_requirements>

---

## Existing Code Inventory

Everything listed here is already implemented and tested. Phase 4 must reuse, not rewrite.

### Parsers

**`parsers/fattura_pa.py`** — `FatturaPAParser` + `FatturaPA` dataclass

- `parse_file(xml_path)` → `List[FatturaPA]`
- `parse_bytes(xml_bytes)` → `List[FatturaPA]`
- `to_prima_nota_suggestion(fattura, is_acquisto, company_piva)` → `dict` (ready for `from_suggestion()`)
- `to_text_summary(fattura)` → human-readable string for LLM review
- `FatturaPA` fields used by Phase 4: `numero`, `data`, `cedente.nome_completo`, `cedente.partita_iva`, `cessionario.nome_completo`, `cessionario.partita_iva`, `tipo_documento`, `importo_totale`, `imponibile_totale`, `iva_totale`, `riepilogo_iva`, `pagamenti`, `xml_path`
- Handles both FPR12 (privati) and FPA12 (PA) formats and both namespaced and non-namespaced XML.
- Multi-body XML files: `parse_bytes()` returns one `FatturaPA` per body. Pipeline should use `fatture[0]` for the standard single-body case (matches existing `analizza_xml_bytes()` behaviour).

**Key detail for acquisto/vendita detection:** `to_prima_nota_suggestion()` accepts `company_piva`. When provided, it auto-detects acquisto vs. vendita by comparing `fattura.cedente.partita_iva != company_piva`. Company P.IVA comes from `config/settings.py` → `load_company_config()["partita_iva"]`.

### Accounting

**`accounting/prima_nota.py`** — `RegistrazionePrimaNota` + `RigaPrimaNota` + `TipoRegistrazione`

- `RegistrazionePrimaNota.from_suggestion(suggestion_dict)` → builds a full object from parser output
- `registrazione.is_bilanciata` — True when Σ DARE == Σ AVERE within 0.01 tolerance
- `registrazione.confermata = False` by default — must be set True before `salva_registrazione()`
- `TipoRegistrazione` enum includes: `FATTURA_ACQUISTO`, `FATTURA_VENDITA`, `PAGAMENTO_FORNITORE`, `INCASSO_CLIENTE`, `GENERICO`

**`accounting/piano_dei_conti.py`** — `PIANO_DEI_CONTI` dict + lookup helpers

Accounts relevant to Phase 4:

| Code | Name | Type |
|------|------|------|
| `C.II.1` | Crediti verso clienti | Attivo (D) |
| `C.II.4-bis` | IVA a credito | Attivo (D) |
| `C.IV.1` | Depositi bancari e postali | Attivo (D) |
| `C.IV.3` | Denaro e valori in cassa | Attivo (D) |
| `D.7` | Debiti verso fornitori | Passivo (A) |
| `D.12` | IVA a debito | Passivo (A) |
| `A.1` | Ricavi delle vendite e delle prestazioni | CE (A) |
| `B.6` | Per materie prime, sussidiarie, di consumo e di merci | CE (D) |
| `B.7` | Per servizi | CE (D) |

**`accounting/db.py`** — SQLite interface

Full schema (from `init_db()`):

```
registrazioni_prima_nota:
  id, data, numero_progressivo, tipo, descrizione, fattura_riferimento,
  bilanciata, creata_da_agente, confermata, created_at

righe_prima_nota:
  id, registrazione_id, conto_codice, conto_nome, dare, avere, descrizione

fatture_importate:
  id, hash_file (UNIQUE), numero, data, cedente_piva, cedente_nome,
  cessionario_piva, cessionario_nome, tipo_documento, importo_totale,
  xml_path, processata, registrazione_id, imported_at
```

Key functions:
- `calcola_hash_fattura(xml_bytes)` → SHA256 hex string
- `fattura_gia_importata(xml_bytes)` → `bool` (True = skip)
- `salva_fattura_importata(fattura, xml_bytes, xml_path)` → `Optional[int]` (None = already present)
- `salva_registrazione(registrazione)` → `int` (row id)
- `marca_registrazione_confermata(reg_id)` → `bool`
- `get_prima_nota(...)` + `get_fatture_importate(...)` — query helpers

**Missing:** No `iban_coa_mapping` table, no `movimenti_bancari` table. Both must be added in Phase 4.

### Scanner

**`scanner/client_folder_scanner.py`** — `ScanResult`

- `ScanResult.files["FatturaXML"]` → `List[Path]` — the exact list of XML files to process
- `ScanResult.files["CSV"]` → `List[Path]` — CSV bank statements to process
- `ScanResult.client_folder` → `Path` — root folder (for relative display in UI)

### Pipeline Stub

**`pipeline/pipeline_a.py`** — `PipelineA` class with `process_folder()` raising `NotImplementedError`

The stub contract is satisfied: import works, `process_folder()` raises `NotImplementedError`.
Phase 4 replaces the body of `process_folder()`.

### Agents

**`agents/fatturazione_agent.py`** — `FatturazioneAgent`

- `analizza_xml_bytes(xml_bytes, company_piva)` → `(FatturaPA, RegistrazionePrimaNota, "")` — pure deterministic, no LLM
- `stream_commento_fattura(xml_bytes, company_piva)` — optional LLM commentary, on-demand
- `process(context)` — swarm pipeline entrypoint, calls `analizza_xml_bytes()`

Pipeline A should NOT instantiate `FatturazioneAgent` for batch processing. It has unnecessary LLM
infrastructure overhead. Instead, call `FatturaPAParser` directly (as `analizza_xml_bytes()` itself does).
FatturazioneAgent is the right tool for interactive single-file analysis in the Fatture page.

### UI Integration Points

**`ui/pages/scanner.py`** — `render_scanner()`

- Reads `st.session_state["scan_results"]` (a `ScanResult`)
- Has the "Avvia elaborazione" button that calls `PipelineA().process_folder(scan_result.client_folder)`
- Currently catches `NotImplementedError` and shows a warning
- **Phase 4 must also add a review section** within this file or a new page

**`app.py`** — session state keys

- `scan_results` → `Optional[ScanResult]` — set by sidebar "Scansiona" button
- `client_folder_path` → `str` — persisted to config.yaml
- Page routing: `current_page == "scanner"` → `render_scanner()`
- `_current_fattura`, `_current_registrazione`, `_current_xml_bytes`, `_current_xml_name`, `_llm_analysis` — used by Fatture page review flow (reference pattern for Phase 4 review UI)

---

## Gap Analysis

What Phase 4 must build from scratch:

| Gap | Scope | Where |
|-----|-------|--------|
| `PipelineA.process_folder()` implementation | Medium | `pipeline/pipeline_a.py` |
| `InvoiceResult` result dataclass | Small | `pipeline/pipeline_a.py` or new `pipeline/models.py` |
| `pipeline/bank_statement_parser.py` | Medium | New file |
| `BankMovement` dataclass | Small | `pipeline/bank_statement_parser.py` |
| `iban_coa_mapping` DB table + CRUD | Small | `accounting/db.py` |
| `movimenti_bancari` DB table + save functions | Small | `accounting/db.py` |
| `pipeline_a_results` session state key + review UI | Medium | `ui/pages/scanner.py` |
| Bank movement review section in scanner page | Medium | `ui/pages/scanner.py` |

---

## Technical Decisions

### Decision 1: PipelineA returns results, does not write to DB

`PipelineA.process_folder()` must return a list of result objects rather than saving to DB. The user
reviews and confirms each item before anything is persisted. This is the project's core principle
("registrazioni NON vengono salvate senza review").

Recommended signature:

```python
@dataclass
class InvoiceResult:
    path: Path
    xml_bytes: bytes
    hash: str
    status: str          # "new" | "gia_importata" | "parse_error"
    fattura: Optional[FatturaPA]
    registrazione: Optional[RegistrazionePrimaNota]
    error_message: str = ""

def process_folder(self, scan_result: ScanResult, company_piva: str = "") -> List[InvoiceResult]:
    ...
```

Note: the current stub signature is `process_folder(client_folder: Path)`. Phase 4 must update the
signature to accept `ScanResult` directly (to avoid re-scanning) and `company_piva` (for
acquisto/vendita detection). The Scanner page's CTA call site in `ui/pages/scanner.py` must be
updated accordingly.

### Decision 2: Processing is synchronous in the UI thread

Invoice XML parsing is deterministic and fast (microseconds per file). Even 200 invoices takes under
2 seconds. No threads, no async, no background workers. Call `PipelineA().process_folder(...)` inside
a `st.spinner()` context and store results in `session_state["pipeline_a_results"]`. Rerun to render
the review UI.

### Decision 3: Bank statement parser uses the real Italian CSV format

Real client CSV files (observed in `CLIENTI/GEOINFOLAB SRL/`) use:
- Semicolon (`;`) as field separator
- Italian decimal format: `25,10` (comma decimal) with possible spaces: `18 668, 63`
- Multiple header rows before the data section (account number, balance, etc.)
- Column layout: `Data contabile;Data valuta;Descrizione;CASUALE;Accrediti;Addebiti;Descrizione estesa;...`
- Accrediti (income) and Addebiti (expenses) are separate columns, not a signed single column

The REQUIREMENTS.md specifies `data, descrizione, importo, saldo` columns (a normalized target format),
but the real files don't have this layout. The parser must handle both:
1. A normalised canonical format (data, descrizione, importo, saldo) — for tests and future use
2. The bank-specific Italian format actually seen in real files — detected by header inspection

A flexible parser that auto-detects the format by examining header rows is the right approach.

### Decision 4: IBAN → CoA mapping is per-client, stored in SQLite

Add a new `iban_coa_mapping` table to `accounting/db.py`:

```sql
CREATE TABLE IF NOT EXISTS iban_coa_mapping (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    iban TEXT NOT NULL,
    conto_codice TEXT NOT NULL,     -- e.g. "C.IV.1"
    conto_nome TEXT NOT NULL,       -- e.g. "Depositi bancari e postali"
    note TEXT DEFAULT '',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

The default mapping when no record exists: IBAN → `C.IV.1` (Depositi bancari e postali). This covers
the 90% case. The user can configure overrides (e.g. petty cash IBAN → `C.IV.3`) via the review UI.

Bank movement prima nota (payment to supplier): Dare `D.7` (Debiti v/fornitori), Avere `C.IV.1`.
Bank movement (receipt from customer): Dare `C.IV.1`, Avere `C.II.1`.
Unknown movement: Dare/Avere `C.IV.1` + `GENERICO` — user manually corrects counterpart account.

### Decision 5: Review UI lives in scanner.py, not a new page

The existing Scanner page already owns `scan_results`. Adding a collapsible review section below the
file list (after "Avvia elaborazione") is simpler than a new page. Pattern: session state holds
`pipeline_a_results: List[InvoiceResult]` and `pipeline_a_bank_results: List[BankMovementResult]`.
The page renders review expanders when these keys are set.

Pattern to follow: the Fatture page in `app.py` already has a working review-and-confirm flow using
`st.dataframe()` + "Conferma e Salva" / "Scarta" buttons. Use the same pattern.

### Decision 6: OFX is low priority

No OFX files were found in the real CLIENTI folder. PIPE-03 mentions OFX but real data is CSV.
Implement CSV fully; add a `parse_ofx()` stub that raises `NotImplementedError` to satisfy the
interface. OFX can be implemented in a future phase when a real use case appears.

---

## Integration Points

### How PipelineA connects to the scanner flow

```
Sidebar "Scansiona" button
  → ClientFolderScanner.scan(folder) → ScanResult stored in session_state["scan_results"]
  → page = "scanner" → render_scanner()
  → "Avvia elaborazione" button pressed
  → PipelineA().process_folder(scan_result, company_piva)  [PHASE 4 implements this]
  → results stored in session_state["pipeline_a_results"]
  → st.rerun()
  → render_scanner() renders review section
  → user clicks "Conferma" per item
  → salva_fattura_importata() + salva_registrazione() called
  → session_state["pipeline_a_results"] item marked confirmed
```

### Session state keys Phase 4 uses

| Key | Type | Set by | Read by |
|-----|------|--------|---------|
| `scan_results` | `ScanResult` | `app.py` sidebar | `scanner.py`, `pipeline_a.py` |
| `pipeline_a_results` | `List[InvoiceResult]` | `scanner.py` CTA | `scanner.py` review section |
| `pipeline_a_bank_results` | `List[BankMovementResult]` | `scanner.py` CTA | `scanner.py` review section |
| `pipeline_a_running` | `bool` | `scanner.py` CTA | `scanner.py` spinner guard |

---

## Data Flow

### FatturaXML → Prima Nota

```
ScanResult.files["FatturaXML"]  →  List[Path]
  for each path:
    xml_bytes = path.read_bytes()
    hash = calcola_hash_fattura(xml_bytes)       # from accounting.db
    if fattura_gia_importata(xml_bytes):
        → InvoiceResult(status="gia_importata")
        continue
    parser = FatturaPAParser()
    fatture = parser.parse_bytes(xml_bytes)
    fattura = fatture[0]
    suggestion = parser.to_prima_nota_suggestion(fattura, company_piva=company_piva)
    registrazione = RegistrazionePrimaNota.from_suggestion(suggestion)
    → InvoiceResult(status="new", fattura=fattura, registrazione=registrazione)

[user reviews each InvoiceResult in UI]
  on "Conferma":
    salva_fattura_importata(fattura, xml_bytes, str(path))
    registrazione.confermata = True
    reg_id = salva_registrazione(registrazione)
    update fatture_importate SET processata=1, registrazione_id=reg_id WHERE hash=hash
```

### CSV → Bank Movements → Prima Nota

```
ScanResult.files["CSV"]  →  List[Path]
  for each path:
    parser = BankStatementParser()
    movements = parser.parse_csv(path)           # List[BankMovement]
    for each movement:
        conto = lookup_iban_coa(movement.iban or "default")  → CoA account
        registrazione = build_bank_movement_registrazione(movement, conto)
        → BankMovementResult(movement=movement, registrazione=registrazione)

[user reviews each BankMovementResult in UI]
  on "Conferma":
    salva_registrazione(registrazione)
    salva_movimento_bancario(movement)
```

### Acquire/vendita detection (critical path)

`to_prima_nota_suggestion()` uses `company_piva` to detect direction:
- If `fattura.cedente.partita_iva != company_piva` → acquisto (we received the invoice)
- If `fattura.cedente.partita_iva == company_piva` → vendita (we issued the invoice)
- If `company_piva == ""` → defaults to `is_acquisto=True` (safe fallback for unknown config)

Pipeline A must load `company_piva` from `config/settings.py` → `load_company_config().get("partita_iva", "")`.

---

## CSV Bank Statement Design

### Real-world CSV format (observed in CLIENTI)

The CSV files in `CLIENTI/GEOINFOLAB SRL/` use this structure:
- Separator: semicolon (`;`)
- Encoding: typically UTF-8 or Latin-1
- Header section: 15-20 rows of bank metadata before the data table
- Data header row contains: `Data contabile;Data valuta;Descrizione;CASUALE;Accrediti;Addebiti;Descrizione estesa;...`
- Accrediti column: positive income amounts (e.g. `300,22`)
- Addebiti column: expense amounts, sometimes negative with sign (e.g. `-25,10`) or positive
- Italian decimal format: comma as decimal separator, optionally space-separated thousands
- Date format: `DD/MM/YYYY`
- Saldo (balance): not always a single column; may be in the header section as `Saldo contabile`

### `BankMovement` dataclass (recommended)

```python
@dataclass
class BankMovement:
    data: date
    data_valuta: Optional[date]
    descrizione: str
    importo: Decimal          # positive = income, negative = expense
    saldo: Optional[Decimal]
    iban: str = ""            # from file metadata if present
    raw_row: dict = field(default_factory=dict)  # original parsed row
```

### `BankStatementParser` interface

```python
class BankStatementParser:
    def parse_csv(self, path: Path) -> List[BankMovement]:
        """Auto-detects header section, parses movements."""

    def parse_canonical_csv(self, path: Path) -> List[BankMovement]:
        """Parses normalized format: data,descrizione,importo,saldo (comma sep)."""

    def _detect_header_row(self, rows: List[List[str]]) -> int:
        """Returns index of the data header row by looking for date-like first column."""

    def _parse_italian_decimal(self, s: str) -> Decimal:
        """Handles '25,10', '-300,22', '18 668,63', '18.668,63'."""

    def _extract_iban_from_header(self, header_rows: List[List[str]]) -> str:
        """Extracts IBAN/account number from metadata header rows."""
```

### Auto-detection strategy

The parser must distinguish two CSV variants:
1. **Bank-specific format** — identified by: multi-row header, semicolon separator, separate Accrediti/Addebiti columns
2. **Canonical format** — identified by: single header row with `data,descrizione,importo,saldo`

Detection: try to parse with csv.Sniffer on first 2048 bytes to detect separator; scan first 30 rows
for a row where column 0 contains a date pattern (`\d{2}[./]\d{2}[./]\d{4}`) — that's the first data
row; the row above it is the header.

---

## Human Review UI Design

### Invoice review section (in scanner.py)

For each `InvoiceResult` in `session_state["pipeline_a_results"]`:

**Status: "gia_importata"** → display as a collapsed expander with grey label "Gia importata".
No action buttons. Show: filename, invoice number, date, total.

**Status: "parse_error"** → display as a collapsed expander with red label. Show error message.

**Status: "new"** → display as an expanded expander with:
- Header: `{cedente.nome_completo} — {fattura.numero} — {fattura.data} — €{importo_totale:.2f}`
- A `st.dataframe()` table with righe (Conto, Nome, Dare, Avere)
- Metrics row: Totale Dare, Totale Avere, Bilanciata status
- Action buttons: "Conferma e Salva" (primary, disabled if not bilanciata) | "Scarta"
- Optional: "Chiedi all'Agente" button (LLM commentary on-demand, non-blocking)

**Batch confirm:** After all individual items, offer a "Conferma tutto" button that confirms all
unprocessed items that are already bilanciata. This is the primary workflow for batches of 20+ invoices.

### Bank movement review section (in scanner.py)

For each `BankMovementResult` in `session_state["pipeline_a_bank_results"]`:

- Table with all movements (data, descrizione, importo, suggested conto, action)
- Inline selectbox for correcting the conto suggestion
- Per-row "Conferma" toggle or bulk "Conferma tutto"
- Summary: total debit movements, total credit movements, net change

---

## Validation Architecture

`nyquist_validation` is enabled in `.planning/config.json`. Tests live in `tests/` directory.
Test runner: `pytest tests/ -x -q` (35 tests currently passing in 0.15s).

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest 8.4.0 |
| Config file | `conftest.py` at project root (adds project root to sys.path) |
| Quick run command | `pytest tests/test_pipeline_a.py -x -q` |
| Full suite command | `pytest tests/ -x -q` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| PIPE-01 | `process_folder()` returns one `InvoiceResult` per XML file | unit | `pytest tests/test_pipeline_a.py::TestPipelineAIngestion -x -q` | No — Wave 0 |
| PIPE-01 | Each result has `fattura`, `registrazione`, `status="new"` | unit | `pytest tests/test_pipeline_a.py::TestPipelineAIngestion::test_invoice_result_fields -x -q` | No — Wave 0 |
| PIPE-01 | `registrazione.is_bilanciata` is True for a standard invoice | unit | `pytest tests/test_pipeline_a.py::TestPipelineAIngestion::test_registrazione_bilanciata -x -q` | No — Wave 0 |
| PIPE-02 | Already-imported file returns `status="gia_importata"`, not exception | unit | `pytest tests/test_pipeline_a.py::TestPipelineAIngestion::test_skip_duplicate -x -q` | No — Wave 0 |
| PIPE-02 | `fattura_gia_importata()` returns True after save | unit | `pytest tests/test_pipeline_a.py::TestDeduplication -x -q` | No — Wave 0 |
| PIPE-03 | `BankStatementParser.parse_csv()` returns `List[BankMovement]` | unit | `pytest tests/test_bank_statement_parser.py -x -q` | No — Wave 0 |
| PIPE-03 | Italian decimal parser handles `25,10`, `-300,22`, `18 668,63` | unit | `pytest tests/test_bank_statement_parser.py::TestDecimalParsing -x -q` | No — Wave 0 |
| PIPE-03 | Auto-detect bank-specific semicolon CSV format | unit | `pytest tests/test_bank_statement_parser.py::TestFormatDetection -x -q` | No — Wave 0 |
| PIPE-04 | Bank movement suggestion uses `C.IV.1` when no IBAN mapping | unit | `pytest tests/test_bank_statement_parser.py::TestCOAMapping -x -q` | No — Wave 0 |
| PIPE-04 | Confirmed bank movement saved to DB | unit | `pytest tests/test_pipeline_a.py::TestBankMovementSave -x -q` | No — Wave 0 |

### Sampling Rate

- **Per task commit:** `pytest tests/test_pipeline_a.py tests/test_bank_statement_parser.py -x -q`
- **Per wave merge:** `pytest tests/ -x -q`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps

- [ ] `tests/test_pipeline_a.py` — covers PIPE-01, PIPE-02, PIPE-04 (DB aspects)
- [ ] `tests/test_bank_statement_parser.py` — covers PIPE-03, PIPE-04 (mapping logic)
- [ ] Test fixtures: minimal valid FatturaPA XML bytes (inline in test, not a file dependency)
- [ ] Test fixtures: sample Italian bank CSV content (inline string in test)

Existing infrastructure: `conftest.py` already handles sys.path; `tmp_path` fixture from pytest
sufficient for all file-based tests. No additional setup required.

---

## Risk Areas

### Risk 1: Namespace variation in real XML files

The parser handles both namespaced and non-namespaced XML. However, the real `IT01863120786_65024.xml`
uses the namespace `http://ivaservizi.agenziaentrate.gov.it/docs/xsd/fatture/v1.2` (a different URL
than the one in the parser: `urn:www.agenziaentrate.gov.it:specificheTecniche:sdi:fatturapa:v1.2`).

The parser's `_find()` method tries with namespace first, then falls back to no-namespace search.
This fallback handles the alternative namespace. Verified acceptable by the existing test suite passing.

**Action for Phase 4:** Add a test that parses a real-format XML bytes (using the `ivaservizi` namespace)
and confirms fields parse correctly.

### Risk 2: Zone.Identifier files in real client folders

The CLIENTI folder contains files like `IT01863120786_65024.xml:Zone.Identifier` — Windows alternate
data stream artifacts stored as separate files on Linux/WSL. These have no standard extension and will
be classified as `Altro` by the scanner (they don't contain `FatturaElettronica` in first 512 bytes).
They will not appear in `ScanResult.files["FatturaXML"]` so Pipeline A won't attempt to parse them.
No action needed — already handled correctly.

### Risk 3: CSV format diversity

Real CSVs vary significantly: some have 20+ header rows, different separators, and Italian decimal
formats. The `_parse_italian_decimal()` function is critical. Edge cases: `"18 668, 63"` (space in
number AND space after comma), `"-"` (empty movement amount), `""` (blank cell).

**Action:** Test `_parse_italian_decimal()` exhaustively with all observed variants before considering
PIPE-03 complete.

### Risk 4: Multi-body XML files

`parse_bytes()` returns a list. For multi-body files (rare but valid), `fatture[0]` is used. The other
bodies are silently dropped. A warning should be logged to `InvoiceResult.error_message` when
`len(fatture) > 1` so the accountant knows to handle the other bodies manually.

### Risk 5: Streamlit session state persistence on rerun

After `PipelineA().process_folder()` runs and results are stored in `session_state["pipeline_a_results"]`,
`st.rerun()` is called. The Scanner page must check `if session_state.get("pipeline_a_results")` to
render the review section. If the user navigates away and back, the results must still be available.
Session state persists within a browser session. The current `scan_results` pattern already demonstrates
this pattern correctly.

### Risk 6: Deduplication race — salva_fattura_importata atomicity

`salva_fattura_importata()` does SELECT-then-INSERT. In single-user local mode this is fine. No risk.

### Risk 7: process_folder signature breaking the CTA in scanner.py

The current CTA calls `PipelineA().process_folder(scan_result.client_folder)`. Phase 4 needs to change
the signature to `process_folder(scan_result, company_piva)`. The CTA in `ui/pages/scanner.py` must
be updated in the same task that changes the signature — they must ship atomically.

---

## Standard Stack

All libraries are already installed. No new dependencies required for Phase 4.

| Library | Purpose | Used in Phase 4 |
|---------|---------|----------------|
| `lxml` (≥5.0) | XML parsing (primary) with fallback to `xml.etree` | FatturaPAParser.parse_bytes() |
| `sqlite3` (stdlib) | DB persistence | accounting/db.py |
| `csv` (stdlib) | CSV parsing | BankStatementParser |
| `decimal` (stdlib) | Monetary arithmetic | BankMovement.importo, all amounts |
| `hashlib` (stdlib) | SHA256 deduplication | calcola_hash_fattura() |
| `streamlit` ≥1.28 | Review UI | scanner.py |
| `pandas` | Tabular display in st.dataframe() | scanner.py (already used in Fatture page) |

**No new pip install required.** All dependencies are already in `requirements.txt`.

---

## Architecture Patterns

### Pattern: Result accumulator (don't stream to DB)

```python
# CORRECT — Phase 4 pattern
results = []
for path in scan_result.files["FatturaXML"]:
    xml_bytes = path.read_bytes()
    if fattura_gia_importata(xml_bytes):
        results.append(InvoiceResult(path=path, status="gia_importata", ...))
        continue
    # ... parse ...
    results.append(InvoiceResult(path=path, status="new", fattura=fattura, registrazione=reg))
return results  # UI reviews, then calls salva_*

# WRONG — do not do this
for path in ...:
    # parse...
    salva_registrazione(reg)  # No! User hasn't reviewed yet.
```

### Pattern: session state review loop (from Fatture page)

```python
# In scanner.py — after Pipeline A runs
if "pipeline_a_results" in st.session_state:
    for i, result in enumerate(st.session_state["pipeline_a_results"]):
        if result.status == "gia_importata":
            st.caption(f"Gia importata: {result.path.name}")
            continue
        with st.expander(f"{result.fattura.cedente.nome_completo} ..."):
            # show dataframe
            col1, col2 = st.columns(2)
            if col1.button("Conferma", key=f"confirm_{i}"):
                # salva_fattura_importata + salva_registrazione
                st.session_state["pipeline_a_results"][i].status = "confermata"
                st.rerun()
```

### Pattern: Italian decimal parsing

```python
import re
from decimal import Decimal

def _parse_italian_decimal(s: str) -> Decimal:
    s = s.strip()
    if not s or s == "-":
        return Decimal("0")
    # Remove thousands separators (dots or spaces before 3 digits)
    s = re.sub(r'[.\s](?=\d{3})', '', s)
    # Replace comma decimal separator with dot
    s = s.replace(',', '.')
    # Remove remaining spaces
    s = s.replace(' ', '')
    try:
        return Decimal(s)
    except Exception:
        return Decimal("0")
```

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| XML parsing | Custom regex/string parsing of FatturaPA | `FatturaPAParser.parse_bytes()` | Already handles namespace variants, multi-body, all field types |
| Prima nota generation | Custom double-entry logic | `FatturaPAParser.to_prima_nota_suggestion()` + `RegistrazionePrimaNota.from_suggestion()` | Already handles acquisto/vendita detection, all IVA types |
| SHA256 dedup | Custom file comparison | `calcola_hash_fattura()` + `fattura_gia_importata()` | Already in db.py with UNIQUE constraint |
| LLM for batch | Run LLM on every invoice during batch | Call `analizza_xml_bytes()` (no LLM) for batch, offer LLM commentary on-demand per invoice | LLM adds latency, zero value for deterministic parsing |

---

## Common Pitfalls

### Pitfall 1: Forgetting to update scanner.py CTA call site

**What goes wrong:** `PipelineA.process_folder()` signature changes but the CTA in `scanner.py` still
passes only `client_folder`. This causes a `TypeError` at runtime.
**Prevention:** Ship the signature change and the updated CTA in the same task.

### Pitfall 2: Re-scanning instead of using ScanResult

**What goes wrong:** `process_folder(client_folder)` re-runs `ClientFolderScanner.scan()` internally,
doing disk I/O twice and potentially getting a different result if files changed.
**Prevention:** Pass `scan_result` directly (already contains `ScanResult.files["FatturaXML"]`).

### Pitfall 3: Calling salva_registrazione before user review

**What goes wrong:** Pipeline saves all registrations immediately on "Avvia elaborazione". User cannot
review or correct. Violates core project principle.
**Prevention:** Pipeline returns results; saves happen only on per-item "Conferma" button click.

### Pitfall 4: Italian decimal parsing failures

**What goes wrong:** `Decimal("25,10")` raises `InvalidOperation`. Real CSVs have values like
`"18 668, 63"` with spaces.
**Prevention:** Normalise all amount strings through `_parse_italian_decimal()` before `Decimal()`.

### Pitfall 5: confermata flag not set before salva_registrazione

**What goes wrong:** Registrations saved with `confermata=False` appear in the "pending review" queue
but are already in the DB. The accountant sees them twice.
**Prevention:** Always set `registrazione.confermata = True` before calling `salva_registrazione()`.
Pattern from `app.py` line 271: `reg.confermata = True` → `salva_registrazione(reg)`.

---

## Sources

### Primary (HIGH confidence)
- Direct code inspection: `parsers/fattura_pa.py` — FatturaPAParser, FatturaPA dataclass, to_prima_nota_suggestion(), to_text_summary()
- Direct code inspection: `accounting/prima_nota.py` — RegistrazionePrimaNota, RigaPrimaNota, TipoRegistrazione, from_suggestion()
- Direct code inspection: `accounting/db.py` — full schema, all functions, SHA256 dedup logic
- Direct code inspection: `accounting/piano_dei_conti.py` — PIANO_DEI_CONTI complete code→name mapping
- Direct code inspection: `scanner/client_folder_scanner.py` — ScanResult structure
- Direct code inspection: `agents/fatturazione_agent.py` — analizza_xml_bytes() deterministic path
- Direct code inspection: `ui/pages/scanner.py` — CTA button, session_state["scan_results"] usage
- Direct code inspection: `app.py` — session state keys, Fatture page review pattern
- Direct code inspection: `swarm/context.py` — ProcessingContext fields
- Direct file inspection: `CLIENTI/GEOINFOLAB SRL/BILANCIO 2025/ESTRATTI CONTO/ELABORATO/20260313_Movimenti_Conto_anno_2025_xlsx.csv` — real Italian bank CSV format
- Direct file inspection: `CLIENTI/ARCOAL/01 - FT AL 06-02-25 - OK/RICEVUTE - OK/IT01863120786_65024.xml` — real FatturaPA XML namespace variant
- Direct inspection: `tests/` — pytest 8.4.0, conftest.py sys.path pattern, 35 tests passing in 0.15s

### Secondary (MEDIUM confidence)
- `REQUIREMENTS.md` — PIPE-01 through PIPE-04 description (what "data, descrizione, importo, saldo" refers to)
- `.planning/config.json` — nyquist_validation: true confirmed

---

## Metadata

**Confidence breakdown:**
- Existing code inventory: HIGH — all findings from direct source inspection
- Gap analysis: HIGH — based on schema inspection and missing tables identified
- CSV format: HIGH — based on real client files in CLIENTI/ directory
- Bank movement CoA mapping: MEDIUM — accounting logic is standard Italian bookkeeping but not verified against a specific regulatory source
- OFX decision: MEDIUM — based on absence of OFX files in real CLIENTI data (may appear in other client folders)

**Research date:** 2026-03-20
**Valid until:** 2026-06-20 (stable codebase; changes only if Phase 4 itself modifies the modules surveyed here)
