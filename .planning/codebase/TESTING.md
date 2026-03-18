# Testing Patterns

**Analysis Date:** 2026-03-18

## Test Framework

**Status:** No test framework configured

**Runner:**
- Not detected. No `pytest`, `unittest`, `vitest`, or `jest` dependencies in `requirements.txt`
- No test configuration files found (`pytest.ini`, `conftest.py`, `tox.ini`, `.github/workflows`)

**Assertion Library:**
- Not applicable — testing infrastructure not yet established

**Run Commands:**
- Not documented. No test scripts in `pyproject.toml` or `package.json`

## Test File Organization

**Current State:**
- Zero test files present in codebase
- No `tests/` directory
- No co-located test files (`*.test.py`, `*.spec.py`)

**Planned Approach (based on project structure):**
- Test directory: `tests/` at project root (to mirror `src/` layout)
- Naming convention: `test_<module>.py` (pytest standard)
- Co-location: Could also use `src/<module>/test_<module>.py` pattern for unit tests

## Manual Testing Coverage

**Current Testing Approach:**
The project relies on manual testing via the Streamlit UI and manual verification. Evidence:

**Integration testing via UI (`app.py`):**
- Manual invoice upload and parsing: `_render_fatture_page()` (lines 114-357)
- User confirmation step before saving: `st.button("✅ Conferma e Salva")`
- Registration confirmation: manual review in Prima Nota page
- Example flow:
  1. User uploads XML file
  2. System parses and suggests registration
  3. User reviews suggested accounting entry
  4. User clicks "Conferma e Salva" to persist to DB

**Manual database verification:**
- `accounting/db.py` includes query functions (`get_prima_nota()`, `get_fatture_importate()`, `get_statistiche()`)
- UI displays results via pandas DataFrames for manual inspection
- Example: `Prima Nota` page renders all registrazioni with `st.dataframe()`

**Agent testing via chat:**
- `ui/chat.py` provides conversation interface
- `agents/base_agent.py` has `ask()` and `stream_ask()` methods for manual interaction
- LLM-generated commentary tested on-demand: `💬 Commento dell'Agente (LLM)` expander in UI

## Unit Testing Readiness

**Testable Components:**

**1. Parser Layer (`parsers/fattura_pa.py`)**
```python
# Could test:
parser = FatturaPAParser()
fatture = parser.parse_bytes(xml_bytes)
assert len(fatture) > 0
assert fatture[0].numero == "123"
assert fatture[0].importo_totale == Decimal("100.00")
```

**2. Accounting Logic (`accounting/prima_nota.py`)**
```python
# Could test:
riga = RigaPrimaNota(
    conto_codice="C.II.1",
    conto_nome="Clienti",
    dare=Decimal("100.00")
)
assert riga.is_dare == True
assert riga.importo == Decimal("100.00")

reg = RegistrazionePrimaNota(
    data=date(2026, 1, 15),
    tipo=TipoRegistrazione.FATTURA_ACQUISTO,
    descrizione="Fattura fornitore",
    righe=[riga, ...]
)
assert reg.is_bilanciata == True  # After balancing rows
```

**3. Database Layer (`accounting/db.py`)**
```python
# Could test:
hash_val = calcola_hash_fattura(xml_bytes)
assert len(hash_val) == 64  # SHA256 hex
assert fattura_gia_importata(xml_bytes) == False  # Before import
salva_fattura_importata(fattura, xml_bytes)
assert fattura_gia_importata(xml_bytes) == True  # After import
```

**4. LLM Client (`core/llm_client.py`)**
```python
# Could test with mocked OpenAI client:
client = OllamaClient(
    model="llama3.2:3b",
    system_prompt="You are an accountant",
    base_url="http://localhost:11434/v1"
)
response = client.invoke("2+2=?")
assert isinstance(response, str)
assert len(response) > 0
```

## Error Handling Patterns (for testing)

**Current error handling in code:**

```python
# Pattern 1: Silent failure with default return (core/llm_client.py)
try:
    proc = subprocess.run(["ollama", "list"], ...)
    # process output
except Exception:
    return []  # Empty list if ollama not available
```

**Test consideration:** Mock `subprocess.run` to raise Exception, verify empty list returned

```python
# Pattern 2: Return error message string (core/llm_client.py)
try:
    response = client.chat.completions.create(...)
except Exception as e:
    return f"[Errore LLM: {e}]"
```

**Test consideration:** Mock OpenAI client to raise, verify error message format

```python
# Pattern 3: UI error display (accounting/db.py)
try:
    cursor.execute("""...""", params)
    conn.commit()
except Exception as e:
    st.error(f"❌ Errore salvataggio: {e}")
    return None
```

**Test consideration:** Mock database connection to raise, verify None returned

## Mocking Strategy

**Required Mocks (for unit tests):**

1. **Ollama API** (`core/llm_client.py`)
   - Mock `OpenAI` client from `openai` library
   - Mock `subprocess.run()` for model list

2. **SQLite Database** (`accounting/db.py`)
   - Use in-memory database: `sqlite3.connect(":memory:")`
   - Or use `tmp_path` pytest fixture for file-based testing

3. **Streamlit Components** (UI testing)
   - Mock `streamlit` functions: `st.error()`, `st.button()`, `st.session_state`
   - Use `streamlit.testing.v1` (available in Streamlit >= 1.28)

4. **File I/O** (`core/file_processors.py`)
   - Mock `Path.read_bytes()`, `open()`
   - Use `tmp_path` for temporary test files

## What to Mock vs. What NOT to Mock

**Mock (External dependencies):**
- `OpenAI` client calls (simulated responses)
- `subprocess` calls (ollama commands)
- `sqlite3` connections (use in-memory DB instead)
- Streamlit components
- File system calls

**Don't Mock (Core business logic):**
- Dataclass initialization: test `FatturaPA`, `RegistrazionePrimaNota` directly
- Parser logic: test `FatturaPAParser` with real XML samples
- Accounting calculations: test `is_bilanciata`, `totale_dare`, `totale_avere` with real data
- Database schema: test with in-memory SQLite, not mock

## Fixtures and Factories

**None currently defined.** Recommended structure:

```python
# tests/conftest.py
import pytest
from datetime import date
from decimal import Decimal
from accounting.prima_nota import RigaPrimaNota, RegistrazionePrimaNota, TipoRegistrazione

@pytest.fixture
def sample_riga():
    """Sample accounting line for testing."""
    return RigaPrimaNota(
        conto_codice="C.II.1",
        conto_nome="Clienti",
        dare=Decimal("100.00"),
        avere=Decimal("0")
    )

@pytest.fixture
def sample_registrazione(sample_riga):
    """Sample balanced accounting entry."""
    return RegistrazionePrimaNota(
        data=date(2026, 1, 1),
        tipo=TipoRegistrazione.FATTURA_VENDITA,
        descrizione="Test invoice",
        righe=[
            sample_riga,
            RigaPrimaNota(
                conto_codice="B.I.1",
                conto_nome="Revenue",
                dare=Decimal("0"),
                avere=Decimal("100.00")
            )
        ]
    )

@pytest.fixture
def sample_fattura_xml():
    """Sample FatturaPA XML for testing."""
    return b"""<?xml version="1.0" encoding="UTF-8"?>
    <FatturaElettronica xmlns="urn:www.agenziaentrate.gov.it:specificheTecniche:sdi:fatturapa:v1.2">
        <!-- sample FPR12 invoice -->
    </FatturaElettronica>"""
```

**Test Data Location:**
- `tests/fixtures/` — static XML, PDF, YAML files
- `tests/conftest.py` — pytest fixtures and factories

## Coverage Requirements

**Not enforced.** No coverage configuration found.

**Recommendations for future:**
- Minimum 70% coverage for `accounting/` (financial logic critical)
- Minimum 60% coverage for `parsers/` (XML parsing complex)
- Minimum 50% coverage for `agents/` (LLM-based, harder to test deterministically)
- Skip coverage for Streamlit UI pages (manual testing sufficient)

**View Coverage Command (when pytest + pytest-cov installed):**
```bash
pytest --cov=accounting --cov=parsers --cov=core --cov-report=html
# Open htmlcov/index.html in browser
```

## Test Types

**Unit Tests (Planned):**
- Scope: Individual functions and dataclasses
- Approach: Direct function calls with known inputs, assert expected outputs
- Examples:
  - `test_parsing_valid_xml()` — verify `FatturaPAParser.parse_bytes()`
  - `test_registrazione_bilanciamento()` — verify `is_bilanciata` property
  - `test_db_deduplication()` — verify `fattura_gia_importata()` logic

**Integration Tests (Planned):**
- Scope: Multi-step workflows (upload → parse → register → save)
- Approach: Use real/test database, mock only external APIs
- Examples:
  - `test_invoice_workflow()` — full flow from XML upload to DB save
  - `test_rag_indexing()` — document upload to vector store

**E2E Tests (Not planned):**
- Scope: Full Streamlit application flow
- Status: Not detected. Would require `streamlit.testing.v1` or Selenium
- Recommendation: Manual testing via Streamlit UI sufficient for alpha

## Async Testing

**Not applicable.** No async code detected in codebase.

**All functions are synchronous:**
- Database: synchronous `sqlite3` API
- LLM client: synchronous `openai.OpenAI`, no `asyncio`
- Streamlit: synchronous callback handlers

## Current Validation Patterns (as testing substitute)

**Dataclass validation methods:**
```python
# In accounting/prima_nota.py
def valida(self) -> Tuple[bool, str]:
    """Validates individual accounting line."""
    if self.dare > 0 and self.avere > 0:
        return False, f"Riga '{self.conto_codice}': dare e avere non possono essere entrambi > 0"
    ...
    return True, "OK"
```

**Database integrity checks:**
```python
# In accounting/prima_nota.py
@property
def is_bilanciata(self) -> bool:
    """Checks if registration balances (DARE == AVERE)."""
    return self.differenza < Decimal("0.01")
```

**UI-level validation:**
```python
# In ui/pages/prima_nota.py
if st.button("Salva Registrazione"):
    ok, errori = registrazione.valida()
    if not ok:
        for err in errori:
            st.error(f"❌ {err}")
    else:
        # Save to DB
```

## Setup for Testing Infrastructure (RECOMMENDED)

**1. Add test dependencies to `requirements.txt`:**
```
pytest>=7.4.0
pytest-cov>=4.1.0
pytest-asyncio>=0.21.0  # If async testing added later
```

**2. Create `pytest.ini`:**
```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = --strict-markers
markers =
    unit: Unit tests
    integration: Integration tests
    slow: Slow tests
```

**3. Create `tests/conftest.py` with fixtures**

**4. Organize tests:**
```
tests/
├── conftest.py
├── fixtures/
│   ├── samples/
│   │   ├── fattura_sample.xml
│   │   └── company_config.yaml
│   └── __init__.py
├── unit/
│   ├── test_parser.py
│   ├── test_accounting.py
│   └── test_llm_client.py
└── integration/
    ├── test_invoice_workflow.py
    └── test_rag_workflow.py
```

---

*Testing analysis: 2026-03-18*
