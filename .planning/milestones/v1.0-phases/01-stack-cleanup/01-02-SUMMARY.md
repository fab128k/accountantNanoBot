---
phase: 01-stack-cleanup
plan: 02
subsystem: database
tags: [chromadb, sentence-transformers, rag, embeddings, multilingual, italian]

# Dependency graph
requires:
  - phase: 01-stack-cleanup-01
    provides: requirements.txt with sentence-transformers>=3.0.0 added
provides:
  - ChromaDB vector store configured with paraphrase-multilingual-MiniLM-L12-v2 embeddings
  - Collection migration from wiki_knowledge_base to accounting_kb
  - Embedding model compatibility detection with silent delete-and-recreate
  - Inline smoke test for verifying Italian semantic retrieval
affects: [02-ingestion, 03-agents, rag-pipeline]

# Tech tracking
tech-stack:
  added: [sentence-transformers (via chromadb.utils.embedding_functions.SentenceTransformerEmbeddingFunction)]
  patterns: [lazy-init embedding function (_get_embedding_function), collection metadata versioning with embedding_model key, ImportError propagation for missing critical deps]

key-files:
  created: []
  modified: [rag/vector_store.py]

key-decisions:
  - "SentenceTransformerEmbeddingFunction from chromadb.utils used instead of raw sentence-transformers — ChromaDB handles embedding calls transparently"
  - "Missing sentence-transformers raises ImportError (not silent fallback) — RAG without multilingual embeddings is non-functional for Italian text"
  - "Collection metadata stores embedding_model key to detect incompatible existing collections and trigger silent recreation"
  - "wiki_knowledge_base -> accounting_kb migration runs automatically on first _init_store() call"

patterns-established:
  - "Lazy-init pattern for expensive resources: _embedding_fn = None in __init__, initialized on first _get_embedding_function() call"
  - "Collection metadata versioning: store embedding_model in metadata dict, compare on init to detect incompatibility"
  - "ImportError propagation: chromadb ImportError is caught+fallback, sentence-transformers ImportError is re-raised (raise)"

requirements-completed: [STACK-04]

# Metrics
duration: 2min
completed: 2026-03-18
---

# Phase 1 Plan 02: ChromaDB Multilingual Embeddings Summary

**ChromaDB reconfigured with paraphrase-multilingual-MiniLM-L12-v2 embeddings, collection renamed to accounting_kb, with automatic migration and embedding compatibility detection**

## Performance

- **Duration:** ~2 min
- **Started:** 2026-03-18T16:28:04Z
- **Completed:** 2026-03-18T16:30:00Z
- **Tasks:** 1 of 1
- **Files modified:** 1

## Accomplishments
- Replaced default English-only ChromaDB embeddings with paraphrase-multilingual-MiniLM-L12-v2 via SentenceTransformerEmbeddingFunction
- Renamed collection from wiki_knowledge_base to accounting_kb with proper metadata (description + embedding_model)
- Added automatic migration: old wiki_knowledge_base collection is silently deleted on first init
- Added embedding model compatibility check: if stored embedding_model != current model, collection is deleted and recreated
- Clear ImportError raised when sentence-transformers is missing (no silent fallback to broken embeddings)
- Added inline smoke test (`python rag/vector_store.py`) that indexes 3 Italian accounting phrases and verifies semantic IVA retrieval

## Task Commits

Each task was committed atomically:

1. **Task 1: Add multilingual embedding function and collection migration to vector_store.py** - `aefa3d1` (feat)

**Plan metadata:** `e6fdfcf` (docs: complete plan)

## Files Created/Modified
- `rag/vector_store.py` - ChromaDB vector store with SentenceTransformerEmbeddingFunction, collection migration, embedding compatibility check, and smoke test

## Decisions Made
- Used `chromadb.utils.embedding_functions.SentenceTransformerEmbeddingFunction` rather than calling sentence-transformers directly — ChromaDB manages embedding calls transparently during `collection.add()` and `collection.query()`, so no changes needed to `add_chunks` or `search` methods
- Missing sentence-transformers is a hard failure (ImportError propagated) — the RAG pipeline is non-functional for Italian text without multilingual embeddings, so a silent fallback would produce silently broken results
- Collection metadata key `embedding_model` enables future-proof compatibility: if the model changes again, old data is automatically invalidated and recreated

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required. sentence-transformers is listed in requirements.txt (added in plan 01-01). Model download happens automatically on first use.

## Next Phase Readiness
- ChromaDB vector store is ready for Italian document ingestion (Pipeline A and B)
- The smoke test can be run anytime to verify embedding quality: `cd /home/admaiora/projects/accountantNanoBot && python rag/vector_store.py`
- Depends on sentence-transformers being installed; if not, clear error message guides installation

---
*Phase: 01-stack-cleanup*
*Completed: 2026-03-18*
