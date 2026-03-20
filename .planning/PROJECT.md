# AccountantNanoBot

## What This Is

Sistema multi-agente locale per la gestione contabile e fiscale italiana. L'utente punta a una cartella cliente e il sistema indicizza tutto automaticamente; poi comanda via chat in italiano ("fammi la contabilità di gennaio", "genera liquidazione IVA Q1"). I calcoli fiscali e le registrazioni sono deterministici in Python puro; l'LLM si occupa solo di chat, classificazione e advisory. Gira interamente in locale (Ollama + SQLite + ChromaDB), nessun dato esce dalla macchina.

Con v1.0 MVP la pipeline end-to-end è operativa: il sistema scansiona la cartella cliente, ingesta fatture XML e estratti conto bancari, produce registrazioni prima nota revisionate dall'accountant — senza inserimento manuale.

## Core Value

L'utente punta alla cartella del cliente, scrive in chat cosa vuole, e riceve registrazioni contabili corrette e PDF pronti — senza toccare un singolo campo manualmente.

## Requirements

### Validated

- ✓ UI Streamlit multi-pagina (dashboard, onboarding, fatture, prima nota, scanner) — v1.0
- ✓ Parser FatturaPA XML v1.2 (FPR12/FPA12) con dataclasses strutturate — existing
- ✓ Accounting core deterministico: partita doppia, piano dei conti OIC, SQLite — existing
- ✓ Agenti base (orchestrator keyword-routing, fatturazione_agent, memoria_agent) — existing
- ✓ RAG: ChromaDB + KnowledgeBaseManager + LocalFolderAdapter + TextChunker — existing
- ✓ LLM client OllamaClient (openai SDK via Ollama API-compatible) — existing
- ✓ Human-in-the-loop: registrazioni non salvate senza conferma utente — existing
- ✓ Deduplicazione fatture via hash SHA256 — existing
- ✓ Stack pulito: LangChain rimosso, SQLAlchemy rimosso, PyPDF2 sostituito con pypdf — v1.0
- ✓ base_agent.py riscritto con openai SDK nativo (no LangChain) — v1.0
- ✓ Embedding semantici multilingua (paraphrase-multilingual-MiniLM-L12-v2) in ChromaDB — v1.0
- ✓ swarm/context.py: ProcessingContext condiviso tra agenti — v1.0
- ✓ swarm/base.py: BaseSwarmAgent con interfaccia sequenziale standard — v1.0
- ✓ ClientFolderScanner: scansione automatica cartella cliente, classificazione file — v1.0
- ✓ Pipeline A: ingestion automatica fatture XML da cartella (riusa parser esistente) — v1.0
- ✓ Pipeline A: ingestion estratti conto bancari (CSV/OFX) con mapping IBAN→conto CoA — v1.0

### Active

<!-- Milestone 2: Pipeline B + Advisory + Moduli Fiscali -->

- [ ] Pipeline B: ingestion visura camerale (PDF/XML) per estrarre ATECO, regime fiscale, ragione sociale
- [ ] Pipeline B: ingestion contratti (PDF/DOCX) per identificare mandati, canoni, scadenze
- [ ] Pipeline B: ingestion bilanci storici (PDF/XLSX) per KPI storici
- [ ] Advisory chat: previsione cash flow a 90 giorni basata su fatture + storico incassi
- [ ] Advisory chat: alert automatico soglia regime forfettario (85.000 EUR)
- [ ] Advisory chat: analisi ritardi pagamenti con impatto cash flow
- [ ] Moduli fiscali: liquidazione IVA periodica (calcolo Python puro + generazione F24)
- [ ] Moduli fiscali: LIPE — generazione automatica comunicazione quadro VP
- [ ] Moduli fiscali: scadenzario fiscale attivo con alert preventivi

### Out of Scope

- Pipeline B profilo cliente (visura, contratti) — milestone 2
- Advisory chat avanzata (cash flow 90gg, alert regime forfettario) — milestone 2
- Moduli fiscali deterministici (liquidazione IVA, LIPE, F24) — milestone 2
- Distribuzione installer (.bat/.sh/.exe) — milestone 3
- Multi-utente / autenticazione — fuori scope definitivo per versione locale
- Cloud LLM (API Anthropic/OpenAI) nel core flow — architettura data-local by design
- Integrazione SDI intermediario (Aruba/Entaksi) — milestone 2+
- Conservazione sostitutiva a norma — delegare a servizio certificato (Aruba/Namirial)

## Context

- v1.0 MVP shipped 2026-03-20 — pipeline A end-to-end operativa
- ~12,000 LOC Python (4 fasi, 125 commit)
- Hardware target: 16GB RAM + 4GB VRAM; modello LLM default `llama3.2:3b`
- Agenti sequenziali (non paralleli) per vincoli hardware — un modello alla volta
- Stack pulito: openai SDK nativo, sqlite3 nativo, pypdf, sentence-transformers, ChromaDB
- Pattern swarm (ProcessingContext condiviso) implementato e agenti migrati
- Codebase mappata in `.planning/codebase/` (ARCHITECTURE.md, STACK.md, STRUCTURE.md, ecc.)
- Gerarchia regole fiscali: globale (legge) → categoria (ATECO) → override cliente confermato da accountant
- Avvio: `cd /home/admaiora/projects/accountantNanoBot && streamlit run app.py`

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
| Rimozione LangChain | Dipendenza inutilizzata, openai SDK nativo già presente e sufficiente | ✓ Good |
| Swarm pattern con ProcessingContext | Agenti stupidi + contesto condiviso = composabilità senza overhead | ✓ Good |
| pypdf invece di PyPDF2 | Stesso maintainer, drop-in replacement, PyPDF2 ufficialmente deprecato | ✓ Good |
| sentence-transformers con MiniLM multilingua | Qualità embedding italiani: modello 420MB, offline, coverage semantica elevata | ✓ Good |
| Raw byte peek per classificazione XML (512 bytes) | 100x più veloce di parse lxml completo durante scan — nessuna latenza percepibile | ✓ Good |
| db_path opzionale in process_folder() | Isolamento test senza monkeypatching — ogni test usa DB temporaneo | ✓ Good |
| st.text_input con solo key= (no value=) | Mixing key+value congela il widget in Streamlit — session_state è source of truth | ✓ Good |
| BankMovement _confirmed/_skipped come attributi dinamici | Non persistiti — reset a ogni "Avvia elaborazione" è il comportamento corretto | ✓ Good |

---
*Last updated: 2026-03-20 after v1.0 milestone*
