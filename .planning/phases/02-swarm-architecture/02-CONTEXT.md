# Phase 2: Swarm Architecture - Context

**Gathered:** 2026-03-18
**Status:** Ready for planning

<domain>
## Phase Boundary

Create `swarm/context.py` (ProcessingContext) and `swarm/base.py` (BaseSwarmAgent); migrate the
three existing agents (FatturazioneAgent, MemoriaAgent) and the Orchestrator to use the new pattern
without breaking the Streamlit UI. No new accounting features in this phase.

</domain>

<decisions>
## Implementation Decisions

### ProcessingContext
- Use a Python `@dataclass` (not a plain class)
- Fields: `client_folder: Path`, `current_file: Path | None`, `errors: list[str]`, `metadata: dict`
- `errors` and `metadata` use `field(default_factory=...)` for mutable defaults
- Context is NOT accounting-aware at the base level — agents write domain outputs into `metadata`
  (e.g. `context.metadata['registrazione_suggerita'] = reg`)
- No results list, no accounting-domain fields at the base level

### BaseSwarmAgent inheritance
- `BaseSwarmAgent` extends `BaseAccountingAgent` (additive, not a replacement)
- `BaseSwarmAgent` adds `process(context: ProcessingContext) -> ProcessingContext` as an
  `@abstractmethod` (via ABC)
- All existing specialized methods on agents (`analizza_xml_bytes`, `stream_commento_fattura`,
  `cerca_in_documenti`, etc.) are preserved — no removals
- `app.py` and all UI code remain unchanged — zero UI regression risk

### Agent migration (SWARM-03)
- `FatturazioneAgent` and `MemoriaAgent` both inherit from `BaseSwarmAgent` (which now extends
  `BaseAccountingAgent`)
- Each agent implements `process(context)` — minimal implementation: routes to relevant specialized
  method based on context fields, writes output to `context.metadata`, appends any errors to
  `context.errors`, returns context
- Placeholder agents in `build_default_orchestrator()` (iva, bilancio, compliance, prima_nota)
  also gain `process()` — default implementation that returns context unchanged (they don't have
  domain logic yet)

### Orchestrator
- Orchestrator does NOT extend BaseSwarmAgent — it stays a separate routing class
- Existing `route()` method unchanged (used by chat UI)
- New method added: `route_with_context(context: ProcessingContext) -> ProcessingContext`
  - Uses same keyword routing on `context.metadata.get('user_message', '')`
  - Calls `agent.process(context)` on the selected agent
  - Returns the processed context; does NOT raise on errors — caller checks `context.errors`
- `set_rag_manager()` and `list_agents()` unchanged

### Error handling
- Agents append error strings to `context.errors` — they do NOT raise exceptions from `process()`
- Caller (pipeline or UI adapter) checks `len(context.errors) > 0` after calling
  `route_with_context()`

### Claude's Discretion
- Exact `process()` implementation bodies for each agent (what goes into metadata, how errors are
  formatted)
- Whether `swarm/__init__.py` re-exports ProcessingContext and BaseSwarmAgent for convenient imports
- File-level docstring style and inline comments
- How placeholder agents' `process()` logs that they have no domain logic yet

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Requirements
- `.planning/REQUIREMENTS.md` §Swarm Architecture — SWARM-01, SWARM-02, SWARM-03 define exact
  acceptance criteria

### Files to create
- `swarm/context.py` — new file: ProcessingContext dataclass
- `swarm/base.py` — new file: BaseSwarmAgent ABC
- `swarm/__init__.py` — new file: module init

### Files to migrate (read before touching)
- `agents/base_agent.py` — current base class; BaseSwarmAgent extends this
- `agents/fatturazione_agent.py` — gains `process()`, keeps all specialized methods
- `agents/memoria_agent.py` — gains `process()`, keeps all specialized methods
- `agents/orchestrator.py` — gains `route_with_context()`; `route()` and all existing API
  unchanged

### Files confirmed NOT needing changes
- `app.py` — uses `orchestrator.get_agent()` and specialized methods; additive migration means
  zero touch
- All `ui/pages/` — no agent API changes visible to UI layer

### Project-level context
- `.planning/PROJECT.md` §Key Decisions — Swarm pattern decision recorded; agents sequential
  (not parallel) due to hardware constraints
- `.planning/STATE.md` §Accumulated Context — architecture decisions from Phase 1

No external specs or ADRs — all requirements are captured in REQUIREMENTS.md and decisions above.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `agents/base_agent.py` `BaseAccountingAgent`: lazy `_client` init pattern, `_get_rag_context()`,
  `ask()`/`stream_ask()` — BaseSwarmAgent inherits all of this for free
- `core/llm_client.py` `OllamaClient`: already native openai SDK — no changes needed
- `agents/orchestrator.py` `_ROUTING_RULES`: existing keyword list reused by `route_with_context()`

### Established Patterns
- Lazy initialization: `self._client = None` + `_get_client()` — same pattern applies to any new
  init work in BaseSwarmAgent
- TYPE_CHECKING guards: `agents/base_agent.py` uses `if TYPE_CHECKING:` for circular-import-safe
  type hints — use same pattern for `ProcessingContext` type hint in `base_agent.py` if needed
- Agents stored in `st.session_state["orchestrator"]` — the orchestrator instance is reused across
  Streamlit reruns; `route_with_context()` must be stateless (no side effects on the orchestrator
  itself)

### Integration Points
- `agents/orchestrator.py` `build_default_orchestrator()` — constructs all agents; needs updating
  to import from `swarm/` instead of any separate location
- `app.py` `ensure_orchestrator()` — creates and caches the orchestrator; no changes needed since
  we're additive
- `agents/__init__.py` — check whether it needs to re-export BaseSwarmAgent for convenience

</code_context>

<specifics>
## Specific Ideas

- The `process()` method on FatturazioneAgent should check if `context.current_file` is set and
  ends with `.xml`; if so, call `analizza_xml_bytes()` with bytes read from that path and write the
  result to `context.metadata['registrazione_suggerita']`
- `ProcessingContext` should be importable as `from swarm import ProcessingContext`

</specifics>

<deferred>
## Deferred Ideas

- File-type-based routing in `route_with_context()` (route by `.xml`/`.csv` extension instead of
  keywords) — deferred to Phase 4 Pipeline A, where it will be more natural
- `run_pipeline(context, agent_ids)` chaining multiple agents — deferred to Phase 3 or 4 when the
  pipeline actually needs it
- Parallel agent execution — explicitly out of scope (hardware constraint: 16GB/4GB VRAM, one LLM
  at a time)

</deferred>

---

*Phase: 02-swarm-architecture*
*Context gathered: 2026-03-18*
