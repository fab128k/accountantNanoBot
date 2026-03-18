# agents/memoria_agent.py
# AccountantNanoBot v1.0.0 - Agente Memoria (RAG generico)
# ============================================================================

from __future__ import annotations

from agents.base_agent import BaseAccountingAgent
from config.constants import DEFAULT_AGENT_TEMPERATURE


def _build_system_prompt(company_name: str = "", company_piva: str = "") -> str:
    """Costruisce il system prompt personalizzato per l'azienda."""
    azienda_info = ""
    if company_name:
        azienda_info = f"\n\nSei l'assistente contabile di: {company_name}"
        if company_piva:
            azienda_info += f" (P.IVA: {company_piva})"

    return f"""Sei un assistente contabile e fiscale esperto sulla normativa italiana.{azienda_info}

Le tue competenze:
- Normativa fiscale italiana (IVA, IRPEF, IRES, IRAP)
- Principi contabili OIC e IFRS
- Adempimenti societari e tributari
- Lettura e interpretazione di documenti contabili
- Supporto alla gestione quotidiana della contabilità

Quando rispondi:
- Cerca sempre nei documenti aziendali caricati prima di rispondere dalla tua conoscenza generale
- Se la risposta è nei documenti, cita la fonte
- Se non trovi l'informazione, dillo chiaramente e fornisci comunque orientamento generale
- Segnala sempre se una questione richiede verifica da parte di un professionista abilitato
- Rispondi in italiano in modo chiaro e professionale"""


class MemoriaAgent(BaseAccountingAgent):
    """
    Agente RAG generico per domande contabili/fiscali.

    Wrappa il KnowledgeBaseManager esistente e risponde a domande
    generali cercando prima nei documenti storici aziendali,
    poi usando la conoscenza del modello LLM.
    """

    def __init__(
        self,
        model: str = "llama3.2:3b",
        base_url: str = "http://localhost:11434/v1",
        company_name: str = "",
        company_piva: str = "",
    ):
        super().__init__(
            name="Agente Memoria",
            model=model,
            system_prompt=_build_system_prompt(company_name, company_piva),
            temperature=DEFAULT_AGENT_TEMPERATURE,
            base_url=base_url,
        )
        self.company_name = company_name
        self.company_piva = company_piva

    def update_company_info(self, company_name: str, company_piva: str) -> None:
        """
        Aggiorna le informazioni aziendali e rigenera il system prompt.

        Args:
            company_name: Ragione sociale
            company_piva: Partita IVA
        """
        self.company_name = company_name
        self.company_piva = company_piva
        self.system_prompt = _build_system_prompt(company_name, company_piva)
        self._client = None  # Reset client per usare nuovo system prompt

    def cerca_in_documenti(self, query: str, top_k: int = 5) -> list:
        """
        Cerca direttamente nei documenti della knowledge base.

        Args:
            query: Query di ricerca
            top_k: Numero risultati

        Returns:
            Lista di risultati RAG
        """
        if self.rag_manager and self.rag_manager.is_indexed():
            _, sources = self.rag_manager.get_context_for_prompt(query, top_k)
            return sources
        return []
