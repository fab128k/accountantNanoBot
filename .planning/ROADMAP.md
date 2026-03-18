# Roadmap: AccountantNanoBot — Milestone 1

## Overview

Milestone 1 transforms the existing brownfield Streamlit/Python accounting app into a clean, extensible foundation capable of ingesting a client folder end-to-end. The journey moves through four natural delivery boundaries: eliminating technical debt in the stack, establishing the swarm agent architecture, wiring the client folder scanner into the UI, and completing Pipeline A so XML invoices and bank statements flow through to reviewable bookkeeping entries — all without manual data entry.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [x] **Phase 1: Stack Cleanup** - Remove dead dependencies and establish a clean technical baseline (completed 2026-03-18)
- [x] **Phase 2: Swarm Architecture** - Implement ProcessingContext and BaseSwarmAgent foundation (completed 2026-03-18)
- [ ] **Phase 3: Client Folder Scanner** - Enable folder selection and automatic file classification from UI
- [ ] **Phase 4: Pipeline A Ingestion** - Ingest invoices and bank statements into reviewable bookkeeping entries

## Phase Details

### Phase 1: Stack Cleanup
**Goal**: The codebase runs on a clean, minimal dependency set with no unused libraries and no deprecated packages
**Depends on**: Nothing (first phase)
**Requirements**: STACK-01, STACK-02, STACK-03, STACK-04
**Success Criteria** (what must be TRUE):
  1. `pip install -r requirements.txt` completes with no LangChain, SQLAlchemy, or PyPDF2 packages installed
  2. The app starts and all existing pages load without import errors after the dependency changes
  3. LLM calls from base_agent.py use openai SDK directly (`client.chat.completions.create`) with no LangChain wrapper
  4. ChromaDB accepts Italian text and returns semantically relevant results using the multilingual MiniLM embedding model
**Plans:** 2/2 plans complete

Plans:
- [x] 01-01-PLAN.md — Remove dead dependencies from requirements.txt and replace PyPDF2 with pypdf in all imports
- [x] 01-02-PLAN.md — Configure ChromaDB with multilingual sentence-transformers embedding model

### Phase 2: Swarm Architecture
**Goal**: A shared ProcessingContext and standard BaseSwarmAgent interface exist, and all existing agents conform to the pattern
**Depends on**: Phase 1
**Requirements**: SWARM-01, SWARM-02, SWARM-03
**Success Criteria** (what must be TRUE):
  1. `swarm/context.py` and `swarm/base.py` exist and are importable with no circular dependencies
  2. A ProcessingContext instance can be passed between two agents sequentially, accumulating results from each step
  3. The existing fatturazione_agent, memoria_agent, and orchestrator work correctly through the Streamlit UI after migration to BaseSwarmAgent
  4. The orchestrator routes a user chat message to the correct agent using the new pattern without regression
**Plans:** 2/2 plans complete

Plans:
- [ ] 02-01-PLAN.md — Create swarm/ package with ProcessingContext dataclass and BaseSwarmAgent ABC
- [ ] 02-02-PLAN.md — Migrate agents to BaseSwarmAgent and add route_with_context() to Orchestrator

### Phase 3: Client Folder Scanner
**Goal**: The user can point the system at a client folder and immediately see which files were found, classified by type, before any processing begins
**Depends on**: Phase 2
**Requirements**: SCAN-01, SCAN-02, SCAN-03
**Success Criteria** (what must be TRUE):
  1. Given a folder path, `ClientFolderScanner` returns a structured list of files classified into categories (FatturaXML, PDF, CSV, DOCX, TXT, Altro)
  2. The user can select a client folder from the Streamlit UI (onboarding page or sidebar) and see the classified file list rendered without writing any code
  3. After scanning, Pipeline A starts automatically for FatturaXML files found — the user does not need to trigger it manually
**Plans:** 1/2 plans executed

Plans:
- [ ] 03-01-PLAN.md — Create ClientFolderScanner core module and Pipeline A stub with full test coverage
- [ ] 03-02-PLAN.md — Wire Scanner UI into Streamlit app (sidebar folder selector, Scanner page, Pipeline A CTA)

### Phase 4: Pipeline A Ingestion
**Goal**: FatturaPA XML invoices and CSV/OFX bank statements from the client folder produce reviewable prima nota entries that the accountant confirms before saving
**Depends on**: Phase 3
**Requirements**: PIPE-01, PIPE-02, PIPE-03, PIPE-04
**Success Criteria** (what must be TRUE):
  1. All FatturaPA XML files in a scanned folder are parsed and produce a suggested prima nota entry per invoice, visible to the user for review
  2. A previously imported invoice (same SHA256 hash) is silently skipped — the user sees it marked as already imported, not as an error
  3. A CSV bank statement (with data, descrizione, importo, saldo columns) is parsed into a structured list of movements visible in the UI
  4. Each bank movement shows a suggested prima nota entry based on the IBAN→CoA mapping; the user can accept or correct each entry before it is saved to SQLite
**Plans**: TBD

## Progress

**Execution Order:**
Phases execute in numeric order: 1 → 2 → 3 → 4

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Stack Cleanup | 2/2 | Complete   | 2026-03-18 |
| 2. Swarm Architecture | 2/2 | Complete   | 2026-03-18 |
| 3. Client Folder Scanner | 1/2 | In Progress|  |
| 4. Pipeline A Ingestion | 0/TBD | Not started | - |
