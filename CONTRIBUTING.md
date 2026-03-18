# Contributing — AccountantNanoBot

Grazie per l'interesse. Questo documento spiega come contribuire in modo coerente
con l'architettura e i vincoli del progetto.

---

## Principi fondamentali

Prima di qualsiasi contributo, tieni presenti questi vincoli architetturali:

**1. Calcoli fiscali e contabili in Python deterministico — mai nell'LLM.**
L'LLM serve solo per la chat e la classificazione iniziale dei documenti.
IVA, prima nota, scadenzario, LIPE: tutto Python puro, risultato sempre identico
a parita' di input.

**2. Conferma umana obbligatoria.**
Nessuna registrazione viene salvata nel database senza review esplicita
dell'operatore. Non rimuovere o aggirare questo step nei tuoi contributi.

**3. Privacy-first.**
I dati del cliente non escono mai dal computer locale. Non introdurre
chiamate a API esterne che trasmettono dati contabili o anagrafici.

**4. Stack minimo.**
Non aggiungere dipendenze senza necessita'. Vedi la sezione Stack sotto.

---

## Stack approvato

```
streamlit>=1.28.0
openai>=1.0.0          # client Ollama (protocollo compatibile OpenAI)
sqlite3                # stdlib Python, nessun ORM
chromadb>=0.4.0        # RAG locale
sentence-transformers>=3.0.0
pypdf>=4.0.0
pdfplumber>=0.11.0
python-docx>=1.1.0
reportlab>=4.0.0
lxml>=5.0.0
requests>=2.31.0
pyyaml>=6.0
python-dotenv>=1.0.0
```

**Non usare:** LangChain, SQLAlchemy, PyPDF2 (deprecato), datapizza-ai.
Se hai dubbi su una nuova dipendenza, apri prima una Issue di discussione.

---

## Tipi di contributo utili

- **Bug fix** nel parser FatturaPA (nuovi tipi documento, edge case XML)
- **Moduli fiscali deterministici** (liquidazione IVA, LIPE, F24, scadenzario)
- **Agenti operativi** (cash flow, scadenzario, analisi ritardi)
- **Miglioramenti UI** alle pagine Streamlit esistenti
- **Test** su fatture XML reali (vedi cartella `FATTURE/` per esempi)
- **Documentazione** — spiegazioni di regole fiscali italiane nel codice

Non sono prioritari: nuovi provider LLM cloud, funzionalita' multi-utente,
integrazioni con servizi esterni non ancora discusse in una Issue.

---

## Setup ambiente

```bash
git clone https://github.com/fab128k/accountantNanoBot.git
cd accountantNanoBot
python -m venv venv
source venv/bin/activate      # Linux/Mac
# venv\Scripts\activate       # Windows
pip install -r requirements.txt
```

Ollama deve essere in esecuzione con almeno un modello installato:

```bash
ollama serve
ollama pull llama3.2:3b
```

Avvio:

```bash
streamlit run app.py
```

---

## Workflow

```bash
# 1. Fork e clone del tuo fork
git clone https://github.com/TUO-USERNAME/accountantNanoBot.git

# 2. Branch dalla main
git checkout -b feature/nome-descrittivo   # nuova funzionalita'
git checkout -b fix/nome-bug               # bug fix

# 3. Sviluppa e testa localmente

# 4. Commit con Conventional Commits (senza emoji)
git commit -m "feat(parser): aggiungi supporto TD29 nota di debito"
git commit -m "fix(prima_nota): correggi calcolo IVA split payment"
git commit -m "docs: documenta override chain profilo cliente"

# 5. Push e Pull Request verso main
git push origin feature/nome-descrittivo
```

### Tipi di commit

| Tipo | Quando usarlo |
|---|---|
| `feat` | nuova funzionalita' |
| `fix` | correzione bug |
| `docs` | solo documentazione |
| `refactor` | refactoring senza cambio comportamento |
| `test` | aggiunta o correzione test |
| `chore` | dipendenze, config, build |

---

## Checklist PR

Prima di aprire una Pull Request:

- [ ] I calcoli fiscali producono risultato deterministico (stesso input = stesso output)
- [ ] Nessun dato contabile trasmesso a API esterne
- [ ] La conferma umana obbligatoria e' preservata
- [ ] Nessuna nuova dipendenza non approvata in requirements.txt
- [ ] Testato con almeno un file XML reale dalla cartella `FATTURE/`
- [ ] Commit message segue Conventional Commits

---

## Segnalare un bug

Apri una [Issue](https://github.com/fab128k/accountantNanoBot/issues) con:

- Versione Python e OS
- Comando eseguito o azione che ha scatenato il bug
- Traceback completo (copia dal terminale)
- File XML coinvolto se il bug riguarda il parser (puoi anonimizzare la P.IVA)

---

## Proporre una feature

Apri una Issue descrivendo:

- Il caso d'uso contabile/fiscale che vuoi coprire
- La norma di riferimento (se applicabile — es. art. 19 DPR 633/72 per IVA)
- Se il calcolo e' deterministico o richiede giudizio dell'LLM

Le proposte piu' facili da accettare sono quelle dove la logica fiscale e'
codificabile in Python puro senza ambiguita'.

---

## Licenza

Contribuendo accetti che il tuo codice sia rilasciato sotto licenza
GNU AGPL-3.0, come il resto del progetto. Vedi [LICENSE](LICENSE).
