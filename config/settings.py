# config/settings.py
# AccountantNanoBot v1.0.0 - Funzioni gestione configurazioni
# ============================================================================

import os
from pathlib import Path
from typing import Dict, Any, Optional, List
from dotenv import load_dotenv

from .constants import (
    COMPANY_CONFIG_FILE,
    SECRETS_DIR,
    BASE_DIR,
    OLLAMA_BASE_URL,
    DEFAULT_MODEL,
    DEFAULT_AGENT_TEMPERATURE,
)

try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False


# ============================================================================
# COMPANY CONFIG
# ============================================================================

_DEFAULT_COMPANY_CONFIG = {
    "ragione_sociale": "",
    "partita_iva": "",
    "codice_fiscale": "",
    "indirizzo": "",
    "cap": "",
    "comune": "",
    "provincia": "",
    "regime_fiscale": "RF01",  # Ordinario
    "codice_sdi": "",
    "pec": "",
    "settore": "commercio",
}


def load_company_config() -> Dict[str, Any]:
    """
    Carica configurazione azienda da data/config.yaml.

    Returns:
        Dict con dati azienda, valori default se file non trovato
    """
    if not YAML_AVAILABLE or not COMPANY_CONFIG_FILE.exists():
        return _DEFAULT_COMPANY_CONFIG.copy()

    try:
        with open(COMPANY_CONFIG_FILE, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
        if not isinstance(config, dict):
            return _DEFAULT_COMPANY_CONFIG.copy()
        return {**_DEFAULT_COMPANY_CONFIG, **config}
    except Exception as e:
        print(f"⚠️ Errore lettura config azienda: {e}")
        return _DEFAULT_COMPANY_CONFIG.copy()


def save_company_config(config: Dict[str, Any]) -> bool:
    """
    Salva configurazione azienda in data/config.yaml.

    Args:
        config: Dict con dati azienda

    Returns:
        True se salvato con successo
    """
    if not YAML_AVAILABLE:
        return False

    try:
        COMPANY_CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(COMPANY_CONFIG_FILE, "w", encoding="utf-8") as f:
            yaml.dump(config, f, allow_unicode=True, default_flow_style=False)
        return True
    except Exception as e:
        print(f"⚠️ Errore salvataggio config azienda: {e}")
        return False


def get_company_piva() -> str:
    """Ritorna P.IVA azienda dalla config."""
    config = load_company_config()
    return config.get("partita_iva", "")


# ============================================================================
# AGENT MODELS CONFIG
# ============================================================================

_DEFAULT_AGENT_MODELS = {
    "orchestrator": DEFAULT_MODEL,
    "fatturazione": DEFAULT_MODEL,
    "iva": DEFAULT_MODEL,
    "bilancio": DEFAULT_MODEL,
    "compliance": DEFAULT_MODEL,
    "memoria": DEFAULT_MODEL,
}


def get_agent_models() -> Dict[str, str]:
    """
    Ritorna dict modello per ogni agente.
    Legge da data/config.yaml se presente, altrimenti usa DEFAULT_MODEL.

    Returns:
        Dict {nome_agente: nome_modello}
    """
    config = load_company_config()
    agent_models = config.get("agent_models", {})
    return {**_DEFAULT_AGENT_MODELS, **agent_models}


def get_ollama_base_url() -> str:
    """Ritorna URL base Ollama (da env o default)."""
    load_dotenv()
    return os.getenv("OLLAMA_BASE_URL", OLLAMA_BASE_URL)


# ============================================================================
# API KEYS (mantenuto per compatibilità RAG)
# ============================================================================

def load_api_key(provider_name: str, env_var_name: str) -> str:
    """
    Carica API key da variabile ambiente o file secrets.

    Args:
        provider_name: Nome provider (es. "openai")
        env_var_name: Nome variabile ambiente (es. "OPENAI_API_KEY")

    Returns:
        API key o stringa vuota se non trovata
    """
    load_dotenv()

    api_key = os.getenv(env_var_name)
    if api_key:
        return api_key

    key_file = SECRETS_DIR / f"{provider_name}_key.txt"
    if key_file.exists():
        try:
            with open(key_file, "r", encoding="utf-8") as f:
                return f.read().strip()
        except Exception:
            pass

    return ""
