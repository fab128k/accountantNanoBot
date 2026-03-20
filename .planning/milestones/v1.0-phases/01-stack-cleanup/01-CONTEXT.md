# Phase 1: Stack Cleanup - Context

**Gathered:** 2026-03-18
**Status:** Ready for planning

<domain>
## Phase Boundary

Remove dead dependencies (LangChain, SQLAlchemy, PyPDF2, beautifulsoup4) from requirements.txt
and the two Python files that import PyPDF2. Add sentence-transformers for Italian-quality
ChromaDB embeddings using the multilingual MiniLM model. No functional changes to accounting
logic, agents, or UI.

</domain>

<decisions>
## Implementation Decisions

### LangChain removal
- LangChain is in requirements.txt but NEVER imported anywhere in Python code
- base_agent.py's client.invoke() / client.stream_invoke() call OllamaClient (already native openai SDK) — NOT LangChain
- Removal is requirements.txt only: delete `langchain>=0.3.0` and `langchain-ollama>=0.2.0` lines
- base_agent.py requires NO rewrite — it is already clean

### SQLAlchemy removal
- SQLAlchemy is in requirements.txt but never imported anywhere
- Removal is requirements.txt only: delete `sqlalchemy>=2.0.0` line

### PyPDF2 replacement
- Replace `PyPDF2>=3.0.0` with `pypdf>=4.0.0` in requirements.txt
- Update import in `core/file_processors.py:82` — change `from PyPDF2 import PdfReader` to `from pypdf import PdfReader`
- Update import in `rag/adapters/local_folder.py:183` — same change
- pypdf is a drop-in replacement (same maintainer, same PdfReader API)

### beautifulsoup4 removal
- Remove `beautifulsoup4>=4.12.0` from requirements.txt in Phase 1
- Not in the target requirements list; dead weight

### sentence-transformers + ChromaDB embedding
- Use ChromaDB's built-in `SentenceTransformerEmbeddingFunction` — not pre-computing externally
- Model: `paraphrase-multilingual-MiniLM-L12-v2`
- Pass the EmbeddingFunction at collection creation time in `_init_store()`; ChromaDB handles embedding automatically on add and query
- Load lazily on first use (consistent with how OllamaClient is initialized)
- If sentence-transformers is not installed: raise a clear error with actionable message ("run pip install sentence-transformers>=3.0.0") — no silent fallback to English-only embedding

### ChromaDB collection
- Rename collection from `'wiki_knowledge_base'` to `'accounting_kb'`
- When startup detects an existing collection with an incompatible embedding model (or wrong name): delete silently and recreate — the vectorstore is a cache that can always be rebuilt by re-indexing the client folder

### Verification
- Inline smoke test in `rag/vector_store.py` (`if __name__ == "__main__":` block): index 3 Italian accounting phrases, query one, assert the correct result is top-1
- App startup check: `python -c "import app"` — verifies all pages import without errors after dependency changes (no need to run full Streamlit)

### Claude's Discretion
- Exact error message wording for missing sentence-transformers
- Whether to detect incompatible collection by metadata key or by exception handling
- Structure of the smoke test assertions

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Requirements
- `.planning/REQUIREMENTS.md` §Stack Cleanup — STACK-01 through STACK-04 define the acceptance criteria for each dependency change

### Codebase files to modify
- `requirements.txt` — 4 removals (langchain, langchain-ollama, sqlalchemy, beautifulsoup4, PyPDF2), 2 additions (pypdf, sentence-transformers)
- `core/file_processors.py` line 82 — PyPDF2 import to update
- `rag/adapters/local_folder.py` line 183 — PyPDF2 import to update
- `rag/vector_store.py` — _init_store() to add EmbeddingFunction; collection name rename; silent recreation logic; smoke test in __main__

### Files confirmed NOT needing changes
- `agents/base_agent.py` — already uses native OllamaClient, no LangChain dependency
- `core/llm_client.py` — already uses openai SDK directly
- All UI pages — no LangChain or PyPDF2 imports

No external specs or ADRs — all requirements are captured in REQUIREMENTS.md and decisions above.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `core/llm_client.py` OllamaClient: already native openai SDK — model for how the embedding client should also be lazy-initialized
- `rag/vector_store.py` add_chunks(): has an optional `embeddings` parameter — with EmbeddingFunction this becomes unused (ChromaDB handles it); can be left for now or simplified

### Established Patterns
- Lazy initialization: OllamaClient uses `self._client = None` + `_get_client()` pattern — same pattern for EmbeddingFunction initialization in vector_store
- Try/except on import: `_init_store()` already wraps `import chromadb` in try/except — same pattern for `import sentence_transformers`, but raise instead of silently falling back

### Integration Points
- `rag/vector_store.py` `_init_store()` is where EmbeddingFunction is injected at collection creation
- `rag/vector_store.py` `clear()` uses `self.client.delete_collection("wiki_knowledge_base")` — update collection name to 'accounting_kb'
- ChromaDB collection metadata currently has `{"description": "Knowledge Base for Wiki RAG"}` — update to `{"description": "AccountantNanoBot knowledge base", "embedding_model": "paraphrase-multilingual-MiniLM-L12-v2"}`

</code_context>

<specifics>
## Specific Ideas

- Use metadata key `embedding_model` on the collection to detect incompatibility at startup (compare stored model name vs expected model name; mismatch -> delete and recreate)
- The smoke test should use real accounting Italian phrases, e.g.: "fattura elettronica IVA", "conto corrente bancario", "liquidazione IVA trimestrale"

</specifics>

<deferred>
## Deferred Ideas

- pdfplumber addition — defer to the phase that actually uses it (Pipeline B, milestone 2); no feature in Phase 1 needs it
- Hardware detection + model recommendation — milestone 3+ (documented in MEMORY.md)

</deferred>

---

*Phase: 01-stack-cleanup*
*Context gathered: 2026-03-18*
