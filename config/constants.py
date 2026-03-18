# config/constants.py
# AccountantNanoBot v1.0.0 - Costanti globali
# ============================================================================

from pathlib import Path

# ============================================================================
# VERSIONE
# ============================================================================

VERSION = "1.0.0"
VERSION_STRING = f"v{VERSION}"
APP_NAME = "AccountantNanoBot"

# ============================================================================
# PATHS
# ============================================================================

BASE_DIR = Path(__file__).parent.parent

CONVERSATIONS_DIR = BASE_DIR / "conversations"
KNOWLEDGE_BASE_DIR = BASE_DIR / "knowledge_base"
SECRETS_DIR = BASE_DIR / "secrets"
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "accounting.db"
FATTURE_DIR = DATA_DIR / "fatture_xml"
DOCUMENTI_DIR = DATA_DIR / "documenti"
COMPANY_CONFIG_FILE = DATA_DIR / "config.yaml"

# ============================================================================
# DEFAULTS - CONVERSAZIONE
# ============================================================================

DEFAULT_MAX_MESSAGES = 50
DEFAULT_MAX_TOKENS_ESTIMATE = 8000

# ============================================================================
# DEFAULTS - RAG
# ============================================================================

DEFAULT_CHUNK_SIZE = 1000
DEFAULT_CHUNK_OVERLAP = 200
DEFAULT_TOP_K_RESULTS = 5

# ============================================================================
# DEFAULTS - AGENTI
# ============================================================================

DEFAULT_AGENT_TEMPERATURE = 0.1  # Bassa per lavoro contabile deterministico
CURRENT_FISCAL_YEAR = 2025
OLLAMA_BASE_URL = "http://localhost:11434/v1"
DEFAULT_MODEL = "llama3.2:3b"

# ============================================================================
# FORMATI FILE SUPPORTATI
# ============================================================================

SUPPORTED_EXTENSIONS = {
    ".md": "Markdown",
    ".txt": "Testo",
    ".html": "HTML",
    ".htm": "HTML",
    ".pdf": "PDF",
    ".docx": "Word",
    ".xml": "XML / FatturaPA",
}

SUPPORTED_DOCUMENT_EXTENSIONS = [".pdf", ".txt", ".md", ".docx", ".xml"]

# ============================================================================
# IVA E FISCO
# ============================================================================

ALIQUOTE_IVA = {
    "ordinaria": 22,
    "ridotta_1": 10,
    "ridotta_2": 5,
    "super_ridotta": 4,
    "esente": 0,
    "esclusa": 0,
    "fuori_campo": 0,
}

TIPI_DOCUMENTO_FATTURA = {
    "TD01": "Fattura",
    "TD02": "Acconto/anticipo su fattura",
    "TD03": "Acconto/anticipo su parcella",
    "TD04": "Nota di credito",
    "TD05": "Nota di debito",
    "TD06": "Parcella",
    "TD16": "Integrazione fattura reverse charge interno",
    "TD17": "Integrazione/autofattura per acquisto servizi dall'estero",
    "TD18": "Integrazione per acquisto di beni intracomunitari",
    "TD19": "Integrazione/autofattura per acquisto di beni ex art.17 c.2 DPR 633/72",
    "TD20": "Autofattura per regolarizzazione e integrazione delle fatture",
    "TD21": "Autofattura per splafonamento",
    "TD22": "Estrazione beni da Deposito IVA",
    "TD23": "Estrazione beni da Deposito IVA con versamento dell'IVA",
    "TD24": "Fattura differita di cui all'art.21, comma 4, lett. a",
    "TD25": "Fattura differita di cui all'art.21, comma 4, terzo periodo lett. b",
    "TD26": "Cessione di beni ammortizzabili e per passaggi interni",
    "TD27": "Fattura per autoconsumo o per cessioni gratuite senza rivalsa",
    "TD28": "Acquisti da San Marino con IVA (fattura cartacea)",
}

# ============================================================================
# EXPORT FORMATS
# ============================================================================

EXPORT_FORMATS = {
    "Markdown": {"ext": ".md", "icon": "📝", "mime": "text/markdown"},
    "JSON": {"ext": ".json", "icon": "📋", "mime": "application/json"},
    "TXT": {"ext": ".txt", "icon": "📄", "mime": "text/plain"},
    "PDF": {"ext": ".pdf", "icon": "📕", "mime": "application/pdf"},
}

CONTENT_OPTIONS = {
    "Conversazione completa": None,
    "Ultimi 10 messaggi": 10,
    "Ultimi 20 messaggi": 20,
    "Ultimi 50 messaggi": 50,
}

# ============================================================================
# UI - COLORI TEMA PROFESSIONALE
# ============================================================================

PRIMARY_COLOR = "#1a3a5c"       # Blu scuro professionale
SECONDARY_COLOR = "#2d6a9f"     # Blu medio
BACKGROUND_COLOR = "#f5f7fa"    # Sfondo chiaro
SUCCESS_COLOR = "#28a745"       # Verde successo
WARNING_COLOR = "#ffc107"       # Giallo avviso
DANGER_COLOR = "#dc3545"        # Rosso errore

USER_MESSAGE_COLOR = "#E3F2FD"
ASSISTANT_MESSAGE_COLOR = "#F5F5F5"
USER_MESSAGE_COLOR_DARK = "#1E3A5F"
ASSISTANT_MESSAGE_COLOR_DARK = "#2D2D2D"

# ============================================================================
# FILE UPLOAD IN CHAT
# ============================================================================

ALLOWED_UPLOAD_TYPES = ["pdf", "txt", "md", "docx", "xml", "png", "jpg", "jpeg"]

VISION_MODEL_PATTERNS = [
    "llava",
    "llava-llama3",
    "llava-phi3",
    "moondream",
    "minicpm-v",
]

MAX_FILE_SIZE_MB = 10
MAX_DOCUMENT_CHARS = 50000

# ============================================================================
# NAMESPACE XML FATTURA PA
# ============================================================================

FATTURA_PA_NAMESPACE = "urn:www.agenziaentrate.gov.it:specificheTecniche:sdi:fatturapa:v1.2"
