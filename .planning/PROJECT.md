# AccountantNanoBot

## What This Is

Sistema multi-agente locale per la gestione contabile e fiscale italiana. L'utente punta a una cartella cliente e il sistema indicizza tutto automaticamente; poi comanda via chat in italiano ("fammi la contabilità di gennaio", "genera liquidazione IVA Q1"). I calcoli fiscali e le registrazioni sono deterministici in Python puro; l'LLM si occupa solo di chat, classificazione e advisory. Gira interamente in locale (Ollama + SQLite + ChromaDB), nessun dato esce dalla macchina.

## Core Value

L'utente punta alla cartella del cliente, scrive in chat cosa vuole, e riceve registrazioni contabili corrette e PDF pronti — senza toccare un singolo campo manualmente.

## Requirements

### Validated

<!-- Shipped and confirmed valuable from existing codebase. -->

- ✓ UI Streamlit multi-pagina (dashboard, onboarding, fatture, prima nota) — existing
- ✓ Parser FatturaPA XML v1.2 (FPR12/FPA12) con dataclasses strutturate — existing
- ✓ Accounting core deterministico: partita doppia, piano dei conti OIC, SQLite — existing
- ✓ Agenti base (orchestrator keyword-routing, fatturazione_agent, memoria_agent) — existing
- ✓ RAG: ChromaDB + KnowledgeBaseManager + LocalFolderAdapter + TextChunker — existing
- ✓ LLM client OllamaClient (openai SDK via Ollama API-compatible) — existing
- ✓ Human-in-the-loop: registrazioni non salvate senza conferma utente — existing
- ✓ Deduplicazione fatture via hash SHA256 — existing

### Active

<!-- Milestone 1: stack cleanup + swarm foundations + Pipeline A -->

- [ ] Stack pulito: LangChain rimosso, SQLAlchemy rimosso, PyPDF2 sostituito con pypdf, sentence-transformers aggiunto
- [ ] base_agent.py riscritto con openai SDK nativo (no LangChain)
- [ ] Embedding semantici multilingua (paraphrase-multilingual-MiniLM-L12-v2) in ChromaDB
- [ ] swarm/context.py: ProcessingContext condiviso tra agenti
- [ ] swarm/base.py: BaseSwarmAgent con interfaccia sequenziale standard
- [ ] ClientFolderScanner: scansione automatica cartella cliente, classificazione file
- [ ] Pipeline A: ingestion automatica fatture XML da cartella (riusa parser esistente)
- [ ] Pipeline A: ingestion estratti conto bancari (CSV/OFX) con mapping IBAN→conto CoA

### Out of Scope

- Pipeline B (visura camerale, contratti, bilanci) — milestone 2
- Advisory chat avanzata (cash flow 90gg, alert regime forfettario) — milestone 2
- Moduli fiscali deterministici (liquidazione IVA, LIPE, F24) — milestone 2
- Distribuzione installer (.bat/.sh/.exe) — milestone 3
- Multi-utente / autenticazione — fuori scope definitivo per versione locale
- Cloud LLM (API Anthropic/OpenAI) nel core flow — architettura data-local by design
- Integrazione SDI intermediario (Aruba/Entaksi) — milestone 2+

## Context

- Progetto avviato come fork di datapizza-streamlit-interface; ora indipendente
- Hardware target: 16GB RAM + 4GB VRAM; modello LLM default `llama3.2:3b`
- Agenti sequenziali (non paralleli) per vincoli hardware — un modello alla volta
- Codebase mappata in `.planning/codebase/` (ARCHITECTURE.md, STACK.md, STRUCTURE.md, STACK.md, ecc.)
- Stack attuale ha debito tecnico documentato: LangChain/SQLAlchemy inutilizzati in requirements.txt, PyPDF2 deprecato
- Pattern swarm (ProcessingContext condiviso) definito in `memory/candidate_solution_1.md`
- Gerarchia regole fiscali: globale (legge) → categoria (ATECO) → override cliente confermato da accountant

## Constraints

- **Hardware**: max 16GB RAM, 4GB VRAM — modelli LLM max 7B; un modello alla volta
- **Data locality**: nessun dato cliente in cloud — Ollama locale obbligatorio per core flow
- **Determinismo**: calcoli contabili e fiscali mai delegati a LLM — solo Python puro
- **Human-in-the-loop**: ogni registrazione richiede conferma esplicita prima del salvataggio
- **Python**: 3.12+ (in uso 3.13.1)
- **UI**: Streamlit locale (localhost:8501) — no SPA, no Electron

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Ollama-only per core LLM | Data locality, zero costi API, funziona offline | ✓ Good |
| SQLite nativo (no ORM) | Semplicità, no deps extra, scala per volumi contabili | ✓ Good |
| Calcoli fiscali deterministici in Python | Affidabilità 100% su operazioni ripetibili, no allucinazioni LLM | ✓ Good |
| Agenti sequenziali (no parallel) | Vincolo hardware 16GB/4GB VRAM, un modello LLM alla volta | ✓ Good |
| Streamlit (no Electron/desktop) | Web app locale più semplice, niente packaging complesso | ✓ Good |
| Rimozione LangChain | Dipendenza inutilizzata, openai SDK nativo già presente e sufficiente | — Pending |
| Swarm pattern con ProcessingContext | Agenti stupidi + contesto condiviso = composabilità senza overhead | — Pending |

---
*Last updated: 2026-03-18 after initialization*
