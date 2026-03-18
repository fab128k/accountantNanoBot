# Architecture

**Analysis Date:** 2026-03-18

## Pattern Overview

**Overall:** Layered multi-agent system with deterministic accounting core + conversational LLM overlay

**Key Characteristics:**
- **Deterministic layer**: Accounting logic (partita doppia, IVA, piano dei conti) executed in pure Python
- **LLM layer**: Knowledge augmentation, advisory chat, classification—via local Ollama only
- **Agent-based routing**: Keyword matching to specialized agents (fatturazione, iva, bilancio, compliance, prima_nota, memoria)
- **RAG-augmented**: Local ChromaDB vector store for document context retrieval
- **Human-in-the-loop**: All registrations require explicit user confirmation before persisting

## Layers

**Presentation Layer (UI):**
- Purpose: Streamlit web interface with multi-page routing
- Location: `app.py`, `ui/pages/`, `ui/sidebar/`
- Contains: Page renders (dashboard, onboarding, fatture, prima_nota), sidebar navigation, session state management
- Depends on: Core agents, accounting DB, RAG manager
- Used by: End users via browser on localhost:8501

**Agent Layer:**
- Purpose: Specialized agents for different accounting domains; orchestrates routing
- Location: `agents/base_agent.py`, `agents/orchestrator.py`, `agents/fatturazione_agent.py`, `agents/memoria_agent.py`
- Contains: BaseAccountingAgent class, agent implementations, orchestrator with keyword routing
- Depends on: LLM client (Ollama), RAG manager, accounting logic
- Used by: UI, conversation handler

**Accounting Core (Deterministic):**
- Purpose: Pure accounting logic: partita doppia (double-entry), piano dei conti (OIC chart of accounts), IVA rules
- Location: `accounting/db.py`, `accounting/prima_nota.py`, `accounting/piano_dei_conti.py`
- Contains: SQLite database schema + functions, data classes for registrazioni (registrations) and righe (rows), OIC account chart
- Depends on: Python stdlib (sqlite3, datetime, decimal)
- Used by: Agents for generating suggestions, UI for display and confirmation

**Parser Layer:**
- Purpose: Extract structured data from documents
- Location: `parsers/fattura_pa.py`, `core/file_processors.py`
- Contains: FatturaPA XML parser (v1.2 FPR12/FPA12), file format extractors (PDF, DOCX, TXT, MD)
- Depends on: lxml, pdfplumber, pypdf, python-docx
- Used by: Fatturazione agent, knowledge base ingestion

**Knowledge Base / RAG:**
- Purpose: Index and retrieve document context for augmenting LLM responses
- Location: `rag/manager.py`, `rag/vector_store.py`, `rag/chunker.py`, `rag/models.py`, `rag/adapters/`
- Contains: KnowledgeBaseManager, ChromaDB vector store, text chunker, adapter pattern for document sources
- Depends on: chromadb, sentence-transformers (for embeddings)
- Used by: Agents to inject context into prompts, UI for knowledge base status

**Configuration:**
- Purpose: App settings, company profile, constants
- Location: `config/settings.py`, `config/constants.py`, `config/branding.py`
- Contains: Default settings, company config YAML persistence, API key loading, paths
- Depends on: Python stdlib, pyyaml
- Used by: All modules for configuration access

**LLM Client:**
- Purpose: Abstraction over local Ollama API (OpenAI-compatible)
- Location: `core/llm_client.py`
- Contains: OllamaClient class, invoke/stream_invoke methods, subprocess helper to list Ollama models
- Depends on: openai SDK (used for Ollama API, not OpenAI), subprocess
- Used by: All agents for LLM requests

## Data Flow

**Invoice Import & Registration Flow:**

1. User uploads FatturaPA XML file via Fatture page
2. `FatturaPAParser.parse_bytes()` parses XML to structured FatturaPA dataclass
3. Fatturazione agent's `analizza_xml_bytes()` generates suggested registration (Registrazione + Righe)
4. Suggested registration displayed in UI with dare/avere lines, balance status
5. User confirms or regenerates → persisted to `registrazioni_prima_nota`, `righe_prima_nota` in DB
6. Fattura hash saved to `fatture_importate` (prevents duplicate import)

**Knowledge Base Ingestion Flow:**

1. User selects folder in UI (onboarding or sidebar knowledge base widget)
2. KnowledgeBaseManager.index_documents() called with folder path
3. LocalFolderAdapter loads files matching extensions (.pdf, .txt, .md, .xml, .docx)
4. TextChunker splits documents into overlapping chunks (default 1000 chars, 200 overlap)
5. SimpleVectorStore.add_chunks() persists to ChromaDB collection
6. Embeddings computed by ChromaDB (default: sentence-transformers multilingual model)

**Agent Chat Flow:**

1. User enters message in dashboard chat
2. Orchestrator.route() matches keywords to determine best agent (fatturazione, iva, bilancio, compliance, prima_nota, memoria)
3. Selected agent _get_rag_context() retrieves top-k relevant chunks from vector store
4. Agent builds prompt: system prompt + RAG context + user message
5. OllamaClient.stream_invoke() sends to local Ollama, streams response chunks
6. UI displays streamed response in real-time

**State Management:**

- Session state stored in `st.session_state` (Streamlit memory per session)
- Persistent state in SQLite database:
  - `registrazioni_prima_nota`: Journal entries (date, type, description, balanced flag, confirmed flag)
  - `righe_prima_nota`: Rows of entries (account code/name, debit/credit amounts)
  - `fatture_importate`: Imported invoices (file hash, number, date, supplier, amount, processing status)
- Knowledge base indexed in ChromaDB at `knowledge_base/vectorstore/`
- Company configuration in YAML: `data/config.yaml` (P.IVA, name, regime, SDI code, etc.)

## Key Abstractions

**Registrazione (Registration):**
- Purpose: Represents single journal entry (partita doppia debit/credit pair)
- Examples: `accounting/prima_nota.py` dataclass Registrazione
- Pattern: Dataclass with `righe` list; enforces balance constraint (sum_dare == sum_avere); supports multiple entry types (TipoRegistrazione enum)

**FatturaPA:**
- Purpose: Structured representation of electronic invoice
- Examples: `parsers/fattura_pa.py` Soggetto, FatturaPA, DettaglioLinea, RiepilogoIVA dataclasses
- Pattern: Nested dataclasses mirror XML structure; factories for clean parsing

**BaseAccountingAgent:**
- Purpose: Base class for all domain-specific agents
- Examples: `agents/fatturazione_agent.py` extends BaseAccountingAgent
- Pattern: Lazy-init client; pluggable RAG manager; system prompt + model/temperature configuration

**Orchestrator:**
- Purpose: Routes user queries to correct agent via keyword matching
- Examples: `agents/orchestrator.py` _ROUTING_RULES tuple of (keywords_list, agent_id)
- Pattern: Scoring algorithm (count matches in message); fallback to memoria agent

**KnowledgeBaseManager:**
- Purpose: Facade over RAG pipeline (load → chunk → embed → index → search)
- Examples: `rag/manager.py` with set_adapter, index_documents, search methods
- Pattern: Configurable components (adapter, chunker, vector_store); progress callbacks

## Entry Points

**Web Application:**
- Location: `app.py`
- Triggers: User runs `streamlit run app.py`
- Responsibilities: Session init, page routing, sidebar navigation, agent orchestrator lazy-load, LLM model selection

**Database Initialization:**
- Location: `accounting/db.py` `init_db()` function
- Triggers: Called by Fatture page, Prima Nota page, dashboard on first render
- Responsibilities: Create schema (registrazioni_prima_nota, righe_prima_nota, fatture_importate) with indexes

**Agent Instantiation:**
- Location: `agents/orchestrator.py` `build_default_orchestrator()` factory
- Triggers: Called by app.py `ensure_orchestrator()` on first page load requiring agents
- Responsibilities: Creates instances of all 6 agents, registers with Orchestrator, injects RAG manager

## Error Handling

**Strategy:** Graceful degradation with user feedback; LLM errors don't block deterministic operations

**Patterns:**

- **LLM failures**: OllamaClient.invoke() returns error message string prefixed `[Errore LLM: ...]`; UI displays in chat; deterministic accounting continues
- **Parser failures**: FatturaPAParser wrapped in try/except; error shown in expandable "Errore parsing" alert; user can import without analysis
- **DB failures**: Caught in page renders; displays warning "Database not available"; app doesn't crash
- **Missing components**: Orchestrator checks `if st.session_state.get("orchestrator") is None`; shows warning instead of error
- **RAG context**: If vector store unavailable, agents continue with empty context (no injection)

## Cross-Cutting Concerns

**Logging:**
- Built-in Python logging not used; errors surfaced via st.error/st.warning
- Future: Add structured logging to `logging.json` for audit trail

**Validation:**
- Registrazione.is_bilanciata property checks balance before save
- RigaPrimaNota.valida() checks single row constraints (dare XOR avere > 0)
- FatturaPA parser validates XML structure during parsing
- Future: Add comprehensive schema validation layer

**Authentication:**
- None implemented (app assumes single-user local instance)
- No user accounts, no password
- Future: Multi-user support deferred to Phase N

**Authorization:**
- None (single user, local only)
- No role-based access control

**Deduplication:**
- Fatture tracked by SHA256 hash of XML bytes (`fatture_importate.hash_file`)
- Prevents re-import of same file

## Architectural Constraints & Decisions

1. **Ollama-only**: No cloud LLMs (OpenAI, Claude API) in core flow to maintain 100% data locality
2. **Deterministic first**: Accounting calculations NEVER depend on LLM output; LLM suggestions reviewed before save
3. **Sequential agents**: No parallel agent execution (hardware constraint: single 3B model in 16GB RAM)
4. **SQLite persistence**: Simple, requires no external DB; sufficient for accounting scale
5. **Streamlit UI**: Multi-page simplicity; no SPA complexity
6. **ChromaDB optional**: Vector store gracefully degrades to in-memory if unavailable

---

*Architecture analysis: 2026-03-18*
