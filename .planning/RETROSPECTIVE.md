# Project Retrospective

*A living document updated after each milestone. Lessons feed forward into future planning.*

## Milestone: v1.0 — MVP

**Shipped:** 2026-03-20
**Phases:** 4 | **Plans:** 8 | **Sessions:** ~8

### What Was Built

- Stack cleanup: LangChain/SQLAlchemy/PyPDF2 rimossi, openai SDK nativo, pypdf, sentence-transformers
- ChromaDB con embedding multilingua (MiniLM) per RAG su testi italiani
- Architettura swarm: ProcessingContext + BaseSwarmAgent — fondamenta per agenti futuri
- ClientFolderScanner: classificazione automatica file in 6 categorie con byte peek XM
- Scanner UI integrata in Streamlit: sidebar, pagina dedicata, metriche per categoria
- Pipeline A completa: FatturaPA XML + CSV estratti conto → prima nota con 47 test
- Review UI: invoice cards + bank movement table con confirm/discard human-in-the-loop

### What Worked

- GSD workflow (plan→execute→verify) ha mantenuto il focus su ogni fase senza scope creep
- TDD per Pipeline A: 47 test scritti prima dell'implementazione hanno catturato edge case reali
- Swarm pattern additivo (estende BaseAccountingAgent): nessuna regressione su agenti esistenti
- Raw byte peek per classificazione XML: soluzione semplice ed efficiente trovata rapidamente
- Isolamento test con db_path opzionale: pattern pulito senza monkeypatching

### What Was Inefficient

- Sidebar folder input: race condition Streamlit con key/value mixing richiesto multiple sessioni di debug
- STATE.md percentuale rimasta a 0% per tutto il milestone (bug nel tool GSD, non bloccante)
- SUMMARY.md one_liner extraction non funzionante via CLI (accomplishments recuperati manualmente)

### Patterns Established

- `st.text_input` con solo `key=` (mai `value=` + `key=` insieme) — Streamlit session_state è source of truth
- `db_path` opzionale per isolamento test senza monkeypatching
- Byte peek 512 byte per classificazione XML FatturaPA — non parse completo durante scan
- `_confirmed/_skipped` come attributi dinamici su dataclass risultato — non persistiti, reset by design
- Ogni agente implementa `process(context: ProcessingContext) -> ProcessingContext` — interfaccia swarm

### Key Lessons

1. Il debito tecnico (LangChain non usato) bloccava la comprensione del codebase — eliminarlo prima era la mossa giusta
2. Streamlit ha vincoli non documentati sul mixing key/value nei widget — documentare immediatamente quando trovati
3. Il pattern TDD su pipeline data ha reso la review umana molto più rapida — applicare anche a Pipeline B
4. L'architettura swarm si è dimostrata additiva: agenti esistenti migrati senza regressioni in <1 ora

### Cost Observations

- Model mix: ~100% sonnet (claude-sonnet-4-6)
- Sessions: ~8 sessioni distribuite su 3 giorni
- Notable: GSD yolo mode ha ridotto le conferme interattive e accelerato l'esecuzione

---

## Cross-Milestone Trends

### Process Evolution

| Milestone | Sessions | Phases | Key Change |
|-----------|----------|--------|------------|
| v1.0 MVP | ~8 | 4 | Baseline — primo milestone con GSD workflow |

### Cumulative Quality

| Milestone | Tests | Coverage | Zero-Dep Additions |
|-----------|-------|----------|-------------------|
| v1.0 | 47+ | Pipeline A coverage | 0 (solo pulizia) |
