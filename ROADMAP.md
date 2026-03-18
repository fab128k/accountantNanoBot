# ROADMAP — AccountantNanoBot

Piano di sviluppo verso la prima release pubblica (v1.0.0).

---

## Visione

Sistema multi-agente per gestione contabile e fiscale italiana.
L'utente punta alla cartella del cliente, poi comanda in chat.
Calcoli deterministici in Python. LLM solo per chat e classificazione.
Tutto locale, nessun dato del cliente in cloud.

Vedi [PHILOSOPHY.md](PHILOSOPHY.md) per le scelte architetturali.
Vedi [REVENUE_MODEL.md](REVENUE_MODEL.md) per il modello di business.

---

## Stato attuale — v0.1.0 (2026-03-18)

Funzionante: parser FatturaPA, partita doppia, agenti base, RAG, UI Streamlit.

Non ancora funzionante: pipeline ingestion completa, moduli IVA/LIPE,
profilo cliente con override chain, installer, SDI.

---

## Milestone 0 — Pulizia stack

**Prerequisito per tutto il resto. Fare prima di qualsiasi sviluppo funzionale.**

- [ ] **Rimuovi LangChain** (`langchain`, `langchain-ollama`) da requirements.txt.
  Riscrivi `core/llm_client.py` con openai SDK nativo.
  `base_agent.py` usa `client.invoke()` / `client.stream_invoke()` LangChain:
  sostituire con `openai.chat.completions.create(stream=True/False)`.

- [ ] **Rimuovi SQLAlchemy** da requirements.txt.
  Non e' usato: `accounting/db.py` gia' usa `sqlite3` stdlib nativo.

- [ ] **Sostituisci PyPDF2 con pypdf**.
  PyPDF2 e' ufficialmente deprecato. `pypdf>=4.0.0` e' drop-in replacement
  dello stesso maintainer.

- [ ] **Aggiungi sentence-transformers**.
  Per embedding semantici multilingua in ChromaDB.
  Modello: `paraphrase-multilingual-MiniLM-L12-v2` (420MB).
  Senza embedding di qualita' il RAG su testi italiani non funziona bene.

**requirements.txt target dopo pulizia:**
```
streamlit>=1.28.0
python-dotenv>=1.0.0
openai>=1.0.0
lxml>=5.0.0
chromadb>=0.4.0
sentence-transformers>=3.0.0
pypdf>=4.0.0
pdfplumber>=0.11.0
python-docx>=1.1.0
reportlab>=4.0.0
Pillow>=10.0.0
pyyaml>=6.0
requests>=2.31.0
```

---

## Milestone 1 — Core engine stabile (v0.2.0)

Obiettivo: il sistema indicizza una cartella cliente reale e propone
registrazioni corrette per tutte le fatture XML trovate.

- [ ] **swarm/context.py** — `ProcessingContext` condiviso tra agenti
  (cliente corrente, fatture caricate, stato ingestion, log operazioni)

- [ ] **swarm/base.py** — classe base per agenti sequenziali con accesso
  al contesto condiviso

- [ ] **ClientFolderScanner** — scansione ricorsiva cartella cliente,
  rilevamento automatico file XML/PDF/DOCX/ZIP, coda ingestion

- [ ] **Pipeline A — ingestion fatture XML**
  - Scansione cartella → lista file FatturaPA
  - Parse XML con `parsers/fattura_pa.py` esistente
  - Generazione prima nota con `accounting/prima_nota.py` esistente
  - Proposta registrazione per review umana
  - Salvataggio in SQLite dopo conferma

- [ ] **Profilo cliente — struttura dati**
  - Tabella `profilo_azienda` in SQLite: ATECO, regime fiscale,
    partita IVA, tipo attivita', note
  - Tabella `regole_override`: fornitore/tipo_spesa → aliquota IVA,
    percentuale deducibilita', motivazione, data conferma
  - Override chain applicato deterministicamente in prima nota

- [ ] **UI onboarding** — selezione cartella, wizard profilo cliente,
  conferma automatica ATECO → categoria fiscale

---

## Milestone 2 — Moduli fiscali deterministici (v0.3.0)

Obiettivo: generare liquidazione IVA e LIPE correte, con alert scadenze.
Tutto Python puro, zero LLM.

- [ ] **Liquidazione IVA periodica**
  - Calcolo IVA a debito/credito da registrazioni del periodo
  - Supporto contribuenti mensili e trimestrali
  - Generazione prospetto liquidazione in PDF (reportlab)
  - Generazione dati per F24 (XML strutturato)

- [ ] **LIPE — Liquidazioni Periodiche IVA**
  - Generazione automatica comunicazione quadro VP
  - Calcolo dati da liquidazioni periodiche gia' effettuate
  - Scadenze trimestrali (maggio, agosto, novembre, febbraio)
  - Export XML nel formato AdE

- [ ] **Scadenzario fiscale attivo**
  - Database scadenze parametrizzato su regime fiscale del cliente
    (estratto da `profilo_azienda`)
  - Alert preventivi a 30/15/7 giorni (notifica in UI)
  - Copertura: F24, LIPE, dichiarazioni, scadenze SDI

- [ ] **Alert regime forfettario**
  - Monitor ricavi vs soglia 85.000 EUR
  - Alert a 75.000, 80.000, 85.000 EUR con proiezione a fine anno
  - Suggerimento automatico in advisory chat

---

## Milestone 3 — Pipeline B e advisory chat (v0.4.0)

Obiettivo: il sistema conosce l'azienda del cliente oltre alle sue fatture,
e risponde a domande complesse in chat.

- [ ] **Pipeline B — ingestion documenti aziendali**
  - Parser per: visura camerale (PDF/XML), contratti (PDF/DOCX),
    bilanci (PDF), dichiarazioni fiscali pregresse (PDF)
  - LLM estrae fatti strutturati fiscalmente rilevanti:
    ATECO confermato, regime, soci, mandati agente, ruling AdE
  - Proposta profilo aggiornato per conferma commercialista
  - Salvataggio in `profilo_azienda` dopo conferma

- [ ] **Nuove tabelle SQLite Layer 2**
  - `contratti`: clienti/fornitori principali, condizioni pagamento
  - `kpi_storici`: fatturato mensile, margini, trend
  - `governance`: soci, cariche, deleghe

- [ ] **Advisory chat — cash flow 90 giorni**
  - Modello deterministico da fatture attive aperte + storico incassi
  - Risposta a: "fammi una previsione di cassa per il prossimo trimestre"
  - Grafici Streamlit interattivi (incasso atteso per settimana)

- [ ] **Advisory chat — analisi ritardi pagamenti**
  - Identifica fatture scadute per cliente
  - Modella impatto sul cash flow
  - Suggerisce azioni (sollecito, anticipo fatture)

- [ ] **Advisory chat — ottimizzazione fiscale conversazionale**
  - Risponde a domande come "ho 50.000 EUR di cassa, opzioni fiscali?"
  - Solo advisory (testo), i calcoli restano deterministici e separati
  - Context: profilo cliente + dati storici dal RAG

---

## Milestone 4 — Integrazioni esterne (v0.5.0)

Prerequisiti normativi per distribuzione pubblica.

- [ ] **Integrazione API intermediario SDI**
  - Scegliere un intermediario abilitato AgID (Aruba, Entaksi, Namirial)
  - Implementare adapter per trasmissione FatturaPA via API
  - Il processing XML resta locale; solo la trasmissione finale e' esterna
  - Opt-in esplicito dall'utente (Livello 3 revenue model)

- [ ] **Conservazione sostitutiva**
  - Adapter per servizio di conservazione certificato AgID
  - Il sistema locale gestisce il processing, il servizio esterno
    gestisce la conservazione legale a norma (10 anni)

- [ ] **Meccanismo aggiornamenti normativi**
  - Modulo `updater/` separato e aggiornabile indipendentemente
  - Aggiorna: specifiche FatturaPA (attualmente v1.9, TD29/RF20/etc.),
    aliquote IVA, tabelle CCNL, scadenze fiscali
  - File di regole firmati scaricati da server (Livello 1 revenue model)
  - Il core AGPL resta immutato; i dati normativi sono separati

---

## Milestone 5 — Distribuzione (v1.0.0)

- [ ] **Fase 1 — Installer script** (alpha con studi pilota)
  - `AVVIA.bat` (Windows): lancia Streamlit + Ollama in background,
    apre browser su localhost:8501
  - `avvia.sh` (Mac/Linux): equivalente per Unix
  - `INSTALLA.bat` / `installa.sh`: installa uv, crea venv, installa
    dipendenze, verifica/installa Ollama, scarica modello LLM,
    crea shortcut desktop
  - Rilevamento hardware: raccomanda modello in base alla RAM disponibile

- [ ] **Fase 2 — Installer professionale** (distribuzione pubblica)
  - Windows: Inno Setup con Python Embeddable (30MB, senza requisiti Python),
    venv pre-configurato, shortcut desktop + voce menu Start
  - Mac: Platypus (wrappa script .sh in .app bundle)
  - Linux: AppImage o .deb
  - **Non usare PyInstaller**: incompatibile con Streamlit + ChromaDB

- [ ] **Hardware detection + model recommendation**
  - Rileva RAM con `psutil` in fase onboarding
  - Logica: <8GB → phi3:mini, 8-16GB → llama3.2:3b,
    16-32GB → mistral:7b, >32GB → llama3.1:8b

---

## Backlog (post v1.0.0)

- **Active learning classificazione** — ogni correzione del commercialista
  migliora il modello di classificazione. Mapping fornitore → conto/IVA
  salvato localmente. Il sistema impara senza mandare dati in cloud.

- **Dashboard studio aggregata** (Livello 2 revenue model) — N clienti
  gestiti dallo stesso studio, KPI cross-cliente, scadenze aggregate

- **Export pacchetto cliente** — PDF + XML + report per consegna al cliente
  o a un secondo commercialista

---

## Legenda

```
✅ = Completato
🚧 = In sviluppo
[ ] = Da fare
```

---

*Ultimo aggiornamento: 2026-03-18*
*AccountantNanoBot — GNU AGPL-3.0*
