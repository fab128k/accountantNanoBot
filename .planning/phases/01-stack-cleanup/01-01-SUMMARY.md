---
phase: 01-stack-cleanup
plan: 01
subsystem: infra
tags: [requirements, pypdf, sentence-transformers, chromadb, openai, langchain-removal]

# Dependency graph
requires: []
provides:
  - Clean requirements.txt with no dead or deprecated packages
  - pypdf>=4.0.0 for PDF extraction (drop-in PyPDF2 replacement)
  - sentence-transformers>=3.0.0 for multilingual Italian RAG embeddings
  - All Python files use pypdf imports, zero PyPDF2 references
affects: [02-llm-client, 03-base-agent, 04-rag-pipeline]

# Tech tracking
tech-stack:
  added: [pypdf>=4.0.0, sentence-transformers>=3.0.0]
  patterns: [openai SDK direct (no LangChain wrapper), sqlite3 native (no SQLAlchemy), pypdf for PDF extraction]

key-files:
  created: []
  modified:
    - requirements.txt
    - core/file_processors.py
    - rag/adapters/local_folder.py

key-decisions:
  - "Removed LangChain and langchain-ollama: replaced by openai SDK direct in llm_client.py"
  - "Removed SQLAlchemy: sqlite3 native already used throughout accounting/"
  - "Removed beautifulsoup4 from requirements: HTML parsing is optional fallback, gracefully degraded"
  - "Replaced PyPDF2 with pypdf>=4.0.0: same maintainer, drop-in replacement, not deprecated"
  - "Added sentence-transformers>=3.0.0: required for quality Italian-language embeddings in ChromaDB"
  - "Updated python-docx to >=1.1.0: current stable release"

patterns-established:
  - "PDF extraction: from pypdf import PdfReader (never PyPDF2)"
  - "ImportError messages reference correct package name and pip install command"

requirements-completed: [STACK-01, STACK-02, STACK-03]

# Metrics
duration: 2min
completed: 2026-03-18
---

# Phase 1 Plan 01: Stack Cleanup — Dependency Pruning Summary

**Removed LangChain, SQLAlchemy, PyPDF2, and beautifulsoup4 from requirements.txt; added pypdf>=4.0.0 and sentence-transformers>=3.0.0; updated all Python imports to use pypdf**

## Performance

- **Duration:** 2 min
- **Started:** 2026-03-18T16:23:33Z
- **Completed:** 2026-03-18T16:25:00Z
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments

- requirements.txt now contains exactly the target dependency set: no dead or deprecated packages
- Both Python files that imported PyPDF2 now import from pypdf with correct error messages and docstrings
- sentence-transformers added to enable quality multilingual embeddings for Italian-language RAG pipeline

## Task Commits

Each task was committed atomically:

1. **Task 1: Clean requirements.txt** - `85c3eaf` (chore)
2. **Task 2: Replace PyPDF2 imports with pypdf in Python files** - `ae60465` (feat)

## Files Created/Modified

- `requirements.txt` - Removed langchain, langchain-ollama, sqlalchemy, beautifulsoup4, PyPDF2; added pypdf>=4.0.0, sentence-transformers>=3.0.0; updated python-docx to >=1.1.0
- `core/file_processors.py` - `from pypdf import PdfReader`, updated ImportError message
- `rag/adapters/local_folder.py` - `from pypdf import PdfReader`, updated docstring and ImportError message

## Decisions Made

- LangChain removed: `core/llm_client.py` already wraps openai SDK directly; `base_agent.py` still references LangChain-style methods but that is addressed in plan 01-02
- SQLAlchemy removed: `accounting/db.py` uses sqlite3 natively throughout; SQLAlchemy was never instantiated
- beautifulsoup4 removed from requirements.txt but `_load_html_file` in `local_folder.py` retains graceful fallback (imports bs4 optionally, prints warning if absent) — this is intentional optional dependency behavior
- sentence-transformers added now so the full environment can be installed before RAG pipeline work begins in phase 2

## Deviations from Plan

None - plan executed exactly as written.

**Note:** During verification, grep detected residual `beautifulsoup4` strings in `rag/adapters/local_folder.py` docstrings and error messages for the HTML loader. These are intentional: the HTML parsing function uses bs4 as an optional dependency with graceful fallback. The plan's goal was to remove it from `requirements.txt` (done) and replace PyPDF2 (done). The HTML loader's optional bs4 usage is out of scope and documented below as deferred.

## Issues Encountered

None.

## Deferred Items

- `rag/adapters/local_folder.py` `_load_html_file`: references `beautifulsoup4` as an optional dep with graceful fallback. If HTML support is not needed for the accounting use case, this method could be removed entirely. Deferred to phase 2 scope review.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- requirements.txt is clean — ready for `pip install -r requirements.txt` in a fresh venv
- Plan 01-02 can now rewrite `core/llm_client.py` and `agents/base_agent.py` using openai SDK direct (LangChain is removed from deps)
- All PDF code now uses pypdf; no import errors will occur on missing PyPDF2

---
*Phase: 01-stack-cleanup*
*Completed: 2026-03-18*
