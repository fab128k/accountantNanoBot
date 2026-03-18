# Technology Stack

**Analysis Date:** 2026-03-18

## Languages

**Primary:**
- Python 3.12+ (3.13.1 in use) - Core application, accounting agents, parsers, RAG
- XML - FatturaPA invoice format parsing
- Markdown - Documentation and export formats

## Runtime

**Environment:**
- Python 3.13.1
- Streamlit 1.28.0+ - Web UI framework (local app, not cloud-based)
- Ollama (locally installed) - LLM inference engine via OpenAI-compatible API

**Package Manager:**
- pip (via requirements.txt)
- Poetry (pyproject.toml for dependency tracking)
- Lock file: Not detected in active use (requirements.txt is primary)

## Frameworks

**Core:**
- Streamlit 1.28.0+ - Web framework for interactive accounting UI
- OpenAI SDK 1.0.0+ - Generic LLM client (interfaces with Ollama via OpenAI-compatible API endpoint)

**LLM Integration:**
- Ollama (localhost:11434) - Local inference server
  - Default model: `llama3.2:3b` (configurable in `config/constants.py`)
  - Temperature: 0.1 (low, for deterministic accounting work)
  - Custom `OllamaClient` wrapper in `core/llm_client.py` (direct OpenAI SDK usage)

**Knowledge Base / RAG:**
- ChromaDB 0.4.0+ - Vector store for document retrieval (with in-memory fallback)
- Custom `SimpleVectorStore` wrapper in `rag/vector_store.py`
- No explicit embedding model specified (ChromaDB provides automatic embeddings)

**Document Processing:**
- lxml 5.0.0+ - XML parsing for FatturaPA v1.2
- PyPDF2 3.0.0+ - PDF text extraction (note: marked for deprecation in favor of pypdf in roadmap)
- python-docx 0.8.0+ - DOCX text extraction
- BeautifulSoup4 4.12.0+ - HTML parsing
- pdfplumber - Alternative PDF extraction
- Pillow 10.0.0+ - Image processing for vision models

**Export:**
- ReportLab 4.0.0+ - PDF generation for financial reports
- Custom markdown/JSON/TXT exporters in `export/exporters.py`

**Build/Dev:**
- python-dotenv 1.0.0+ - Environment variable management

## Key Dependencies

**Critical:**
- `openai>=1.0.0` - Generic LLM client (used to interface with Ollama via OpenAI-compatible endpoint)
  - Why it matters: Abstracts vendor-specific APIs; Ollama exposes OpenAI-compatible interface at `localhost:11434/v1`
- `streamlit>=1.28.0` - All UI/web interface functionality
- `chromadb>=0.4.0` - Vector database for RAG retrieval over client documents

**Accounting Core:**
- `lxml>=5.0.0` - XML parsing for FatturaPA invoices (regulatory requirement)
- `sqlite3` (stdlib) - SQL database for accounting ledger, registrations, invoices
  - Path: `data/accounting.db` (auto-initialized in `accounting/db.py`)

**Infrastructure:**
- `pyyaml>=6.0` - Configuration file parsing for company settings
- `requests>=2.31.0` - HTTP client for external integrations (not heavily used currently)

## Configuration

**Environment:**
- No `.env` file required for basic operation
- All defaults hardcoded in `config/constants.py` and `config/settings.py`
- Optional: `data/config.yaml` for per-company settings (loaded by `config/settings.py`)

**Build:**
- `.streamlit/config.toml` - Streamlit theme configuration (colors, fonts)
- `pyproject.toml` - Poetry dependency management (metadata; requirements.txt is actual install source)
- `requirements.txt` - Primary dependency manifest

## Platform Requirements

**Development:**
- Python 3.12+
- 16GB RAM minimum (per project vision)
- 4GB VRAM for Ollama local inference
- Ollama runtime (installed separately, not via pip)
- OS: Windows, macOS, or Linux (tested on WSL2)

**Production:**
- Streamlit requires Python 3.12+
- Ollama must be running on `localhost:11434`
- SQLite database (local file)
- No external API keys required (fully local)

## Stack Status & Technical Debt

**Issues to Address (from MEMORY.md):**
- [ ] **Remove LangChain** - Currently in requirements but not actively used. Replace with direct OpenAI SDK calls.
- [ ] **Remove SQLAlchemy** - Listed in requirements but `accounting/db.py` uses native `sqlite3` exclusively.
- [ ] **Replace PyPDF2** - Deprecated upstream; switch to `pypdf>=4.0.0` (drop-in replacement by same maintainer).
- [ ] **Add sentence-transformers** - Needed for multilingual embeddings in ChromaDB. Model: `paraphrase-multilingual-MiniLM-L12-v2` (420MB).
- [ ] **Add pdfplumber** - For better PDF extraction than PyPDF2.
- [ ] **Remove beautifulsoup4** - Included in pdfplumber; not needed independently.

**Target requirements.txt (after cleanup):**
```
streamlit>=1.28.0
python-dotenv>=1.0.0
openai>=1.0.0
lxml>=5.0.0
chromadb>=0.4.0
sentence-transformers>=3.0.0
pypdf>=4.0.0
pdfplumber>=0.11.0
python-docx>=1.1.0
reportlab>=4.0.0
Pillow>=10.0.0
pyyaml>=6.0
requests>=2.31.0
```

---

*Stack analysis: 2026-03-18*
