# Codebase Concerns

**Analysis Date:** 2026-03-18

## Tech Debt

**LangChain and SQLAlchemy Unused Dependencies:**
- Issue: `requirements.txt` includes `langchain>=0.3.0` and `langchain-ollama>=0.2.0`, but neither package is imported anywhere in the codebase. Similarly, `sqlalchemy>=2.0.0` is listed but not used—all database operations use native `sqlite3`. These dependencies add unnecessary bloat and maintenance burden.
- Files: `requirements.txt` (lines 28, 31-32)
- Impact: Bloated installation (30-50MB extra), slower pip resolve, unnecessary security surface, conflicts during environment setup
- Fix approach: Remove these three packages from `requirements.txt` immediately. This is a breaking change only if external code depends on them; internal code does not.

**Deprecated PyPDF2 Package:**
- Issue: `requirements.txt` line 15 uses `PyPDF2>=3.0.0`, which is officially deprecated as of late 2024. The package is still listed in CONTRIBUTING.md line 48 as "do not use". However, the codebase imports it in two places.
- Files:
  - `core/file_processors.py` line 82: `from PyPDF2 import PdfReader`
  - `rag/adapters/local_folder.py` line 183: `from PyPDF2 import PdfReader`
- Impact: Future security vulnerabilities will not be patched. The maintainer recommends migration to `pypdf>=4.0.0`, which is a drop-in replacement. API is identical.
- Fix approach: (1) Change `requirements.txt` line 15 from `PyPDF2>=3.0.0` to `pypdf>=4.0.0`. (2) No code changes needed—imports work identically. (3) Test PDF ingestion in RAG pipeline.

**Bare Exception Handlers:**
- Issue: Multiple locations use bare `except:` clauses, which catch all exceptions including `KeyboardInterrupt`, `SystemExit`, and `GeneratorExit`. This masks programming errors and makes debugging difficult.
- Files:
  - `core/conversation.py` line 158: `except:` in `format_time_from_iso()`
  - `ui/chat.py` line 51: `except:` in stream processing
  - `ui/sidebar/knowledge_base.py` lines 492, 542: `except:` in UI widget updates
  - `rag/vector_store.py` line 202: `except:` in similarity search
- Impact: Silent failures, unpredictable behavior during interrupts or system shutdown, harder debugging
- Fix approach: Replace bare `except:` with `except Exception as e:` and log the exception. If catching `KeyboardInterrupt` is intentional, be explicit.

---

## Known Bugs

**PyPDF2 Import Not Gracefully Handled:**
- Symptoms: In `core/file_processors.py` line 80-100, if PyPDF2 is not installed, the error message says "[Errore: PyPDF2 non installato]" but the function still tries to use `PdfReader` if the import succeeds elsewhere. The error handling is inline but depends on runtime import.
- Files: `core/file_processors.py` lines 97-99
- Trigger: User uploads a PDF file when PyPDF2 is not installed
- Workaround: Install PyPDF2 (or upgrade to pypdf). Error message is clear but occurs after parsing attempt.

**RAG Vector Store Silent Fallback:**
- Symptoms: `rag/vector_store.py` lines 41-64 attempt to initialize ChromaDB but silently fall back to in-memory store on import error or exception. No persistent metadata is available—searches revert to keyword matching.
- Files: `rag/vector_store.py` lines 56-64
- Trigger: ChromaDB installation fails or corrupts; user doesn't realize search quality is degraded
- Workaround: Check `vector_store.use_chromadb` flag to see if ChromaDB is active. No API to query this from UI.

**Bare Exception in OllamaClient.invoke():**
- Symptoms: `core/llm_client.py` line 93 catches all exceptions and returns `f"[Errore LLM: {e}]"`. This masks network errors, timeouts, and model not found errors equally, making root cause diagnosis difficult.
- Files: `core/llm_client.py` lines 93-94
- Trigger: Ollama not running, model not downloaded, network error
- Workaround: Check Ollama status manually; error message is vague.

---

## Security Considerations

**Missing Input Validation on SQL Queries:**
- Risk: `accounting/db.py` uses parameterized queries for INSERT/UPDATE/DELETE (safe), but the `get_prima_nota()` function at lines 254-325 builds dynamic WHERE clauses by concatenating strings with parameters. The parameters ARE passed separately (safe from SQL injection) but the field names in `where_clauses` are not validated. A malicious caller passing `tipo="'; DROP TABLE registrazioni_prima_nota; --"` will not execute because the value is parameterized, but the pattern is fragile.
- Files: `accounting/db.py` lines 277-292
- Current mitigation: Parameters are always passed via tuple, never concatenated. Field filtering is done by enum values elsewhere.
- Recommendations: Add explicit validation for `tipo` parameter against allowed `TipoRegistrazione` enum values. Document that `where_clauses` must come from trusted internal code only.

**No Rate Limiting on LLM Requests:**
- Risk: Users can send unlimited requests to Ollama without throttling. A malicious script could overwhelm the local Ollama instance, causing DoS.
- Files: `core/llm_client.py` (no rate limiting), agents use this client directly
- Current mitigation: Ollama is local (not cloud), so limited to single machine resources. No public exposure.
- Recommendations: Add request throttling (e.g., 1 request per second) in `OllamaClient.invoke()` if distributing to multiple users.

**Environment Configuration Not Validated:**
- Risk: `.env` file (if present) is not validated. Invalid paths or missing Ollama instance are silently ignored until first use.
- Files: `config/settings.py` (loads settings), but no validation
- Current mitigation: Default values are used if env vars are missing.
- Recommendations: Add startup check in `app.py` to verify Ollama is reachable before initializing session state.

---

## Performance Bottlenecks

**PDF Text Extraction Inefficient for Large Files:**
- Problem: `core/file_processors.py` line 87-90 reads entire PDF into memory and extracts text from ALL pages sequentially. For a 500-page PDF, this can cause UI freeze for 5-10 seconds.
- Files: `core/file_processors.py` lines 80-100
- Cause: Single-threaded page iteration, no pagination or streaming
- Improvement path: (1) Add maximum page limit (e.g., first 100 pages for preview). (2) Use `pdfplumber` instead of PyPDF2—it's faster for text extraction. `pdfplumber` is already in the intended stack (see memory).

**RAG Chunking Not Optimized for Italian Text:**
- Problem: `rag/chunker.py` uses fixed chunk size (default 500 chars) with hardcoded overlap. Italian accounting documents often have complex terminology that spans chunk boundaries, leading to poor semantic coherence.
- Files: `rag/chunker.py` (not fully read, but referenced in manager)
- Cause: Language-agnostic chunking strategy
- Improvement path: Add Italian-aware preprocessing (e.g., split on sentence boundaries using regex for Italian abbreviations like "s.p.a.", "s.r.l."). Consider using `sentence_transformers` for semantic chunking (already planned in memory).

**Vector Search Always Queries All Chunks:**
- Problem: `rag/vector_store.py` lines 81-102 add all chunks to ChromaDB collection without pagination or indexing by date/category. Searching for "fatture gennaio 2026" may return 200 results and iterate through all of them.
- Files: `rag/vector_store.py` lines 120-145 (search method)
- Cause: No filtering by metadata before similarity search
- Improvement path: Add metadata filtering before vector search (e.g., filter by document type, date range). ChromaDB supports this via `where` parameter.

**Database Queries Use GROUP_CONCAT Without LIMIT:**
- Problem: `accounting/db.py` line 295-298 uses `GROUP_CONCAT()` to fetch all righe (accounting lines) for a registrazione without limit. For a registrazione with 1000+ lines, this could cause memory spike.
- Files: `accounting/db.py` lines 294-304
- Cause: No pagination or streaming of results
- Improvement path: Split fetching into two operations: (1) get registrazioni, (2) fetch righe in batches. Or add LIMIT clause.

---

## Fragile Areas

**Base Agent RAG Context Silently Fails:**
- Files: `agents/base_agent.py` lines 70-87
- Why fragile: If `rag_manager.is_indexed()` returns True but `get_context_for_prompt()` throws an exception, the error is caught and an empty string is returned. Caller gets no context and no warning. System appears to work but silently degrades quality.
- Safe modification: Add logging before returning empty string. Consider returning a flag with the context tuple to signal whether context was retrieved successfully.
- Test coverage: No unit tests for this fallback scenario.

**Orchestrator Routing Hardcoded Keywords:**
- Files: `agents/orchestrator.py` lines 20-52
- Why fragile: Routing rules are hardcoded as tuples of keywords. If a user message says "IVA" but uses different wording ("imposta sulla valore aggiunto"), the message routes to default "memoria" agent instead of "iva" agent. No semantic understanding of intent.
- Safe modification: Add fallback to semantic matching (use small embeddings model) if keyword match confidence is low. Or document limitations clearly in UI.
- Test coverage: No unit tests for routing logic; easy to break with keyword list changes.

**FatturaPA Parser Assumes UTF-8 XML:**
- Files: `parsers/fattura_pa.py` (full file not read, but referenced)
- Why fragile: FatturaPA spec requires UTF-8, but if a malformed file declares ISO-8859-1 encoding, parsing may silently corrupt data without error.
- Safe modification: Add explicit encoding check at parse start. Validate XML declaration matches actual content encoding.
- Test coverage: No test for non-UTF-8 FatturaPA files.

**Session State Initialization Not Idempotent:**
- Files: `app.py` lines 46-76
- Why fragile: `initialize_session_state()` is called on every page load. Creating new `KnowledgeBaseManager()` every time (line 56) initializes a new ChromaDB client. If the old one is still holding locks, this causes errors.
- Safe modification: Check if `kb_manager` already exists before creating new one. Or use a singleton pattern.
- Test coverage: No test for multi-page navigation in Streamlit.

**Piano dei Conti OIC Hardcoded:**
- Files: `accounting/piano_dei_conti.py` (575 lines)
- Why fragile: Chart of accounts is hardcoded for Italy OIC standard. Client with different GAAP (e.g., IFRS) or custom account structure cannot modify it without editing source code.
- Safe modification: Load piano_dei_conti from database or JSON config file instead of hardcoding. Add override mechanism per client.
- Test coverage: No test for non-OIC account structures.

---

## Scaling Limits

**SQLite Single-Writer Limitation:**
- Current capacity: Works fine for single accountant using system. If distributed to multi-user (2+ concurrent sessions), SQLite will lock on write operations.
- Limit: ~1 concurrent writer; reads are OK but writes are serialized
- Scaling path: Migrate to PostgreSQL or similar when multi-user support is needed. Change `accounting/db.py` to use `psycopg2` instead of `sqlite3`. This is a breaking change; schema migration script needed.

**Ollama Local Model Limited by RAM:**
- Current capacity: llama3.2:3b works in 16GB RAM + 4GB VRAM. Larger models (7b+) will cause swap thrashing.
- Limit: Model size capped by available hardware
- Scaling path: Implement model switching logic based on available memory (e.g., detect RAM, load appropriate model). See memory notes for `psutil` hardware detection approach.

**RAG Chunk Storage:**
- Current capacity: ChromaDB in-process storage works for <100k chunks (~50MB docs). Beyond that, search latency degrades.
- Limit: ~100k chunks before noticeable slowdown
- Scaling path: For larger knowledge bases, switch to hosted ChromaDB (cloud) or Pinecone vector DB. Requires API integration.

---

## Dependencies at Risk

**PyPDF2 No Longer Maintained:**
- Risk: Package marked deprecated; no new versions planned after 3.0.0
- Impact: Cannot handle new PDF format variants or security issues. Users must upgrade to `pypdf`.
- Migration plan: Upgrade to `pypdf>=4.0.0` (drop-in replacement, API identical). Update `requirements.txt` and run smoke tests on PDF imports.

**beautifulsoup4 Only Used for Fallback:**
- Risk: `requirements.txt` line 14 includes beautifulsoup4, but it's only used as fallback in RAG HTML adapter. Not critical.
- Impact: Extra 200KB dependency that could be removed if HTML support is dropped.
- Migration plan: Review if HTML document ingestion is needed. If not, remove from requirements and rag/adapters code. If yes, keep as-is.

---

## Missing Critical Features

**No Schema Versioning or Migration System:**
- Problem: `accounting/db.py` uses `CREATE TABLE IF NOT EXISTS` (safe), but if schema changes, there's no migration path. Adding a new column requires manual ALTER TABLE.
- Blocks: Cannot evolve database schema in production without manual intervention
- Recommendation: Implement simple migration system (e.g., versioned SQL files in `migrations/` directory, run on app startup if version mismatch detected). Use semver for schema versions.

**No Request Logging or Audit Trail:**
- Problem: LLM requests, file uploads, and accounting entries have no audit trail. Cannot trace who did what when.
- Blocks: Compliance audit, debugging user issues, regulatory requirements for accounting systems
- Recommendation: Add transaction log table (`audit_log`) with timestamp, user, action, details. Log all state changes. Implement in `accounting/db.py`.

**No Backup/Export Strategy:**
- Problem: All data lives in `data/accounting.db` and ChromaDB store. No backup mechanism documented.
- Blocks: Data loss if disk fails; cannot recover from accidental deletion
- Recommendation: Implement scheduled backup to ZIP file (database + vectorstore). Add export endpoint to save JSON.

---

## Test Coverage Gaps

**No Unit Tests for Accounting Logic:**
- What's not tested: `accounting/prima_nota.py` balance validation, `accounting/piano_dei_conti.py` account mappings, IVA calculation logic
- Files: `accounting/*.py`
- Risk: Silent calculation errors could propagate to generated PDFs; regulatory non-compliance
- Priority: **High** — accounting correctness is business-critical

**No Integration Tests for RAG Pipeline:**
- What's not tested: Document ingestion → chunking → indexing → search end-to-end
- Files: `rag/manager.py`, `rag/adapters/local_folder.py`, `rag/vector_store.py`
- Risk: RAG silently fails (falls back to memory store) with no warning
- Priority: **High** — RAG is core feature

**No Tests for FatturaPA Parser:**
- What's not tested: Parsing of real FatturaPA XML files, edge cases (note di credito, reverse charge, split payment), non-UTF-8 files
- Files: `parsers/fattura_pa.py`
- Risk: Malformed invoices silently truncate or corrupt data; tax compliance risk
- Priority: **High** — parser correctness is non-negotiable

**No Tests for Orchestrator Routing:**
- What's not tested: User message routing to correct agent, edge cases (ambiguous keywords, multilingual input)
- Files: `agents/orchestrator.py`
- Risk: User questions routed to wrong agent; wrong domain expertise applied
- Priority: **Medium** — affects UX but not data integrity

**No Tests for SQLite Database Operations:**
- What's not tested: Concurrent access, transaction rollback, constraint violations, index performance
- Files: `accounting/db.py`
- Risk: Data corruption under edge case loads
- Priority: **Medium** — only relevant for multi-user deployment

---

*Concerns audit: 2026-03-18*
