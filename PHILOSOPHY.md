# PHILOSOPHY.md
## Perche' AccountantNanoBot fa le scelte che fa

**Progetto:** AccountantNanoBot
**Ultima revisione:** 2026-03-18

---

## La domanda fondamentale

In contabilita' e fiscalita', cosa deve fare l'AI e cosa deve fare il commercialista?

La risposta di questo progetto:

- **L'AI fa** la parte meccanica, ripetitiva, soggetta a regole codificabili:
  parsing dei file, calcoli IVA, registrazioni in partita doppia, scadenzario.
- **Il commercialista fa** la parte che richiede giudizio: validare il profilo
  fiscale del cliente, confermare ogni registrazione, prendere decisioni sugli
  edge case.

Questa divisione non e' ovvia. La maggior parte dei software AI contabili
prova a farla fare tutta all'AI. Questo e' il problema che AccountantNanoBot
cerca di risolvere.

---

## Parte 1 — Il problema del probabilismo nei calcoli fiscali

### 1.1 I modelli LLM sono probabilistici per definizione

Un LLM risponde a una domanda producendo il testo statisticamente piu' probabile
dato il contesto. Per molti usi questo e' sufficiente. Per la contabilita' no.

**Esempio concreto:**
Una fattura del fornitore X per telefonia. IVA detraibile al 50% secondo la
regola generale italiana (art. 19-bis1, lettera g), DPR 633/72).
Ma il cliente ha documentazione che dimostra uso 100% professionale del
telefono — quindi IVA detraibile al 100%.

Se chiedi a un LLM ogni volta che elabori una fattura di telefonia dello stesso
fornitore, potresti ottenere risposte diverse:
- "50% detraibile" (regola generale)
- "dipende dall'uso" (risposta vaga)
- "100% se documentato" (risposta corretta per questo cliente)

La varianza non e' accettabile. Su 200 fatture annue dello stesso tipo, vuoi
sempre la stessa risposta — quella giusta per quel cliente specifico.

### 1.2 La soluzione: chiedi una volta, salva la risposta

AccountantNanoBot separa il momento della decisione dal momento dell'applicazione:

1. **Prima volta:** il sistema propone la regola, il commercialista valida.
2. **Ogni volta successiva:** la regola validata viene applicata deterministicamente
   in Python — zero LLM, zero varianza.

La prima volta costa attenzione. Le 199 volte successive costano zero.
I concorrenti che delegano ogni calcolo all'LLM pagano il costo di attenzione
ogni volta, e non hanno garanzia di coerenza.

---

## Parte 2 — La gerarchia delle regole

Il motore di regole e' il cuore del vantaggio competitivo del progetto.

### Override chain

```
Livello 1 — Regola globale
  Legge italiana (hard-coded in Python)
  Esempio: telefonia → IVA 50% detraibile, costo 80% deducibile

Livello 2 — Regola di categoria
  Derivata da ATECO / tipo attivita'
  Esempio: agente di commercio (ATECO 4619) → auto costo 80% deducibile

Livello 3 — Override specifico cliente
  Documentato e validato dal commercialista, salvato in SQLite
  Esempio: cliente con documentazione uso 100% professionale telefono
           → IVA 100% detraibile
```

Ogni override e' tracciato: chi lo ha approvato, quando, su quale base documentale.
Non e' un'impostazione arbitraria — e' una decisione professionale registrata.

### Perche' non un "AI che impara"

Si potrebbe immaginare un sistema che impara autonomamente dagli override
del commercialista, senza che lui debba confermare esplicitamente ogni regola.

Abbiamo scelto di non farlo, per tre ragioni:

1. **Responsabilita' professionale.** Il commercialista firma le dichiarazioni
   fiscali. Ha bisogno di sapere esattamente quale regola si applica e perche'.
   Un sistema che "impara in autonomia" crea opacita' inaccettabile in un contesto
   di responsabilita' legale.

2. **Edge case fiscali.** Le eccezioni alle regole fiscali italiane sono numerose
   e dipendono da dettagli (tipo di attivita', documentazione disponibile,
   interpretazioni dell'Agenzia delle Entrate). Un sistema che generalizza
   automaticamente dagli esempi rischia di applicare regole sbagliate a casi
   apparentemente simili ma diversi.

3. **Audit trail.** In caso di verifica fiscale, devi poter spiegare ogni
   registrazione. "Il sistema l'ha imparato da solo" non e' una risposta
   accettabile davanti all'Agenzia delle Entrate.

---

## Parte 3 — Il commercialista come esperto, non come operatore dati

### Il problema attuale

Il lavoro di un commercialista e' per la maggior parte operativo e ripetitivo:
aprire file XML, verificare i dati, registrare la fattura nel gestionale,
controllare che l'IVA sia giusta. Questo lavoro non richiede la competenza
professionale del commercialista — richiede attenzione e tempo.

Il risultato e' che il commercialista passa piu' tempo a fare data entry
che a fare consulting. Il valore professionale — interpretare situazioni
complesse, pianificare fiscalmente, consigliare il cliente — resta inespresso
perche' non c'e' tempo.

### La soluzione di AccountantNanoBot

Il sistema gestisce tutta la parte meccanica:
- Parsing automatico dei file FatturaPA dalla cartella cliente
- Proposta di registrazione in partita doppia
- Calcolo IVA con applicazione dell'override chain
- Scadenzario automatico
- Alert preventivi su soglie (regime forfettario, liquidazioni IVA)

Il commercialista interviene dove serve la sua competenza:
- Validare il profilo fiscale del cliente (una volta per cliente)
- Confermare ogni registrazione proposta (review veloce, non data entry)
- Gestire gli edge case che il sistema non sa classificare
- Usare la chat advisory per rispondere a domande complesse del cliente

### La conferma umana obbligatoria non e' un ostacolo

Ogni registrazione proposta dal sistema richiede conferma prima di essere
salvata. Questa scelta viene spesso percepita come attrito inutile —
"perche' non la salva direttamente se e' ovviamente giusta?"

E' intenzionale, per due motivi:

1. **Responsabilita'.** La firma professionale e' del commercialista, non del
   software. La conferma e' il momento in cui quella responsabilita' viene
   esercitata consciamente.

2. **Qualita' del modello.** Ogni conferma (o correzione) alimenta il profilo
   cliente. Un sistema che salva senza review non impara dai casi in cui il
   commercialista avrebbe corretto — e accumula errori silenziosamente.

---

## Parte 4 — Privacy e sovranita' dei dati

### I dati contabili dei clienti non escono dal computer

I dati di un'azienda cliente — fatture, estratti conto, bilanci, contratti —
sono tra le informazioni piu' sensibili che esistano. Contengono informazioni
su clienti, fornitori, margini, struttura finanziaria.

AccountantNanoBot e' progettato con un principio non negoziabile:
**questi dati non vengono mai trasmessi a servizi cloud esterni**.

Tutto il processing avviene localmente:
- LLM locale via Ollama (nessuna chiamata a OpenAI, Anthropic, Google)
- Database SQLite sul file system locale
- RAG con ChromaDB locale
- Embedding con sentence-transformers in locale

Le uniche eccezioni esplicite e opt-in:
- Trasmissione fatture al SDI via intermediario abilitato (Livello 3 del revenue
  model) — l'utente attiva questa funzione consapevolmente, i dati trasmessi
  sono solo quelli necessari per la trasmissione
- Conservazione sostitutiva a norma — stessa logica

### Perche' non usare API cloud per avere modelli piu' potenti

Un LLM cloud piu' potente produrrebbe classificazioni migliori.
Ma richiederebbe di inviare il contenuto delle fatture dei clienti
a server di terzi.

Il compromesso non e' accettabile. La qualita' del modello migliora
nel tempo con modelli locali sempre piu' capaci — e il principio di
privacy rimane intatto.

---

## Parte 5 — Open source come scelta strategica

### AGPL-3.0 non e' una scelta ideologica

La licenza AGPL-3.0 e' stata scelta per ragioni pratiche:

1. **Fiducia.** Un commercialista che affida i dati dei suoi clienti a un
   software ha bisogno di poter verificare che quel software faccia quello
   che dice. Il codice sorgente aperto e' l'unica garanzia verificabile.

2. **Calcoli fiscali verificabili.** Le regole di calcolo IVA, le aliquote,
   la logica di partita doppia devono essere ispezionabili da chiunque
   abbia le competenze per farlo. Non e' possibile fidarsi ciecamente
   di un black box per calcoli fiscalmente rilevanti.

3. **Protezione dall'obsolescenza.** Se il progetto venisse abbandonato,
   gli studi che lo usano possono continuare a farlo e, se necessario,
   farlo evolvere internamente.

### Il moat non e' il codice

Il vantaggio competitivo non viene dal tenere il codice segreto.
Viene da:
- I dati normativi aggiornati (Livello 1 del revenue model)
- La fiducia costruita con gli studi nel tempo
- Le integrazioni SDI gia' negoziate (Livello 3)

Un concorrente puo' fare fork del codice core — non puo' replicare
questi elementi in poco tempo.

---

## Principi in sintesi

| Principio | Conseguenza pratica |
|---|---|
| Calcoli deterministici | LLM mai nei calcoli fiscali, solo in chat e classificazione |
| Chiedi una volta, applica sempre | Override chain salvato e validato, non rigenerato ogni volta |
| Il commercialista resta esperto | Conferma umana obbligatoria su ogni registrazione |
| Privacy non negoziabile | LLM locale, dati mai in cloud |
| Codice ispezionabile | AGPL-3.0, calcoli verificabili da chiunque |

---

*AccountantNanoBot — github.com/fab128k/accountantNanoBot*
*GNU AGPL-3.0*
