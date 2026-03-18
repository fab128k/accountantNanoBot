# agents/base_agent.py
# AccountantNanoBot v1.0.0 - Classe base per agenti contabili
# ============================================================================

from __future__ import annotations

from typing import Generator, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from rag.manager import KnowledgeBaseManager


class BaseAccountingAgent:
    """
    Classe base per tutti gli agenti contabili del sistema.

    Ogni agente specializzato eredita da questa classe e definisce
    il proprio system prompt e le proprie capacità.
    """

    def __init__(
        self,
        name: str,
        model: str,
        system_prompt: str,
        temperature: float = 0.1,
        base_url: str = "http://localhost:11434/v1",
    ):
        """
        Inizializza l'agente.

        Args:
            name: Nome identificativo dell'agente
            model: Nome modello Ollama (es. "llama3.2:3b")
            system_prompt: Istruzioni di sistema per l'agente
            temperature: Temperatura generazione (default 0.1 per lavoro contabile)
            base_url: URL base API Ollama
        """
        self.name = name
        self.model = model
        self.system_prompt = system_prompt
        self.temperature = temperature
        self.base_url = base_url
        self.rag_manager: Optional[KnowledgeBaseManager] = None

        # Lazy-init del client (evita errore se Ollama non è attivo all'avvio)
        self._client = None

    def _get_client(self):
        """Ritorna il client Ollama, creandolo se necessario."""
        if self._client is None:
            from core.llm_client import create_ollama_client
            self._client = create_ollama_client(
                model=self.model,
                system_prompt=self.system_prompt,
                temperature=self.temperature,
                base_url=self.base_url,
            )
        return self._client

    def set_rag_manager(self, rag_manager) -> None:
        """
        Inietta il RAG manager per accesso alla knowledge base.

        Args:
            rag_manager: Istanza di KnowledgeBaseManager
        """
        self.rag_manager = rag_manager

    def _get_rag_context(self, query: str, top_k: int = 3) -> str:
        """
        Recupera contesto RAG per una query.

        Args:
            query: Query per la ricerca
            top_k: Numero massimo di risultati

        Returns:
            Testo di contesto o stringa vuota
        """
        if self.rag_manager and self.rag_manager.is_indexed():
            try:
                context, _ = self.rag_manager.get_context_for_prompt(query, top_k)
                return context
            except Exception:
                return ""
        return ""

    def ask(self, user_message: str, context: str = "") -> str:
        """
        Invia una domanda all'agente, con contesto opzionale.

        Args:
            user_message: Messaggio dell'utente
            context: Contesto aggiuntivo (es. dati RAG, dati fattura)

        Returns:
            Risposta dell'agente
        """
        client = self._get_client()

        # Arricchisci con contesto RAG se disponibile
        rag_context = self._get_rag_context(user_message)

        full_prompt = user_message

        if context or rag_context:
            parts = []
            if rag_context:
                parts.append(f"=== DOCUMENTI AZIENDALI RILEVANTI ===\n{rag_context}\n=== FINE DOCUMENTI ===")
            if context:
                parts.append(f"=== CONTESTO OPERATIVO ===\n{context}\n=== FINE CONTESTO ===")

            full_prompt = "\n\n".join(parts) + f"\n\n{user_message}"

        return client.invoke(full_prompt)

    def stream_ask(self, user_message: str, context: str = "") -> Generator[str, None, None]:
        """
        Versione streaming di ask() per la UI.

        Args:
            user_message: Messaggio dell'utente
            context: Contesto aggiuntivo

        Yields:
            Oggetti con attributo .text (incrementale)
        """
        client = self._get_client()

        rag_context = self._get_rag_context(user_message)

        full_prompt = user_message
        if context or rag_context:
            parts = []
            if rag_context:
                parts.append(f"=== DOCUMENTI AZIENDALI RILEVANTI ===\n{rag_context}\n=== FINE DOCUMENTI ===")
            if context:
                parts.append(f"=== CONTESTO OPERATIVO ===\n{context}\n=== FINE CONTESTO ===")
            full_prompt = "\n\n".join(parts) + f"\n\n{user_message}"

        yield from client.stream_invoke(full_prompt)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name={self.name!r}, model={self.model!r})"
