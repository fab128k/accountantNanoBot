# Coding Conventions

**Analysis Date:** 2026-03-18

## Naming Patterns

**Files:**
- Module files: `snake_case` with leading underscores for private modules (e.g., `_text_chunk` in `core/llm_client.py`)
- Example: `fattura_pa.py`, `piano_dei_conti.py`, `base_agent.py`
- Entry points: `app.py` (Streamlit), `__init__.py` for package exports

**Functions:**
- All functions use `snake_case`
- Private functions prefixed with single underscore: `_get_client()`, `_get_rag_context()`, `_get_connection()`
- Public functions unprefixed: `invoke()`, `stream_invoke()`, `parse_file()`, `salva_registrazione()`
- Example patterns: `get_local_ollama_models()`, `create_ollama_client()`, `init_db()`

**Variables:**
- Local variables: `snake_case` (e.g., `xml_bytes`, `hash_file`, `company_piva`)
- Constants: `UPPER_SNAKE_CASE` (e.g., `DEFAULT_MODEL`, `OLLAMA_BASE_URL`, `DB_PATH`)
- Configuration values from constants: `ALIQUOTE_IVA`, `TIPI_DOCUMENTO_FATTURA`
- Boolean flags: prefixed descriptively (e.g., `is_bilanciata`, `is_indexed()`, `is_nota_credito`)

**Types & Classes:**
- Classes: `PascalCase` (e.g., `FatturaPAParser`, `OllamaClient`, `RegistrazionePrimaNota`)
- Dataclasses: `PascalCase` (e.g., `Soggetto`, `RigaPrimaNota`, `FatturaPA`)
- Enum classes: `PascalCase` with `str` mixin (e.g., `TipoRegistrazione(str, Enum)`)
- Internal/helper classes prefixed with underscore: `_TextChunk`

**Modules:**
- Package organization: lowercase with underscores (e.g., `accounting/`, `parsers/`, `agents/`, `core/`, `rag/`, `ui/`)

## Code Style

**Formatting:**
- No explicit formatter configured (no `.prettierrc` or `black` config found)
- Style is Python-idiomatic, following PEP 8 conventions
- Line length: Implicit ~88-120 characters based on observed code

**Linting:**
- No explicit linter configuration (no `.eslintrc`, `pylint` config, or `ruff` config found)
- Uses type hints throughout: `from typing import ...` imports present in all modules
- TYPE_CHECKING pattern used to avoid circular imports: `if TYPE_CHECKING: ...` in `agents/base_agent.py`, `agents/orchestrator.py`

**Type Annotations:**
- Strong use of type hints: function parameters and returns annotated
- Optional types: `Optional[str]`, `Optional[date]`, `Optional[int]`
- Union types: `List[str]`, `Dict[str, Any]`, `Tuple[bool, str]`
- Generator types: `Generator[str, None, None]` for streaming
- Literal types used in parsing: `field(default_factory=Soggetto)`

## Import Organization

**Order:**
1. `__future__` imports for annotations: `from __future__ import annotations`
2. Standard library: `import hashlib`, `from datetime import date`, `from pathlib import Path`
3. Third-party libraries: `import streamlit as st`, `from openai import OpenAI`, `from lxml import etree`
4. Local imports: `from config import ...`, `from accounting.db import ...`
5. TYPE_CHECKING conditional imports (for type hints only)

**Path Aliases:**
- No path aliases or `@` imports configured
- Absolute imports from project root: `from config.constants import ...`, `from agents.orchestrator import ...`
- Relative imports avoided

**Example from `accounting/db.py`:**
```python
from __future__ import annotations
import hashlib
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from typing import List, Optional, Dict, Any
from config.constants import DB_PATH
```

## Error Handling

**Patterns:**
- Broad `except Exception as e` pattern used throughout (found in 30+ locations)
- Graceful degradation: return empty values on error (e.g., `return []` in `get_local_ollama_models()`)
- Error messages logged to Streamlit UI: `st.error()`, `st.warning()`
- No custom exception classes defined

**Core pattern in `core/llm_client.py`:**
```python
try:
    from openai import OpenAI
    client = OpenAI(base_url=self.base_url, api_key="ollama")
    response = client.chat.completions.create(...)
except Exception as e:
    return f"[Errore LLM: {e}]"
```

**Database pattern in `accounting/db.py`:**
```python
try:
    with sqlite3.connect(str(db_path)) as conn:
        # operations
except Exception:
    return None  # Silent failure
```

**UI pattern in `app.py`:**
```python
try:
    parser = FatturaPAParser()
    fatture = parser.parse_bytes(xml_bytes)
except Exception as e:
    st.error(f"❌ Errore parsing: {e}")
```

## Logging

**Framework:** No dedicated logging module (no `logging` imports found)

**Patterns:**
- Streamlit console feedback: `st.error()`, `st.warning()`, `st.success()`, `st.info()`
- Used in UI pages (`ui/pages/dashboard.py`, `ui/pages/prima_nota.py`, `ui/pages/onboarding.py`)
- Debug output via exception messages: bare exception caught and displayed to user
- No structured logging or log files configured

## Comments

**When to Comment:**
- Docstrings required for all public functions and classes
- Section headers use comment blocks with "=" decorations (e.g., `# ============================================================================`)
- Inline comments minimal; code is generally self-documenting

**Docstring Pattern (PEP 257 style):**
```python
def salva_registrazione(
    registrazione,  # RegistrazionePrimaNota
    db_path: Path = DB_PATH
) -> int:
    """
    Salva una registrazione di prima nota nel DB.

    Args:
        registrazione: Istanza di RegistrazionePrimaNota
        db_path: Path al DB

    Returns:
        ID della registrazione salvata
    """
```

**File headers:**
```python
# module_name.py
# AccountantNanoBot v1.0.0 - [Description]
# ============================================================================
# [Additional details]
# ============================================================================
```

## Function Design

**Size:** Medium functions (20-50 lines typical)
- Short functions for I/O: `_get_connection()`, `_get_client()` (5-10 lines)
- Medium functions for business logic: `parse_file()`, `invoke()` (40-60 lines)
- Longer functions in UI code: `_render_fatture_page()` (180 lines for complex UI with multiple tabs/buttons)

**Parameters:**
- Explicit over implicit: all parameters named, defaults specified
- Database path parameters: `db_path: Path = DB_PATH` (allows per-test override)
- Optional parameters use `Optional[]` type: `xml_path: Optional[str] = None`
- Maximum typically 7-8 parameters; complex data passed via dataclasses

**Return Values:**
- Single returns: direct value (`str`, `List[dict]`, `int`)
- Multiple returns: tuples (`Tuple[bool, str]`, `Tuple[bool, List[str]]`)
- Optional returns: `Optional[int]` with None for "not found"
- Dataclass returns: full structured objects (`FatturaPA`, `RegistrazionePrimaNota`)

## Module Design

**Exports:**
- Explicit via `__init__.py` (e.g., `core/__init__.py` re-exports from submodules)
- Convention: if a module is imported via package, it's exported from `__init__.py`

**Example from `core/__init__.py`:**
```python
from .llm_client import (
    get_local_ollama_models,
    OllamaClient,
    create_ollama_client,
    create_client,
)
```

**Barrel Files:** Used consistently
- `config/__init__.py` exports constants and config
- `agents/__init__.py` exports agent classes
- `accounting/__init__.py` re-exports db functions

## Decimal Precision

**Financial data:**
- Always use `Decimal` type for monetary amounts (found in `accounting/` modules)
- Conversions: `Decimal("0")`, `Decimal(str(value))` to avoid float precision loss
- Comparisons: `self.differenza < Decimal("0.01")` for tolerance checks
- Database storage: `DECIMAL(15,2)` SQL type

## Configuration

**Strategy:**
- Global constants: `config/constants.py` (paths, defaults, tax rates)
- Settings: `config/settings.py` (company config via YAML)
- Per-environment: `config.yaml` file (saved to `data/config.yaml`)
- LLM configuration: pass via function parameters (`temperature=0.1`)

**Env vars:**
- `.env` files supported via `python-dotenv` but not required for core functionality
- No secrets in code; configuration stored in local YAML

## Italian Domain Language

**Terminology preserved from domain:**
- Accounting: `prima_nota`, `registrazione`, `dare`, `avere`, `conto`
- Financial: `partita_iva`, `cedente`, `cessionario`, `fattura`
- Functions: `salva_registrazione()`, `calcola_hash_fattura()`
- Classes: `FatturaPA`, `RegistrazionePrimaNota`, `Soggetto`
- Constants: `ALIQUOTE_IVA`, `TIPI_DOCUMENTO_FATTURA`

---

*Convention analysis: 2026-03-18*
