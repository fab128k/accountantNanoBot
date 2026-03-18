# Modello di Revenue — AccountantNanoBot

Architettura freemium a 4 livelli, coerente con licenza AGPL-3.0.
Il codice core è open source. Il valore commerciale sta nei servizi collegati.

---

## Livello 0 — Gratuito forever

**Target:** singolo professionista, sviluppatori, studi che vogliono valutare

**Incluso:**
- Parser FatturaPA XML (v1.2+)
- Partita doppia con piano dei conti OIC
- Prima nota con conferma umana obbligatoria
- SQLite locale, zero cloud, zero telemetria
- Advisory chat base via LLM locale (Ollama)
- Profilo cliente con motore regole personalizzato (override chain)
- Export PDF generato da codice deterministico
- Scansione automatica cartella cliente

**Vincolo AGPL:** chi modifica e distribuisce deve rilasciare le modifiche.
Chi usa internamente (studio, azienda) non ha obblighi di rilascio.

---

## Livello 1 — Aggiornamenti (5–10 EUR/mese)

**Target:** studi che usano il software in produzione e non vogliono gestire aggiornamenti manuali

**Incluso:**
- Aggiornamenti normativi automatici push:
  - Nuove versioni FatturaPA (attualmente v1.9, aprile 2025: TD29, RF20)
  - Aliquote IVA e tabelle CCNL aggiornate
  - Scadenze fiscali (F24, LIPE, dichiarazioni)
- Nuovi tipi documento appena disponibili (SDI, AdE)
- Canale di notifica aggiornamenti (email o in-app)

**Modello tecnico:** modulo `updater/` separato che scarica file di regole
firmati da server. Il core resta open source, i file di regole sono dati.

---

## Livello 2 — Studio (20–40 EUR/mese per studio)

**Target:** commercialisti e studi con più clienti gestiti

**Incluso tutto il Livello 1, più:**
- Multi-cliente: N aziende gestite dallo stesso studio
- Dashboard studio aggregata (scadenze, anomalie, KPI cross-cliente)
- Export pacchetto dati cliente per consegna (PDF + XML + report)
- Separazione profili per operatore (chi ha fatto cosa)

**Pricing indicativo:**
- fino a 10 clienti: 20 EUR/mese
- fino a 50 clienti: 35 EUR/mese
- illimitati: 40 EUR/mese

---

## Livello 3 — SDI revenue share (passivo)

**Target:** clienti che vogliono trasmettere fatture via il software

**Modello:**
- Il software si integra con un intermediario SDI abilitato AgID
  (Aruba, Entaksi, Namirial o equivalente)
- L'utente attiva la trasmissione dal software senza uscire dall'interfaccia
- Commissione passiva su ogni fattura trasmessa (revenue share con intermediario)

**Perché non costruiamo l'intermediario:**
Diventare intermediario SDI richiede accreditamento AgID, infrastruttura
certificata, e responsabilità legale. La barriera regolamentare è alta.
Meglio integrare API di chi è già accreditato e prendere una quota.

**Stima ordine di grandezza:**
- Costo trasmissione lato intermediario: 0.05–0.15 EUR/fattura
- Markup possibile: 0.05–0.10 EUR/fattura
- Studio con 500 fatture/mese → 25–50 EUR/mese di margine passivo

---

## Coerenza con AGPL-3.0

| Componente | Licenza | Razionale |
|---|---|---|
| Core engine (parser, contabilità, advisory) | AGPL-3.0 open source | Vantaggio competitivo è la qualità, non la segretezza |
| File di regole normativi (Livello 1) | Dati proprietari | Non sono codice, non coperti da AGPL |
| Dashboard multi-cliente (Livello 2) | Hosted service o addon | SaaS/hosted non obbligo di rilascio AGPL |
| Integrazione SDI (Livello 3) | API call a terzi | Infrastruttura esterna, non codice distribuito |

**Principio guida:** un concorrente può fare fork del core, ma non può replicare
i dati normativi aggiornati, la fiducia dello studio, né l'integrazione SDI già
negoziata. Il moat non è il codice, è il servizio.
