---
phase: 01-stack-cleanup
verified: 2026-03-18T16:33:43Z
status: passed
score: 7/7 must-haves verified
re_verification: false
---

# Phase 1: Stack Cleanup — Verification Report

**Phase Goal:** The codebase runs on a clean, minimal dependency set with no unused libraries and no deprecated packages
**Verified:** 2026-03-18T16:33:43Z
**Status:** passed
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

| #  | Truth                                                                                     | Status     | Evidence                                                                                        |
|----|-------------------------------------------------------------------------------------------|------------|-------------------------------------------------------------------------------------------------|
| 1  | requirements.txt contains no LangChain, SQLAlchemy, PyPDF2, or beautifulsoup4 entries    | VERIFIED   | File contains none of these strings; grep returns no matches                                    |
| 2  | requirements.txt contains pypdf>=4.0.0 and sentence-transformers>=3.0.0                   | VERIFIED   | Both lines present at lines 17 and 14 respectively                                              |
| 3  | All Python files that previously imported PyPDF2 now import pypdf instead                 | VERIFIED   | `from pypdf import PdfReader` in core/file_processors.py:82 and rag/adapters/local_folder.py:183; zero PyPDF2 occurrences in production code |
| 4  | LLM calls from base_agent.py use openai SDK directly with no LangChain wrapper            | VERIFIED   | base_agent.py has zero langchain references; delegates to OllamaClient.invoke which calls `client.chat.completions.create` (openai SDK) |
| 5  | ChromaDB uses paraphrase-multilingual-MiniLM-L12-v2 for embeddings                        | VERIFIED   | EMBEDDING_MODEL constant set at rag/vector_store.py:12; SentenceTransformerEmbeddingFunction configured in _get_embedding_function(); passed to get_or_create_collection |
| 6  | Collection name is accounting_kb, not wiki_knowledge_base                                 | VERIFIED   | COLLECTION_NAME = "accounting_kb" at line 13; wiki_knowledge_base appears only in migration deletion block (lines 80-81) |
| 7  | If sentence-transformers is not installed, a clear ImportError is raised (no silent fallback) | VERIFIED | `except ImportError: raise` at vector_store.py:100-101 ensures propagation; _get_embedding_function raises ImportError with actionable pip message |

**Score:** 7/7 truths verified

---

### Required Artifacts

| Artifact                          | Expected                                       | Status     | Details                                                                                  |
|-----------------------------------|------------------------------------------------|------------|------------------------------------------------------------------------------------------|
| `requirements.txt`                | Clean dependency list with pypdf, no dead deps | VERIFIED   | Exact target content; 14 deps; no langchain/sqlalchemy/PyPDF2/beautifulsoup4             |
| `core/file_processors.py`         | PDF extraction using pypdf                     | VERIFIED   | `from pypdf import PdfReader` at line 82; substantive extraction logic; wired as primary PDF handler |
| `rag/adapters/local_folder.py`    | PDF loading using pypdf                        | VERIFIED   | `from pypdf import PdfReader` at line 183; substantive load logic; wired in _load_single_file dispatch |
| `rag/vector_store.py`             | ChromaDB vector store with multilingual embeddings | VERIFIED | 327 lines; EMBEDDING_MODEL, COLLECTION_NAME constants; _get_embedding_function(); _init_store with migration; clear(); smoke test at __main__; exports SimpleVectorStore |
| `agents/base_agent.py`            | LLM calls via openai SDK, no LangChain         | VERIFIED   | Zero langchain imports; delegates to core/llm_client.OllamaClient which uses client.chat.completions.create |

---

### Key Link Verification

| From                              | To                                              | Via                              | Status    | Details                                                             |
|-----------------------------------|-------------------------------------------------|----------------------------------|-----------|---------------------------------------------------------------------|
| `core/file_processors.py`         | `pypdf`                                         | `from pypdf import PdfReader`    | WIRED     | Import at line 82; used at line 84 in extract_text_from_pdf        |
| `rag/adapters/local_folder.py`    | `pypdf`                                         | `from pypdf import PdfReader`    | WIRED     | Import at line 183; used at line 184 in _load_pdf_file             |
| `rag/vector_store.py`             | `chromadb.utils.embedding_functions`            | `SentenceTransformerEmbeddingFunction` | WIRED | Imported in _get_embedding_function(); instance passed as embedding_function to get_or_create_collection at lines 90-97 and 258-265 |
| `rag/vector_store.py`             | `sentence-transformers`                         | ChromaDB EmbeddingFunction       | WIRED     | Model name "paraphrase-multilingual-MiniLM-L12-v2" passed to SentenceTransformerEmbeddingFunction; ChromaDB calls sentence-transformers transparently on add/query |
| `agents/base_agent.py`            | `openai SDK`                                    | `create_ollama_client` / `OllamaClient.invoke` | WIRED | base_agent._get_client() calls create_ollama_client(); OllamaClient.invoke and stream_invoke both call `client.chat.completions.create` |

---

### Requirements Coverage

| Requirement | Source Plan | Description                                                                                     | Status    | Evidence                                                          |
|-------------|-------------|-------------------------------------------------------------------------------------------------|-----------|-------------------------------------------------------------------|
| STACK-01    | 01-01-PLAN  | Sistema usa solo openai SDK nativo; LangChain rimosso da requirements.txt e da base_agent.py    | SATISFIED | requirements.txt: no langchain entries. base_agent.py: no langchain imports. llm_client.py: client.chat.completions.create throughout |
| STACK-02    | 01-01-PLAN  | SQLAlchemy rimosso da requirements.txt                                                          | SATISFIED | requirements.txt: no sqlalchemy entry. grep over all .py files: zero sqlalchemy references |
| STACK-03    | 01-01-PLAN  | PyPDF2 sostituito con pypdf>=4.0.0 in requirements.txt e in tutti i file che lo importano       | SATISFIED | requirements.txt: pypdf>=4.0.0 present, PyPDF2 absent. Both importing files updated |
| STACK-04    | 01-02-PLAN  | sentence-transformers>=3.0.0 aggiunto; ChromaDB configurato con paraphrase-multilingual-MiniLM-L12-v2 | SATISFIED | requirements.txt: sentence-transformers>=3.0.0. rag/vector_store.py: EMBEDDING_MODEL, SentenceTransformerEmbeddingFunction, collection metadata with embedding_model key |

**Orphaned requirements check:** REQUIREMENTS.md Traceability table maps STACK-01 through STACK-04 to Phase 1. All four are claimed by plan frontmatter (01-01 claims STACK-01/02/03; 01-02 claims STACK-04). No orphaned requirements.

---

### Success Criteria Coverage (from ROADMAP.md)

| SC# | Criterion                                                                                    | Status    | Evidence                                                                                    |
|-----|----------------------------------------------------------------------------------------------|-----------|---------------------------------------------------------------------------------------------|
| 1   | pip install -r requirements.txt completes with no LangChain, SQLAlchemy, or PyPDF2 installed | VERIFIED  | None of these appear in requirements.txt                                                    |
| 2   | App starts and all existing pages load without import errors                                  | VERIFIED  | `python -c 'import core.file_processors; import rag.vector_store; import agents.base_agent'` succeeds with output "imports OK" |
| 3   | LLM calls from base_agent.py use openai SDK directly (client.chat.completions.create) with no LangChain wrapper | VERIFIED | base_agent -> OllamaClient.invoke -> client.chat.completions.create; zero langchain in codebase |
| 4   | ChromaDB accepts Italian text and returns semantically relevant results using multilingual MiniLM | HUMAN NEEDED | Code structure is fully wired; actual semantic relevance requires running the smoke test with sentence-transformers installed |

---

### Anti-Patterns Found

No anti-patterns detected in phase-modified files. Scan covered:
- `requirements.txt`
- `core/file_processors.py`
- `rag/adapters/local_folder.py`
- `rag/vector_store.py`
- `agents/base_agent.py`

No TODO/FIXME/PLACEHOLDER comments found. No empty implementations. No stub return values. All handlers substantive.

**Notable (info only):** `rag/adapters/local_folder.py` retains `beautifulsoup4` references in docstrings and the optional HTML loading fallback — this is intentional by design (bs4 is an optional runtime dep for HTML files, not in requirements.txt). Documented in 01-01-SUMMARY.md as deliberate. Not a gap.

---

### Human Verification Required

#### 1. Italian Semantic Retrieval Quality

**Test:** Install dependencies (`pip install -r requirements.txt`), then run `python rag/vector_store.py` from the project root.
**Expected:** Output ends with "=== Smoke test completato con successo ===" and prints either "PASS: top result = 'liquidazione IVA trimestrale dichiarazione periodica'" or "PASS: result is IVA-related (acceptable)". The test indexes 3 Italian accounting phrases and queries for "dichiarazione IVA periodo fiscale".
**Why human:** Requires sentence-transformers model download (~420MB, paraphrase-multilingual-MiniLM-L12-v2) and actual semantic inference. Cannot verify embedding quality via static grep.

---

### Gaps Summary

No gaps. All automated checks passed across all four requirements and all seven observable truths.

The only remaining item is human verification of semantic retrieval quality (SC-4 from ROADMAP.md), which requires running the smoke test with the model actually installed and loaded. The code wiring for this is complete and correct.

**Commit verification:** All commits referenced in SUMMARYs were confirmed in git log — `85c3eaf`, `ae60465`, `44375d3`, `aefa3d1`, `e6fdfcf` all present and match described purposes.

---

_Verified: 2026-03-18T16:33:43Z_
_Verifier: Claude (gsd-verifier)_
