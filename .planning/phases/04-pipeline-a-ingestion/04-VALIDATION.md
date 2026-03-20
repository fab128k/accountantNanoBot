---
phase: 4
slug: pipeline-a-ingestion
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-20
---

# Phase 4 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.x |
| **Config file** | tests/conftest.py (exists) |
| **Quick run command** | `pytest tests/test_pipeline_a.py -q` |
| **Full suite command** | `pytest tests/ -q` |
| **Estimated runtime** | ~3 seconds |

---

## Sampling Rate

- **After every task commit:** Run `pytest tests/test_pipeline_a.py -q`
- **After every plan wave:** Run `pytest tests/ -q`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 5 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 04-01-01 | 01 | 1 | PIPE-01 | unit | `pytest tests/test_pipeline_a.py::TestInvoicePipeline -q` | ❌ W0 | ⬜ pending |
| 04-01-02 | 01 | 1 | PIPE-02 | unit | `pytest tests/test_pipeline_a.py::TestDedup -q` | ❌ W0 | ⬜ pending |
| 04-01-03 | 01 | 1 | PIPE-03 | unit | `pytest tests/test_pipeline_a.py::TestCSVParser -q` | ❌ W0 | ⬜ pending |
| 04-01-04 | 01 | 1 | PIPE-04 | unit | `pytest tests/test_pipeline_a.py::TestBankMovements -q` | ❌ W0 | ⬜ pending |
| 04-02-01 | 02 | 2 | PIPE-01, PIPE-02 | integration | `pytest tests/test_pipeline_a.py -q` | ❌ W0 | ⬜ pending |
| 04-02-02 | 02 | 2 | PIPE-03, PIPE-04 | integration | `pytest tests/test_pipeline_a.py -q` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_pipeline_a.py` — stubs for PIPE-01 through PIPE-04 (invoice pipeline, dedup, CSV parser, bank movement review)
- [ ] Fixtures: sample FatturaPA XML bytes, sample CSV bank statement content, in-memory SQLite DB

*Existing infrastructure (tests/conftest.py, pytest) covers the framework needs.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Invoice review cards render in Scanner page | PIPE-01 | Streamlit runtime required | Run app, scan CLIENTI/ folder, click "Avvia elaborazione", verify invoice cards appear with Fornitore/Importo/Tipo fields |
| "Gia importata" badge on duplicate invoice | PIPE-02 | Streamlit session_state | Import invoice, restart app, re-scan same folder, verify badge appears instead of review card |
| Bank movement table renders with accept/correct | PIPE-04 | Streamlit runtime required | Run app with CSV in scan results, verify each movement row shows suggested CoA and accept/correct buttons |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 5s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
