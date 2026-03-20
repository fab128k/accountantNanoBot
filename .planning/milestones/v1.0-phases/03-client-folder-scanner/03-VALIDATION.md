---
phase: 3
slug: client-folder-scanner
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-18
---

# Phase 3 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest |
| **Config file** | `conftest.py` (project root — adds root to sys.path) |
| **Quick run command** | `/home/admaiora/.local/bin/pytest tests/test_scanner.py -x -q` |
| **Full suite command** | `/home/admaiora/.local/bin/pytest tests/ -q` |
| **Estimated runtime** | ~3 seconds |

---

## Sampling Rate

- **After every task commit:** Run `/home/admaiora/.local/bin/pytest tests/test_scanner.py -x -q`
- **After every plan wave:** Run `/home/admaiora/.local/bin/pytest tests/ -q`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** ~3 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 3-01-01 | 01 | 0 | SCAN-01 | unit | `/home/admaiora/.local/bin/pytest tests/test_scanner.py::TestClientFolderScanner -x -q` | Wave 0 | ⬜ pending |
| 3-01-02 | 01 | 1 | SCAN-01 | unit | `/home/admaiora/.local/bin/pytest tests/test_scanner.py::TestClassification::test_fattura_xml_classified -x -q` | Wave 0 | ⬜ pending |
| 3-01-03 | 01 | 1 | SCAN-01 | unit | `/home/admaiora/.local/bin/pytest tests/test_scanner.py::TestClassification::test_generic_xml_to_altro -x -q` | Wave 0 | ⬜ pending |
| 3-01-04 | 01 | 1 | SCAN-01 | unit | `/home/admaiora/.local/bin/pytest tests/test_scanner.py::TestClassification::test_extension_dispatch -x -q` | Wave 0 | ⬜ pending |
| 3-01-05 | 01 | 1 | SCAN-01 | unit | `/home/admaiora/.local/bin/pytest tests/test_scanner.py::TestScannerEdgeCases::test_missing_folder -x -q` | Wave 0 | ⬜ pending |
| 3-01-06 | 01 | 1 | SCAN-01 | unit | `/home/admaiora/.local/bin/pytest tests/test_scanner.py::TestClientFolderScanner::test_recursive -x -q` | Wave 0 | ⬜ pending |
| 3-02-01 | 02 | 1 | SCAN-02 | manual | N/A — Streamlit UI not testable in pytest | manual-only | ⬜ pending |
| 3-03-01 | 03 | 1 | SCAN-03 | unit | `/home/admaiora/.local/bin/pytest tests/test_scanner.py::TestPipelineAStub -x -q` | Wave 0 | ⬜ pending |
| 3-03-02 | 03 | 1 | SCAN-03 | unit | `/home/admaiora/.local/bin/pytest tests/test_scanner.py::TestPipelineAStub::test_import -x -q` | Wave 0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_scanner.py` — stubs for SCAN-01 (scanner classification, edge cases) and SCAN-03 (pipeline stub import and NotImplementedError contract)

*Existing `conftest.py` (project root) already covers sys.path — no changes needed.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| `render_scanner()` renders sidebar folder selector and classified file list in Streamlit | SCAN-02 | Streamlit runtime required — no pytest Streamlit server available | Launch `streamlit run app.py`, navigate to Scanner page, enter a folder path, verify classified file list renders with category counts |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 5s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
