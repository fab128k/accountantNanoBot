# agents/fatturazione_agent.py
# AccountantNanoBot v1.0.0 - Agente Fatturazione (primo agente operativo)
# ============================================================================

from __future__ import annotations

from pathlib import Path
from typing import Optional, Tuple, TYPE_CHECKING

from swarm.base import BaseSwarmAgent
from config.constants import DEFAULT_AGENT_TEMPERATURE

if TYPE_CHECKING:
    from swarm.context import ProcessingContext


_SYSTEM_PROMPT = """Sei un esperto contabile italiano specializzato nella gestione
delle fatture elettroniche (FatturaPA) e nella tenuta della prima nota.

Le tue competenze:
- Analisi e interpretazione di fatture XML FatturaPA (formato v1.2)
- Classificazione fatture: acquisto (TD01 da fornitore), vendita (TD01 a cliente),
  note credito (TD04), autofatture (TD16-TD21)
- Suggerimento registrazioni contabili in partita doppia (dare/avere)
- Classificazione costi/ricavi secondo il piano dei conti OIC
- Gestione IVA: aliquote ordinarie (22%), ridotte (10%, 5%, 4%), operazioni esenti/escluse

Regole fondamentali:
1. Ogni registrazione DEVE essere bilanciata (∑DARE == ∑AVERE)
2. Usa SEMPRE il piano dei conti OIC (codici standard: C.II.1, D.7, A.1, B.6, ecc.)
3. Per le fatture di acquisto: Dare=Costo+IVAcredito, Avere=DebitoFornitore
4. Per le fatture di vendita: Dare=CreditoCliente, Avere=Ricavo+IVAdebito
5. Segnala SEMPRE se ci sono anomalie o elementi da verificare

Rispondi in italiano, in modo preciso e professionale."""


class FatturazioneAgent(BaseSwarmAgent):
    """
    Agente specializzato nella gestione fatture e prima nota.

    Primo agente operativo del sistema AccountantNanoBot.
    Integra il parser FatturaPA con il sistema di prima nota.
    """

    def __init__(
        self,
        model: str = "llama3.2:3b",
        base_url: str = "http://localhost:11434/v1",
    ):
        super().__init__(
            name="Agente Fatturazione",
            model=model,
            system_prompt=_SYSTEM_PROMPT,
            temperature=DEFAULT_AGENT_TEMPERATURE,
            base_url=base_url,
        )

    def process(self, context: "ProcessingContext") -> "ProcessingContext":
        """
        Processa il contesto swarm. Se current_file e' un XML FatturaPA,
        lo analizza e scrive il risultato in context.metadata.
        """
        if context.current_file and str(context.current_file).lower().endswith('.xml'):
            try:
                xml_bytes = context.current_file.read_bytes()
                company_piva = context.metadata.get('company_piva', '')
                fattura, registrazione, errore = self.analizza_xml_bytes(
                    xml_bytes, company_piva=company_piva
                )
                if fattura and registrazione:
                    context.metadata['fattura'] = fattura
                    context.metadata['registrazione_suggerita'] = registrazione
                elif errore:
                    context.errors.append(errore)
            except Exception as e:
                context.errors.append(f"Errore processing fattura {context.current_file}: {e}")
        return context

    def processa_fattura(
        self,
        xml_path: str | Path,
        company_piva: str = "",
        save_to_db: bool = False,
    ) -> Tuple[Optional[object], Optional[object], str]:
        """
        Processa una fattura XML e suggerisce la registrazione contabile.

        Flusso:
        1. Parsa l'XML con FatturaPAParser
        2. Determina se acquisto o vendita
        3. Genera suggerimento prima nota
        4. Usa LLM per arricchire/validare il suggerimento
        5. Salva nel DB se richiesto e bilanciata

        NOTA: richiede sempre conferma umana prima di salvare definitivamente.

        Args:
            xml_path: Path al file XML FatturaPA
            company_piva: P.IVA dell'azienda (per distinguere acquisto/vendita)
            save_to_db: Se True, salva la fattura importata nel DB (NON la registrazione)

        Returns:
            Tupla (fattura, registrazione_suggerita, messaggio_llm)
        """
        from parsers.fattura_pa import FatturaPAParser
        from accounting.prima_nota import RegistrazionePrimaNota
        from accounting.db import salva_fattura_importata, fattura_gia_importata

        xml_path = Path(xml_path)

        # Leggi bytes
        with open(xml_path, "rb") as f:
            xml_bytes = f.read()

        # Controlla duplicato
        if fattura_gia_importata(xml_bytes):
            return None, None, "⚠️ Fattura già importata in precedenza (hash duplicato)"

        # Parsa XML
        parser = FatturaPAParser()
        try:
            fatture = parser.parse_bytes(xml_bytes)
        except Exception as e:
            return None, None, f"❌ Errore parsing XML: {e}"

        if not fatture:
            return None, None, "❌ Nessuna fattura trovata nel file XML"

        # Gestisci prima fattura (in caso di file multiplo)
        fattura = fatture[0]

        # Genera suggerimento prima nota
        suggestion = parser.to_prima_nota_suggestion(
            fattura,
            is_acquisto=True,  # Default acquisto, sovrascritto se company_piva
            company_piva=company_piva,
        )

        # Crea oggetto registrazione
        registrazione = RegistrazionePrimaNota.from_suggestion(suggestion)

        # Usa LLM per commentare/validare
        summary = parser.to_text_summary(fattura)
        prompt = f"""Analizza questa fattura e la registrazione contabile suggerita.
Verifica che sia corretta e segnala eventuali problemi o elementi da controllare.

FATTURA:
{summary}

REGISTRAZIONE SUGGERITA:
{registrazione}

Fornisci:
1. Conferma o correzione del tipo documento (acquisto/vendita)
2. Verifica dei conti utilizzati
3. Eventuali note o avvertenze (es. operazioni particolari, IVA speciale)
4. Giudizio finale: la registrazione è corretta?"""

        llm_response = self.ask(prompt)

        # Salva fattura nel DB se richiesto (non la registrazione - richiede conferma umana)
        if save_to_db:
            salva_fattura_importata(
                fattura,
                xml_bytes,
                str(xml_path)
            )

        return fattura, registrazione, llm_response

    def analizza_xml_bytes(
        self,
        xml_bytes: bytes,
        company_piva: str = "",
    ) -> Tuple[Optional[object], Optional[object], str]:
        """
        Versione di processa_fattura che accetta bytes (da Streamlit upload).
        Operazione deterministica e veloce — NON chiama l'LLM.
        Per il commento LLM usa stream_commento_fattura() separatamente.

        Args:
            xml_bytes: Contenuto XML della fattura
            company_piva: P.IVA dell'azienda

        Returns:
            Tupla (fattura, registrazione_suggerita, "")
        """
        from parsers.fattura_pa import FatturaPAParser
        from accounting.prima_nota import RegistrazionePrimaNota

        parser = FatturaPAParser()

        try:
            fatture = parser.parse_bytes(xml_bytes)
        except Exception as e:
            return None, None, f"❌ Errore parsing XML: {e}"

        if not fatture:
            return None, None, "❌ Nessuna fattura trovata nel file XML"

        fattura = fatture[0]
        suggestion = parser.to_prima_nota_suggestion(
            fattura,
            is_acquisto=True,
            company_piva=company_piva,
        )
        registrazione = RegistrazionePrimaNota.from_suggestion(suggestion)

        return fattura, registrazione, ""

    def stream_commento_fattura(
        self,
        xml_bytes: bytes,
        company_piva: str = "",
    ):
        """
        Genera un commento LLM in streaming su una fattura già parsata.
        Da chiamare DOPO analizza_xml_bytes() per non bloccare la UI.

        Args:
            xml_bytes: Contenuto XML della fattura
            company_piva: P.IVA dell'azienda

        Yields:
            _TextChunk con attributo .text (testo cumulativo)
        """
        from parsers.fattura_pa import FatturaPAParser
        from accounting.prima_nota import RegistrazionePrimaNota

        parser = FatturaPAParser()
        try:
            fatture = parser.parse_bytes(xml_bytes)
        except Exception as e:
            from core.llm_client import _TextChunk
            yield _TextChunk(f"❌ Errore parsing: {e}")
            return

        if not fatture:
            from core.llm_client import _TextChunk
            yield _TextChunk("❌ Nessuna fattura trovata nel file XML")
            return

        fattura = fatture[0]
        suggestion = parser.to_prima_nota_suggestion(
            fattura, is_acquisto=True, company_piva=company_piva
        )
        registrazione = RegistrazionePrimaNota.from_suggestion(suggestion)
        summary = parser.to_text_summary(fattura)

        prompt = f"""Verifica questa registrazione contabile in 3-4 punti concisi:
- Tipo documento corretto (acquisto/vendita)?
- Conti OIC appropriati?
- Anomalie IVA o elementi da segnalare?
- Registrazione bilanciata?

FATTURA:
{summary}

REGISTRAZIONE:
{registrazione}"""

        yield from self.stream_ask(prompt)

    def rispondi_domanda_fattura(self, domanda: str, contesto_fattura: str = "") -> str:
        """
        Risponde a una domanda specifica su una fattura o sulla fatturazione.

        Args:
            domanda: Domanda dell'utente
            contesto_fattura: Testo della fattura come contesto

        Returns:
            Risposta dell'agente
        """
        return self.ask(domanda, context=contesto_fattura)
