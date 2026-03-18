# agents/orchestrator.py
# AccountantNanoBot v1.0.0 - Orchestratore agenti
# ============================================================================
# Routing keyword-based verso l'agente specializzato corretto.
# ============================================================================

from __future__ import annotations

import re
from typing import Dict, Optional, Tuple, TYPE_CHECKING

if TYPE_CHECKING:
    from agents.base_agent import BaseAccountingAgent


# ============================================================================
# ROUTING RULES
# ============================================================================

_ROUTING_RULES: list[Tuple[list[str], str]] = [
    # Fatturazione
    (
        ["fattura", "xml", "fornitore", "cedente", "cessionario",
         "fpa12", "fpr12", "fatturaPA", "sdi", "importazione"],
        "fatturazione",
    ),
    # IVA
    (
        ["iva", "liquidazione", "aliquota", "imponibile", "imposta",
         "reverse charge", "esente", "esclusione", "f24", "versamento iva"],
        "iva",
    ),
    # Bilancio
    (
        ["bilancio", "chiusura", "apertura", "stato patrimoniale",
         "conto economico", "attivo", "passivo", "patrimonio netto",
         "ammortamento", "svalutazione"],
        "bilancio",
    ),
    # Scadenze e compliance
    (
        ["scadenza", "adempimento", "dichiarazione", "modello", "spesometro",
         "comunicazione", "esterometro", "intrastat", "lipe", "730", "770", "770", "unico"],
        "compliance",
    ),
    # Prima nota / contabilità generale
    (
        ["prima nota", "registrazione", "partita doppia", "dare", "avere",
         "conto", "piano dei conti", "mastro", "giornale"],
        "prima_nota",
    ),
]

_DEFAULT_AGENT = "memoria"


class Orchestrator:
    """
    Orchestratore per il routing dei messaggi agli agenti specializzati.

    Usa keyword matching per determinare quale agente è più adatto
    a rispondere a un messaggio utente.
    """

    def __init__(self):
        self._agents: Dict[str, "BaseAccountingAgent"] = {}

    def register_agent(self, agent_id: str, agent: "BaseAccountingAgent") -> None:
        """
        Registra un agente nell'orchestratore.

        Args:
            agent_id: Identificatore univoco (es. "fatturazione")
            agent: Istanza dell'agente
        """
        self._agents[agent_id] = agent

    def route(self, user_message: str) -> Tuple[str, "BaseAccountingAgent"]:
        """
        Determina l'agente più appropriato per il messaggio.

        Args:
            user_message: Messaggio dell'utente

        Returns:
            Tupla (agent_id, agente)
        """
        message_lower = user_message.lower()

        # Conta match per ciascun tipo di agente
        scores: Dict[str, int] = {}

        for keywords, agent_id in _ROUTING_RULES:
            score = sum(1 for kw in keywords if kw in message_lower)
            if score > 0:
                scores[agent_id] = scores.get(agent_id, 0) + score

        # Seleziona agente con score più alto
        if scores:
            best_agent_id = max(scores, key=lambda k: scores[k])
            agent = self._agents.get(best_agent_id)
            if agent:
                return best_agent_id, agent

        # Fallback: agente memoria (RAG generico)
        default_agent = self._agents.get(_DEFAULT_AGENT)
        if default_agent:
            return _DEFAULT_AGENT, default_agent

        # Se non c'è nemmeno il default, usa il primo disponibile
        if self._agents:
            agent_id, agent = next(iter(self._agents.items()))
            return agent_id, agent

        raise ValueError("Nessun agente registrato nell'orchestratore")

    def get_agent(self, agent_id: str) -> Optional["BaseAccountingAgent"]:
        """Ritorna un agente specifico per ID."""
        return self._agents.get(agent_id)

    def list_agents(self) -> Dict[str, str]:
        """Ritorna dict {agent_id: nome_agente}."""
        return {aid: a.name for aid, a in self._agents.items()}

    def set_rag_manager(self, rag_manager) -> None:
        """Propaga il RAG manager a tutti gli agenti registrati."""
        for agent in self._agents.values():
            agent.set_rag_manager(rag_manager)


def build_default_orchestrator(
    models: Optional[Dict[str, str]] = None,
    base_url: str = "http://localhost:11434/v1",
) -> Orchestrator:
    """
    Costruisce l'orchestratore con tutti gli agenti predefiniti.

    Args:
        models: Dict {agent_id: model_name} — usa defaults se None
        base_url: URL base Ollama

    Returns:
        Orchestratore configurato
    """
    from config.constants import DEFAULT_MODEL, DEFAULT_AGENT_TEMPERATURE
    from agents.fatturazione_agent import FatturazioneAgent
    from agents.memoria_agent import MemoriaAgent
    from agents.base_agent import BaseAccountingAgent

    if models is None:
        models = {}

    def get_model(agent_id: str) -> str:
        return models.get(agent_id, DEFAULT_MODEL)

    orchestrator = Orchestrator()

    # Agente Fatturazione (primo agente operativo)
    orchestrator.register_agent(
        "fatturazione",
        FatturazioneAgent(
            model=get_model("fatturazione"),
            base_url=base_url,
        )
    )

    # Agente Memoria / RAG Generico
    orchestrator.register_agent(
        "memoria",
        MemoriaAgent(
            model=get_model("memoria"),
            base_url=base_url,
        )
    )

    # Agenti placeholder (usano BaseAccountingAgent con system prompt specializzato)
    _PLACEHOLDER_AGENTS = {
        "iva": (
            "Agente IVA",
            """Sei un esperto di IVA italiana con profonda conoscenza del DPR 633/72
e delle relative normative. Assisti nella liquidazione IVA, nel calcolo delle
aliquote, nella gestione delle operazioni esenti/escluse, e nella compilazione
del modello F24 per il versamento dell'IVA.
Rispondi sempre in modo preciso e cita la normativa di riferimento.""",
        ),
        "bilancio": (
            "Agente Bilancio",
            """Sei un esperto di bilancio civilistico italiano (OIC) con profonda
conoscenza delle norme del Codice Civile (artt. 2423-2435-bis) e dei principi
contabili OIC. Assisti nella redazione del bilancio d'esercizio, nelle chiusure
annuali, nelle scritture di assestamento e nella predisposizione della nota
integrativa. Rispondi con precisione e cita sempre i riferimenti normativi.""",
        ),
        "compliance": (
            "Agente Compliance",
            """Sei un esperto di adempimenti fiscali e tributari italiani.
Monitora le scadenze fiscali, assisti nella predisposizione delle dichiarazioni
(LIPE, Spesometro, Esterometro, Intrastat, modelli annuali) e nella gestione
dei rapporti con l'Agenzia delle Entrate.
Avvisa proattivamente sulle scadenze imminenti.""",
        ),
        "prima_nota": (
            "Agente Prima Nota",
            """Sei un esperto di contabilità generale italiana e partita doppia.
Assisti nella registrazione manuale delle scritture contabili, nella gestione
del piano dei conti OIC, nel controllo del bilanciamento dare/avere e nella
riconciliazione dei conti. Ogni registrazione deve essere bilnciata.""",
        ),
    }

    for agent_id, (name, prompt) in _PLACEHOLDER_AGENTS.items():
        orchestrator.register_agent(
            agent_id,
            BaseAccountingAgent(
                name=name,
                model=get_model(agent_id),
                system_prompt=prompt,
                temperature=DEFAULT_AGENT_TEMPERATURE,
                base_url=base_url,
            )
        )

    return orchestrator
