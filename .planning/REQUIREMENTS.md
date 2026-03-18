# Requirements: AccountantNanoBot — Milestone 1

**Defined:** 2026-03-18
**Core Value:** L'utente punta alla cartella cliente, scrive in chat cosa vuole, e riceve registrazioni contabili corrette e PDF pronti — senza toccare un singolo campo manualmente.

## v1 Requirements

### Stack Cleanup

- [ ] **STACK-01**: Il sistema usa solo openai SDK nativo per le chiamate LLM (LangChain rimosso da requirements.txt e da base_agent.py)
- [ ] **STACK-02**: SQLAlchemy rimosso da requirements.txt (non era usato; sqlite3 nativo rimane)
- [ ] **STACK-03**: PyPDF2 sostituito con pypdf>=4.0.0 in requirements.txt e in tutti i file che lo importano
- [ ] **STACK-04**: sentence-transformers>=3.0.0 aggiunto a requirements.txt; ChromaDB configurato per usare il modello `paraphrase-multilingual-MiniLM-L12-v2` per embedding multilingua

### Swarm Architecture

- [ ] **SWARM-01**: Esiste `swarm/context.py` con classe `ProcessingContext` che aggrega stato condiviso tra agenti (cliente corrente, file in elaborazione, risultati intermedi, errori)
- [ ] **SWARM-02**: Esiste `swarm/base.py` con classe `BaseSwarmAgent` che definisce l'interfaccia standard per gli agenti (metodo `process(context: ProcessingContext) -> ProcessingContext`)
- [ ] **SWARM-03**: Gli agenti esistenti (fatturazione_agent, memoria_agent, orchestrator) sono migrati al pattern BaseSwarmAgent mantenendo compatibilità con l'UI Streamlit esistente

### Client Folder Scanner

- [ ] **SCAN-01**: Esiste `scanner/client_folder_scanner.py` che data una cartella restituisce una lista strutturata di file classificati per tipo (FatturaXML, PDF, CSV, DOCX, TXT, Altro)
- [ ] **SCAN-02**: L'utente può selezionare la cartella cliente da UI Streamlit (pagina onboarding o sidebar); il sistema avvia la scansione e mostra i file trovati divisi per categoria
- [ ] **SCAN-03**: Dopo la scansione, il sistema avvia automaticamente Pipeline A per i file FatturaXML trovati senza intervento manuale dell'utente

### Pipeline A — Ingestion

- [ ] **PIPE-01**: Esiste `pipeline/pipeline_a.py` che dato un percorso cartella legge tutti i file FatturaXML, li invia al parser FatturaPA esistente, e genera per ciascuno una registrazione suggerita (prima nota)
- [ ] **PIPE-02**: Le fatture già importate (tracked per hash SHA256 in `fatture_importate`) sono saltate automaticamente nella pipeline senza errore
- [ ] **PIPE-03**: Esiste `pipeline/bank_statement_parser.py` che legge estratti conto in formato CSV (colonne: data, descrizione, importo, saldo) e OFX, producendo una lista di movimenti bancari strutturati
- [ ] **PIPE-04**: Il sistema suggerisce la registrazione prima nota per ogni movimento bancario usando una mappatura IBAN→conto CoA configurabile per cliente; l'utente conferma o corregge prima del salvataggio

## v2 Requirements

### Pipeline B — Documenti Aziendali

- **PIPB-01**: Ingestion visura camerale (PDF/XML) per estrarre ATECO, regime fiscale, ragione sociale
- **PIPB-02**: Ingestion contratti (PDF/DOCX) per identificare mandati, canoni, scadenze
- **PIPB-03**: Ingestion bilanci storici (PDF/XLSX) per KPI storici

### Advisory Chat Avanzata

- **ADV-01**: Previsione cash flow a 90 giorni basata su fatture attive/passive + storico incassi
- **ADV-02**: Alert automatico soglia regime forfettario (85.000 EUR)
- **ADV-03**: Analisi ritardi pagamenti con impatto cash flow

### Moduli Fiscali Deterministici

- **FISC-01**: Liquidazione IVA periodica (calcolo Python puro + generazione F24)
- **FISC-02**: LIPE: generazione automatica comunicazione quadro VP
- **FISC-03**: Scadenzario fiscale attivo con alert preventivi

### Distribuzione

- **DIST-01**: Installer script .bat (Windows) + .sh (Linux/Mac) per installazione one-click
- **DIST-02**: Hardware detection + model recommendation in fase di onboarding

## Out of Scope

| Feature | Reason |
|---------|--------|
| Multi-utente / autenticazione | App locale single-user by design |
| Cloud LLM nel core flow | Data locality obbligatoria; nessun dato cliente in cloud |
| Integrazione SDI intermediario | Barriera regolamentare AgID; richiede certificazioni specifiche |
| Conservazione sostitutiva a norma | Delegare a servizio certificato (Aruba/Namirial); fuori scope MVP |
| App mobile | Web-first; mobile non richiesto |
| Real-time sync con software contabili (TeamSystem, Zucchetti) | Complessità eccessiva per v1; formato export manuale sufficiente |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| STACK-01 | Phase 1 | Pending |
| STACK-02 | Phase 1 | Pending |
| STACK-03 | Phase 1 | Pending |
| STACK-04 | Phase 1 | Pending |
| SWARM-01 | Phase 2 | Pending |
| SWARM-02 | Phase 2 | Pending |
| SWARM-03 | Phase 2 | Pending |
| SCAN-01 | Phase 3 | Pending |
| SCAN-02 | Phase 3 | Pending |
| SCAN-03 | Phase 3 | Pending |
| PIPE-01 | Phase 4 | Pending |
| PIPE-02 | Phase 4 | Pending |
| PIPE-03 | Phase 4 | Pending |
| PIPE-04 | Phase 4 | Pending |

**Coverage:**
- v1 requirements: 14 total
- Mapped to phases: 14
- Unmapped: 0 ✓

---
*Requirements defined: 2026-03-18*
*Last updated: 2026-03-18 after initial definition*
