# Codebase Structure

**Analysis Date:** 2026-03-18

## Directory Layout

```
accountantNanoBot/
├── app.py                          # Streamlit entry point (router multipagina)
├── requirements.txt                # Python dependencies
├── pyproject.toml                  # Project metadata
├── .streamlit/                     # Streamlit config (secrets, theme)
├── .planning/                      # GSD planning artifacts
│   └── codebase/                   # Architecture/structure docs
├── config/                         # Configuration & constants
│   ├── __init__.py
│   ├── settings.py                 # Company config YAML loader, API key helpers
│   ├── constants.py                # Paths, defaults, IVA rates, file extensions
│   └── branding.py                 # App title, icons, UI strings
├── core/                           # Core services
│   ├── __init__.py
│   ├── llm_client.py               # OllamaClient, openai SDK wrapper
│   ├── file_processors.py          # PDF/DOCX/TXT/XML extractors
│   ├── conversation.py             # Message history management
│   └── persistence.py              # Conversation serialization
├── accounting/                     # Accounting logic (partita doppia)
│   ├── __init__.py
│   ├── db.py                       # SQLite schema, CRUD operations
│   ├── prima_nota.py               # Registrazione, RigaPrimaNota dataclasses, TipoRegistrazione enum
│   └── piano_dei_conti.py          # OIC chart of accounts (all 100+ account codes)
├── parsers/                        # Document parsers
│   ├── __init__.py
│   └── fattura_pa.py               # FatturaPA v1.2 XML parser (FPR12, FPA12)
├── agents/                         # Multi-agent orchestration
│   ├── __init__.py
│   ├── base_agent.py               # BaseAccountingAgent (abstract)
│   ├── orchestrator.py             # Orchestrator with keyword routing
│   ├── fatturazione_agent.py       # Invoice processing agent (first operational)
│   └── memoria_agent.py            # Fallback chat agent
├── rag/                            # Knowledge Base / Retrieval-Augmented Generation
│   ├── __init__.py
│   ├── manager.py                  # KnowledgeBaseManager orchestrator
│   ├── vector_store.py             # SimpleVectorStore (ChromaDB + fallback)
│   ├── chunker.py                  # TextChunker (1000 chars, 200 overlap default)
│   ├── models.py                   # Document, Chunk dataclasses
│   └── adapters/                   # Document source adapters
│       ├── __init__.py
│       ├── base.py                 # BaseAdapter interface
│       └── local_folder.py         # LocalFolderAdapter (files from filesystem)
├── ui/                             # Streamlit UI components
│   ├── __init__.py
│   ├── style.py                    # CSS injection, theme
│   ├── pages/                      # Multi-page views
│   │   ├── __init__.py
│   │   ├── dashboard.py            # Main dashboard with stats & agent chat
│   │   ├── onboarding.py           # Company config setup, knowledge base indexing
│   │   ├── prima_nota.py           # Journal entry list, detail view
│   │   └── bilancio.py             # (Stub) Balance sheet view
│   └── sidebar/                    # Sidebar widgets
│       ├── __init__.py
│       ├── session_map_widget.py   # Client folder selection
│       ├── knowledge_base.py       # KB management (index, search stats)
│       └── conversations.py        # Chat history list
├── data/                           # Runtime data (SQLite, configs, indexed docs)
│   ├── accounting.db               # SQLite with registrazioni, righe, fatture
│   ├── config.yaml                 # Company profile (P.IVA, name, regime)
│   ├── fatture_xml/                # Imported FatturaPA files
│   └── documenti/                  # Supporting documents (contracts, visure)
├── knowledge_base/                 # Knowledge base artifacts
│   └── vectorstore/                # ChromaDB persistent store (UUID subdirs)
├── conversations/                  # Chat history (JSON per session)
├── FATTURE/                        # Sample client folder (demo data)
│   └── ARCOAL/
│       ├── 01 - FT AL 06-02-25 - OK/
│       │   ├── EMESSE - OK/        # Invoices issued by this client
│       │   └── RICEVUTE - OK/      # Invoices received by this client
│       └── ...
├── memory/                         # Project context & philosophy
│   └── MEMORY.md                   # Project vision, decisions, stack decisions
├── examples/                       # Tutorial scripts
│   ├── secrets_tutorial.py         # API key loading example
│   └── client_factory_tutorial_datapizza-ai.py
└── export/                         # Generated exports (PDF F24, reports)
```

## Directory Purposes

**app.py (Root)**
- Purpose: Streamlit application entry point and router
- Contains: Session initialization, page routing, sidebar navigation, orchestrator lazy-load
- Key files: Lines 1-100 handle imports & session setup; lines 363-455 sidebar; lines 467-490 page routing

**config/**
- Purpose: Application configuration, constants, and settings
- Contains: Default values, file paths, IVA rates, OIC account codes, company profile management
- Key files:
  - `constants.py`: Defines BASE_DIR, DB_PATH, FATTURE_DIR, DEFAULT_MODEL, ALIQUOTE_IVA
  - `settings.py`: load_company_config(), save_company_config(), get_agent_models()

**core/**
- Purpose: Reusable services and utilities
- Contains: LLM client (Ollama), file processors (PDF/DOCX extraction), conversation storage
- Key files:
  - `llm_client.py`: OllamaClient.invoke(), .stream_invoke(), get_local_ollama_models()
  - `file_processors.py`: extract_text_from_pdf(), extract_text_from_docx(), ProcessedFile dataclass

**accounting/**
- Purpose: Deterministic accounting logic (partita doppia implementation)
- Contains: SQLite persistence, journal entry generation, chart of accounts
- Key files:
  - `db.py`: init_db(), salva_registrazione(), get_fatture_importate(), SQLite CRUD
  - `prima_nota.py`: Registrazione dataclass, RigaPrimaNota (dare/avere validation), TipoRegistrazione enum
  - `piano_dei_conti.py`: PIANO_DEI_CONTI dict with 100+ OIC account codes (A, B.I.1, C.II.1, etc.)

**parsers/**
- Purpose: Extract structured data from documents
- Contains: FatturaPA v1.2 XML parser (only parser currently implemented)
- Key files:
  - `fattura_pa.py`: FatturaPAParser class, Soggetto, FatturaPA, DettaglioLinea, RiepilogoIVA dataclasses

**agents/**
- Purpose: Multi-agent system for specialized accounting tasks
- Contains: Base agent class, orchestrator with keyword routing, specialized agents
- Key files:
  - `base_agent.py`: BaseAccountingAgent (model, system_prompt, _get_client(), _get_rag_context())
  - `orchestrator.py`: Orchestrator class, _ROUTING_RULES keyword matching, build_default_orchestrator()
  - `fatturazione_agent.py`: FatturazioneAgent (first operational agent), analizza_xml_bytes(), stream_commento_fattura()
  - `memoria_agent.py`: General-purpose agent (fallback)

**rag/**
- Purpose: Knowledge Base management (document ingestion → chunking → indexing → search)
- Contains: Vector store, document chunker, adapter pattern for sources
- Key files:
  - `manager.py`: KnowledgeBaseManager (orchestrator for RAG pipeline)
  - `vector_store.py`: SimpleVectorStore (ChromaDB + in-memory fallback)
  - `chunker.py`: TextChunker (splits by overlap strategy)
  - `adapters/local_folder.py`: LocalFolderAdapter (loads .pdf, .txt, .md, .docx, .xml from folder)

**ui/pages/**
- Purpose: Streamlit multi-page views
- Contains: Dashboard, onboarding, prima nota, balance sheet
- Key files:
  - `dashboard.py`: render_dashboard(), _render_stats(), _render_agent_chat()
  - `onboarding.py`: Company config form, KB folder indexing UI
  - `prima_nota.py`: Journal entry list, filter by date/type, edit view
  - (bilancio.py is stub, not implemented)

**ui/sidebar/**
- Purpose: Sidebar widgets and navigation
- Contains: Session/client selection, knowledge base status, conversation list
- Key files:
  - Widgets mounted in app.py sidebar (lines 363-455)

**data/**
- Purpose: Runtime and persistent data
- Contains: SQLite database, YAML company config, imported XML files, documents
- Key files:
  - `accounting.db`: Created by init_db(); tables: registrazioni_prima_nota, righe_prima_nota, fatture_importate
  - `config.yaml`: Company profile (partita_iva, ragione_sociale, regime_fiscale, ecc.)
  - `fatture_xml/`: Imported invoice files (organized by filename)
  - `documenti/`: Supporting docs for RAG (visure, contracts, etc.)

**knowledge_base/**
- Purpose: Persistent RAG index
- Contains: ChromaDB vector store with chunked documents
- Structure: `vectorstore/` contains UUID subdirs (ChromaDB collections)

**memory/**
- Purpose: Project vision and architectural decisions
- Key files:
  - `MEMORY.md`: Complete project context, stack decisions, competitive analysis

## Key File Locations

**Entry Points:**
- `app.py`: Streamlit app entry point (run: `streamlit run app.py`)
- `accounting/db.py` `init_db()`: Database schema initialization (called by UI pages)
- `agents/orchestrator.py` `build_default_orchestrator()`: Agent factory (called by app.py)

**Configuration:**
- `config/constants.py`: All path, version, default constants
- `config/settings.py`: Company config loader (data/config.yaml)
- `config/branding.py`: App name, icons, UI strings
- `.streamlit/secrets.toml`: Streamlit secrets (not in git, for optional API keys)

**Core Logic:**
- `accounting/prima_nota.py`: Registrazione dataclass (debit/credit validation)
- `accounting/piano_dei_conti.py`: Account chart (all OIC codes)
- `parsers/fattura_pa.py`: FatturaPA XML parser
- `agents/base_agent.py`: BaseAccountingAgent class

**Testing:**
- No test files in codebase (test/unit coverage is missing—see CONCERNS.md)

## Naming Conventions

**Files:**
- `snake_case.py`: All Python files use snake_case
- Entry point: `app.py`
- Modules: Singular or plural descriptive (e.g., `agent.py`, `agents/`, `db.py`)
- Pages: Correspond to app route (e.g., `dashboard.py`, `prima_nota.py`)

**Directories:**
- Plural for module groups: `config/`, `core/`, `agents/`, `parsers/`, `ui/pages/`
- Singular for data: `data/`, `knowledge_base/` (contains persistent artifacts)
- Lowercase, no hyphens

**Classes:**
- `PascalCase` for all classes: `BaseAccountingAgent`, `OllamaClient`, `Registrazione`, `FatturaPA`, `KnowledgeBaseManager`
- Enum: `PascalCase.CONSTANT` (e.g., `TipoRegistrazione.FATTURA_ACQUISTO`)

**Functions:**
- `snake_case` for all functions: `load_company_config()`, `init_db()`, `extract_text_from_pdf()`
- Factory functions prefixed `create_` or `build_`: `create_ollama_client()`, `build_default_orchestrator()`
- Getters prefixed `get_`: `get_local_ollama_models()`, `get_company_piva()`

**Variables:**
- `snake_case` for local/instance variables: `company_piva`, `registration_id`, `top_k`
- `UPPER_SNAKE_CASE` for module constants: `DEFAULT_CHUNK_SIZE`, `OLLAMA_BASE_URL`, `DB_PATH`
- `_private_underscore()` for internal/implementation methods

**Dataclasses:**
- Field names snake_case: `cedente_piva`, `importo_totale`, `data_scadenza`
- `@property` for computed fields: `nome_completo`, `is_bilanciata`, `importo`

## Where to Add New Code

**New Feature (e.g., new agent capability):**
- Primary code: `agents/[new_agent].py` (inherit from BaseAccountingAgent)
- Register in: `agents/orchestrator.py` _ROUTING_RULES + build_default_orchestrator()
- Tests: (Missing—should go in tests/agents/test_[new_agent].py)

**New Page/UI Route:**
- Implementation: `ui/pages/[route_name].py` with `render_[route_name]()` function
- Register in: `app.py` navigation dict (lines 370-376) + routing switch (lines 467-490)
- Sidebar: Add navigation button in app.py sidebar loop (lines 378-386)

**New Document Parser:**
- Implementation: `parsers/[format]_parser.py` (follow FatturaPAParser pattern)
- Register in: `core/file_processors.py` (add to extraction dispatcher)
- Config: Add extension to `config/constants.py` SUPPORTED_EXTENSIONS

**New Accounting Rule (e.g., new IVA handling):**
- Logic: `accounting/prima_nota.py` in Registrazione or RigaPrimaNota
- Reference table: `config/constants.py` (if rate or rule needs global visibility)
- Agent integration: `agents/fatturazione_agent.py` _SYSTEM_PROMPT or processa_fattura() method

**New Account Code:**
- Add to: `accounting/piano_dei_conti.py` PIANO_DEI_CONTI dict
- Key format: Code (e.g., "C.II.1"), value: dict with codice, nome, sezione, tipo, dare_avere

**Utilities / Shared Helpers:**
- Core utilities: `core/[utility_name].py`
- Config-like constants: `config/constants.py`
- Accounting-specific helpers: `accounting/[helper_name].py`

**Knowledge Base Ingestion:**
- New source type: `rag/adapters/[source]_adapter.py` (inherit from BaseAdapter)
- Register in: `rag/manager.py` (add to set_adapter() selection logic if needed)

## Special Directories

**data/**
- Purpose: Runtime persistent data
- Generated: Yes (SQLite, YAML created on first run)
- Committed: No (gitignored; only schema is versioned)
- What goes here: accounting.db, config.yaml, fatture_xml/*.xml, documenti/*

**knowledge_base/vectorstore/**
- Purpose: ChromaDB persistent vector index
- Generated: Yes (populated during onboarding KB indexing)
- Committed: No (gitignored; rebuilt per client)
- What goes here: ChromaDB collection metadata and embeddings

**conversations/**
- Purpose: Streamlit session chat history (optional persistence)
- Generated: Yes (created if chat feature persists across sessions)
- Committed: No (gitignored; ephemeral per session)

**FATTURE/**
- Purpose: Demo/test client folder structure
- Generated: No (checked in as example)
- Committed: Yes (sample invoice XMLs for testing)
- Structure mirrors expected client folder hierarchy

**.streamlit/**
- Purpose: Streamlit framework config
- Generated: Partially (config.toml is checked in)
- Committed: Yes (config.toml for theme/layout)
- Contains: Secrets, config (theme=light, layout=wide)

---

*Structure analysis: 2026-03-18*
