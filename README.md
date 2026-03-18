# AccountantNanoBot

> Sistema multi-agente per la gestione contabile e fiscale italiana.
> Punta alla cartella del cliente, poi comanda in italiano.

[![Version](https://img.shields.io/badge/version-0.1.0-blue.svg)](https://github.com/fab128k/accountantNanoBot/releases)
[![Python](https://img.shields.io/badge/python-3.10+-green.svg)](https://python.org)
[![Streamlit](https://img.shields.io/badge/streamlit-1.28+-red.svg)](https://streamlit.io)
[![License](https://img.shields.io/badge/license-AGPL--3.0-blue.svg)](LICENSE)

---

## Cos'e'

AccountantNanoBot e' un assistente contabile locale che:

1. **Indicizza la cartella cliente** — FatturaPA XML, PDF, DOCX, estratti conto
2. **Elabora in automatico** — partita doppia, piano dei conti OIC, liquidazione IVA
3. **Risponde in chat** — "fammi la contabilita' di gennaio 2026", "genera LIPE Q1"
4. **Genera PDF deterministici** — nessun dato sensibile esce dal computer

I calcoli fiscali e contabili sono in Python puro. L'LLM serve solo per la chat e la classificazione iniziale. Ogni registrazione richiede conferma umana prima di essere salvata.

---

## Features

- **Parser FatturaPA** — supporto XML v1.2+ (TD01–TD29, tutti i tipi documento)
- **Partita doppia** — piano dei conti OIC con regole personalizzabili per cliente
- **Profilo cliente** — override chain per regole fiscali (generale → categoria ATECO → specifico cliente)
- **Advisory chat** — LLM locale via Ollama, risponde a domande su cash flow, scadenze, ottimizzazione fiscale
- **SQLite locale** — zero cloud, zero telemetria, dati sempre sul tuo hardware
- **Conferma umana obbligatoria** — nessuna registrazione salvata senza review dell'operatore

---

## Architettura

```
accountantNanoBot/
├── app.py                    # Entry point Streamlit (router multipagina)
│
├── parsers/
│   └── fattura_pa.py         # Parser FatturaPA XML v1.2+
│
├── accounting/
│   ├── piano_dei_conti.py    # Piano dei conti OIC
│   ├── prima_nota.py         # Registrazioni partita doppia
│   └── db.py                 # SQLite (sqlite3 nativo)
│
├── agents/
│   ├── base_agent.py         # BaseAccountingAgent (RAG + prompt)
│   ├── orchestrator.py       # Orchestratore sequenziale
│   ├── fatturazione_agent.py # Agente elaborazione fatture
│   └── memoria_agent.py      # Agente memoria e profilo cliente
│
├── core/
│   ├── llm_client.py         # Client Ollama (openai SDK)
│   └── file_processors.py    # Estrazione testo da PDF, DOCX, XML
│
├── rag/
│   ├── manager.py            # KnowledgeBaseManager (ChromaDB)
│   ├── vector_store.py       # Store vettoriale locale
│   └── adapters/
│       └── local_folder.py   # Indicizzazione cartella cliente
│
└── ui/pages/
    ├── dashboard.py          # Dashboard principale
    ├── onboarding.py         # Setup cliente + scansione cartella
    └── prima_nota.py         # Review e conferma registrazioni
```

---

## Requisiti

- Python 3.10+
- [Ollama](https://ollama.com) con un modello installato (es. `llama3.2:3b`)
- 8 GB RAM minimo (16 GB consigliati)

---

## Installazione

```bash
git clone https://github.com/fab128k/accountantNanoBot.git
cd accountantNanoBot
python -m venv venv
source venv/bin/activate       # Linux/Mac
# oppure: venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

---

## Avvio

```bash
# Assicurati che Ollama sia in esecuzione
ollama serve

# In un altro terminale
streamlit run app.py
```

Apri il browser su `http://localhost:8501`.

---

## Modello LLM consigliato

| RAM disponibile | Modello consigliato |
|---|---|
| 8 GB | `phi3:mini` |
| 16 GB | `llama3.2:3b` o `qwen2.5:3b` |
| 32 GB+ | `mistral:7b` |

```bash
ollama pull llama3.2:3b
```

---

## Stato del progetto

In sviluppo attivo. Funzionalita' implementate:

- [x] Parser FatturaPA XML
- [x] Piano dei conti OIC + prima nota
- [x] Agenti base con RAG
- [x] UI Streamlit multipagina (dashboard, onboarding, prima nota)
- [ ] Pulizia stack (rimozione LangChain, SQLAlchemy, PyPDF2 deprecato)
- [ ] Pipeline ingestion cartella cliente completa
- [ ] Profilo cliente con override chain
- [ ] Liquidazione IVA + F24
- [ ] LIPE automatica
- [ ] Installer script Windows/Mac/Linux

Vedi [ROADMAP.md](ROADMAP.md) per il piano completo.

---

## Modello di revenue

Freemium a 4 livelli, coerente con la licenza AGPL-3.0.
Vedi [REVENUE_MODEL.md](REVENUE_MODEL.md).

---

## Licenza

GNU Affero General Public License v3.0 — vedi [LICENSE](LICENSE).

Il codice core e' open source. Chi modifica e distribuisce deve rilasciare
le modifiche. Chi usa internamente (studio, azienda) non ha obblighi di rilascio.

---

## Contributing

Contribuzioni benvenute. Vedi [CONTRIBUTING.md](CONTRIBUTING.md).

```bash
git checkout -b feature/nome-feature
git commit -m "feat: descrizione"
git push origin feature/nome-feature
# apri Pull Request su GitHub
```
