# CHANGELOG

Tutte le modifiche significative al progetto sono documentate in questo file.
Formato: [Keep a Changelog](https://keepachangelog.com/it/1.0.0/) —
Versioning: [Semantic Versioning](https://semver.org/lang/it/).

---

## [Unreleased]

### Da fare (prima release pubblica)
- Pulizia stack: rimozione LangChain, SQLAlchemy, PyPDF2 → pypdf
- Pipeline ingestion cartella cliente completa
- Profilo cliente con override chain (globale → ATECO → specifico cliente)
- Liquidazione IVA + generazione F24
- LIPE automatica (comunicazione quadro VP)
- Scadenzario fiscale attivo con alert
- Installer script Windows/Mac/Linux

---

## [0.1.0] - 2026-03-18 — Bootstrap progetto

Prima versione funzionante. Fork da
[datapizza-streamlit-interface v1.12.1](https://github.com/EnzoGitHub27/datapizza-streamlit-interface)
come base Streamlit, con sostituzione completa della logica applicativa.

### Added

**Infrastruttura progetto**
- Licenza GNU AGPL-3.0
- `REVENUE_MODEL.md` — modello freemium a 4 livelli (gratuito, aggiornamenti,
  studio, SDI revenue share)
- `README.md` riscritto per il progetto contabile
- `CONTRIBUTING.md` con vincoli architetturali specifici (determinismo fiscale,
  conferma umana obbligatoria, privacy-first, stack approvato)

**Parser FatturaPA** (`parsers/fattura_pa.py`)
- Parser XML completo per FatturaPA v1.2
- Supporto intestazione trasmissione, cedente/cessionario, dati generali fattura
- Estrazione righe dettaglio, aliquote IVA, riepilogo per aliquota
- Gestione dati pagamento e sconto/maggiorazione

**Contabilita'** (`accounting/`)
- Piano dei conti OIC (`piano_dei_conti.py`) — struttura a 5 macrocategorie
  (attivo, passivo, patrimonio netto, costi, ricavi) con sottoconti standard
- Prima nota in partita doppia (`prima_nota.py`) — generazione automatica
  scritture da fattura attiva/passiva, calcolo IVA, righe dare/avere bilanciate
- Database SQLite nativo (`db.py`) — tabelle `prima_nota`, `righe_prima_nota`,
  `fatture`; auto-init senza ORM

**Agenti** (`agents/`)
- `BaseAccountingAgent` — pattern RAG-augmented con ChromaDB locale,
  client Ollama via openai SDK, system prompt contabile in italiano
- `Orchestrator` — coordinamento sequenziale agenti (hardware 16GB RAM)
- `FatturazioneAgent` — elaborazione fatture: parse XML → prima nota →
  proposta registrazione per review umana
- `MemoriaAgent` — recupero contesto storico cliente da RAG

**Core** (`core/`)
- `LLMClient` — wrapper Ollama (protocollo openai-compatible), supporto
  streaming e non-streaming, timeout configurabile
- `FileProcessors` — estrazione testo da PDF (pypdf), DOCX (python-docx),
  XML (lxml), TXT

**RAG** (`rag/`)
- `KnowledgeBaseManager` — ChromaDB locale, embedding sentence-transformers
  multilingua (`paraphrase-multilingual-MiniLM-L12-v2`)
- `LocalFolderAdapter` — indicizzazione ricorsiva cartella cliente
- `TextChunker` — chunking intelligente con overlap configurabile

**UI Streamlit** (`ui/pages/`, `app.py`)
- Router multipagina: dashboard, onboarding, prima nota
- `Dashboard` — stato connessione Ollama, statistiche DB, fatture recenti
- `Onboarding` — selezione cartella cliente, avvio indicizzazione RAG,
  configurazione profilo azienda
- `PrimaNota` — visualizzazione proposte agente, conferma/rigetto
  registrazione, salvataggio in SQLite

### Technical

- Stack: Streamlit 1.28+, openai SDK (client Ollama), sqlite3 stdlib,
  ChromaDB, sentence-transformers, lxml, pypdf, pdfplumber, reportlab
- LLM default: `llama3.2:3b` via Ollama locale (localhost:11434)
- DB: `data/accounting.db` auto-init all'avvio
- Avvio: `streamlit run app.py`

### Note

Il fork originale (DeepAiUG chat socratica) e' stato mantenuto come base
per il layer Streamlit, RAG e file processor. Tutta la logica contabile,
fiscale e gli agenti sono nuovi. La git history riflette la provenienza
del fork — i commit precedenti a questa versione appartengono al progetto
originale e non riguardano la funzionalita' contabile.

---

## Legenda

- `Added` — nuove funzionalita'
- `Changed` — modifiche a funzionalita' esistenti
- `Fixed` — correzioni bug
- `Removed` — funzionalita' rimosse
- `Security` — fix di sicurezza
- `Deprecated` — funzionalita' che saranno rimosse

---

*AccountantNanoBot — GNU AGPL-3.0*
