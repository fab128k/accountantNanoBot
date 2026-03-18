# External Integrations

**Analysis Date:** 2026-03-18

## APIs & External Services

**Not Currently Integrated:**
- No external APIs are actively integrated in v1.0.0
- System is designed for fully local operation without cloud dependencies

**Planned/Future Integrations (from ROADMAP.md):**
- **Intermediario SDI (Sistema di Interscambio)** - For official invoice transmission to Italian tax authority (AdE)
  - Candidates: Aruba, Entaksi, Namirial (AgID-certified intermediaries)
  - Status: Not yet implemented; required for public distribution
  - Implementation: Keep local processing, delegate transmission via API to certified intermediary
- **Conservazione Sostitutiva (Document Archival)** - 10-year retention compliance
  - Will integrate via API to AgID-certified services
  - Status: Not yet implemented

## Data Storage

**Databases:**
- SQLite 3 (native, standard library)
  - Location: `data/accounting.db`
  - Auto-initialized by `accounting/db.py` on first run
  - Tables: `registrazioni_prima_nota` (ledger entries), `righe_prima_nota` (debit/credit lines), `fatture_importate` (invoice records)
  - Indexes: On date, document type, account code, VAT payer
  - Client: Direct `sqlite3` module (no ORM)

**Vector Database:**
- ChromaDB 0.4.0+
  - Location: `knowledge_base/vectorstore/` (persistent local directory)
  - Purpose: RAG vector store for semantic search over client documents (invoices, contracts, statements)
  - Embedding: ChromaDB default embeddings (not specified; automatic)
  - Fallback: In-memory keyword search if ChromaDB unavailable
  - Client: `chromadb.PersistentClient` in `rag/vector_store.py`

**File Storage:**
- Local filesystem only
  - Invoice XMLs: `data/fatture_xml/`
  - Documents: `data/documenti/`
  - Conversations: `conversations/`
  - Knowledge base: `knowledge_base/`
  - Database: `data/`

**Caching:**
- In-memory (per Streamlit session) via `st.session_state`
- ChromaDB provides persistent vector cache

## Authentication & Identity

**Auth Provider:**
- None - Single-user local web app
- Streamlit runs on `localhost:8501` (localhost-only binding)
- No user accounts, login, or API keys required

**Client Identification:**
- Per-client configuration loaded from `data/config.yaml` (human-created YAML file)
- Loaded by `config/settings.py`: `load_company_config()`
- No automated identity verification

## Monitoring & Observability

**Error Tracking:**
- None (local development/small-scale use)

**Logs:**
- Console output via Python `logging` or `print()`
- Streamlit writes to terminal stdout
- No persistent log files or external logging service

**Debugging:**
- Manual inspection via Streamlit UI
- Database inspection via SQLite tools (e.g., `sqlite3` CLI)

## CI/CD & Deployment

**Hosting:**
- Local machine only (not cloud-deployed)
- Web interface: Streamlit development server on `localhost:8501`
- LLM inference: Ollama on `localhost:11434`

**CI Pipeline:**
- None (no automated testing or deployment)

**Installer Strategy (planned, not yet implemented):**
- Phase 1: Bash/Batch scripts (`install.bat`, `install.sh`)
  - Installs `uv` or pip
  - Creates isolated venv
  - Installs Python deps
  - Verifies/installs Ollama
  - Downloads default LLM model
- Phase 2: Windows Inno Setup `.exe` installer
  - Bundles Python 3.13 Embeddable (30MB)
  - Pre-configured venv
  - Creates Start Menu shortcuts
- macOS: Platypus app bundle wrapper
- Linux: AppImage or .deb package

**Build Tools:**
- None active; Poetry metadata present but requirements.txt is primary manifest

## Environment Configuration

**Required env vars:**
- None mandatory for core functionality
- Optional: `OLLAMA_BASE_URL` (defaults to `http://localhost:11434/v1` in `config/constants.py`)
- Optional: `DEFAULT_MODEL` (defaults to `llama3.2:3b`)

**Secrets location:**
- `secrets/` directory (for future use; currently empty)
- Not used by current v1.0.0
- Future: SDI intermediary API keys would go here

**No API Keys in Use:**
- Ollama doesn't require authentication
- No cloud LLM services integrated (all inference local)

## Webhooks & Callbacks

**Incoming:**
- None

**Outgoing:**
- None in v1.0.0
- Future: Will notify user of accounting events (e.g., VAT filing deadline alerts) via chat

## Local System Integration

**File System:**
- Automatic scanning of client folder via `ClientFolderScanner` (planned, partially implemented)
- Watches `data/fatture_xml/` for new invoice XMLs
- Watches `data/documenti/` for company documents (PDF, DOCX, etc.)

**Process Management:**
- User launches `streamlit run app.py` manually
- Ollama must already be running (separate process)
- No inter-process communication beyond standard HTTP to Ollama API

## Data Flow - External Touch Points

**Invoice Input:**
1. User scans client folder → detects XML files in `data/fatture_xml/`
2. Parser: `parsers/fattura_pa.py` reads FatturaPA v1.2 XML
3. Accounting: `accounting/db.py` stores invoice metadata + hash (deduplication)
4. RAG: `rag/manager.py` indexes invoice text for semantic search

**Document Input:**
1. User uploads PDFs/DOCX/images → UI file uploader
2. Processor: `core/file_processors.py` extracts text
3. RAG: ChromaDB indexes document chunks
4. Agents: Can retrieve relevant docs via RAG for advisory

**Output Artifacts:**
- Accounting registrations exported as JSON/PDF via `export/exporters.py`
- Financial reports generated as PDF via ReportLab
- Conversations exported as Markdown/JSON/TXT

## Data Sources for Model Training (Future)

**Active Learning (planned):**
- User corrections to invoice classifications → automatically saved
- Example: User confirms "Telefonica invoice → Categoria SPESE_TELECOM" → stored as mapping
- System learns invoice/supplier classification without cloud sync
- All learning stays local (no data export)

---

*Integration audit: 2026-03-18*
