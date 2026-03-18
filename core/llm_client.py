# core/llm_client.py
# AccountantNanoBot v1.0.0 - Client LLM (solo Ollama locale)
# ============================================================================

import subprocess
from typing import List, Any, Generator, Optional


def get_local_ollama_models() -> List[str]:
    """
    Recupera lista modelli Ollama installati localmente.

    Esegue 'ollama list' e parsa l'output.

    Returns:
        Lista di nomi modelli disponibili
    """
    try:
        proc = subprocess.run(
            ["ollama", "list"],
            capture_output=True,
            text=True,
            check=True,
            timeout=5
        )
        lines = proc.stdout.splitlines()
        models = []

        for line in lines:
            s = line.strip()
            if not s or s.upper().startswith("NAME") or set(s) <= set("- "):
                continue
            parts = s.split()
            if parts:
                models.append(parts[0])

        return models

    except Exception:
        return []


class OllamaClient:
    """
    Client semplificato per Ollama via API OpenAI-compatibile.

    Usato dagli agenti contabili per comunicare con modelli locali.
    """

    def __init__(
        self,
        model: str,
        system_prompt: str,
        temperature: float = 0.1,
        base_url: str = "http://localhost:11434/v1",
    ):
        self.model = model
        self.system_prompt = system_prompt
        self.temperature = temperature
        self.base_url = base_url.rstrip("/")

    def invoke(self, prompt: str, max_tokens: int = 500) -> str:
        """
        Invia prompt al modello e ritorna risposta completa.

        Args:
            prompt: Testo del prompt utente
            max_tokens: Limite token risposta (default 500)

        Returns:
            Risposta del modello come stringa
        """
        try:
            from openai import OpenAI

            client = OpenAI(
                base_url=self.base_url,
                api_key="ollama",
            )

            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": prompt},
                ],
                temperature=self.temperature,
                max_tokens=max_tokens,
            )

            return response.choices[0].message.content or ""

        except Exception as e:
            return f"[Errore LLM: {e}]"

    def stream_invoke(self, prompt: str, max_tokens: int = 500) -> Generator[str, None, None]:
        """
        Invia prompt e ritorna generatore di chunk di testo.

        Args:
            prompt: Testo del prompt utente
            max_tokens: Limite token risposta (default 500)

        Yields:
            Chunk di testo man mano che arrivano
        """
        try:
            from openai import OpenAI

            client = OpenAI(
                base_url=self.base_url,
                api_key="ollama",
            )

            stream = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": prompt},
                ],
                temperature=self.temperature,
                stream=True,
                max_tokens=max_tokens,
            )

            accumulated = ""
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    accumulated += chunk.choices[0].delta.content
                    # Yield oggetto con attributo .text per compatibilità
                    yield _TextChunk(accumulated)

        except Exception as e:
            yield _TextChunk(f"[Errore LLM: {e}]")

    def invoke_with_history(self, messages: List[dict], user_message: str) -> str:
        """
        Invia messaggio con storico conversazione.

        Args:
            messages: Lista di dict {"role": "user"|"assistant", "content": str}
            user_message: Nuovo messaggio utente

        Returns:
            Risposta del modello
        """
        try:
            from openai import OpenAI

            client = OpenAI(
                base_url=self.base_url,
                api_key="ollama",
            )

            api_messages = [{"role": "system", "content": self.system_prompt}]
            api_messages.extend(messages)
            api_messages.append({"role": "user", "content": user_message})

            response = client.chat.completions.create(
                model=self.model,
                messages=api_messages,
                temperature=self.temperature,
            )

            return response.choices[0].message.content or ""

        except Exception as e:
            return f"[Errore LLM: {e}]"


class _TextChunk:
    """Helper per compatibilità streaming con il codice UI esistente."""

    def __init__(self, text: str):
        self.text = text


def create_ollama_client(
    model: str,
    system_prompt: str,
    temperature: float = 0.1,
    base_url: str = "http://localhost:11434/v1",
) -> OllamaClient:
    """
    Factory per creare un client Ollama configurato.

    Args:
        model: Nome modello Ollama (es. "llama3.2:3b")
        system_prompt: System prompt per l'agente
        temperature: Temperatura generazione (default 0.1 per lavoro contabile)
        base_url: URL base API Ollama

    Returns:
        OllamaClient configurato
    """
    return OllamaClient(
        model=model,
        system_prompt=system_prompt,
        temperature=temperature,
        base_url=base_url,
    )


# Alias per compatibilità con codice esistente che usa create_client
def create_client(
    connection_type: str,
    provider: str,
    api_key: str,
    model: str,
    system_prompt: str,
    base_url: str,
    temperature: float,
) -> OllamaClient:
    """
    Compatibilità con l'interfaccia originale — crea sempre un client Ollama.

    Args:
        connection_type: Ignorato (sempre Ollama locale)
        provider: Ignorato
        api_key: Ignorato (Ollama non richiede autenticazione)
        model: Nome modello
        system_prompt: System prompt
        base_url: URL Ollama
        temperature: Temperatura

    Returns:
        OllamaClient configurato
    """
    return OllamaClient(
        model=model,
        system_prompt=system_prompt,
        temperature=temperature,
        base_url=base_url or "http://localhost:11434/v1",
    )
