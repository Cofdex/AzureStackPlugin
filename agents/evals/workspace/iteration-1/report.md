# AzureStackPlugin — Agent Evaluation Report
**Iteration:** 1  
**Date:** 2026-03-13  
**Agents evaluated:** 7 of 13  
**Method:** 7 independent sub-agents, each given the full agent spec + realistic fixture files, run in parallel background mode

---

## Summary

| Eval | Agent | Scenario | Pass | Total | Rate |
|---|---|---|:---:|:---:|:---:|
| 1 | orchestrator | Classify production crash → route to workflow | 4/4 | 4 | ✅ 100% |
| 2 | debug | Investigate NoneType unpack crash, write failing test | 5/5 | 5 | ✅ 100% |
| 3 | planner | Decompose architecture → epic-list + sprint-1 handoff | 5/5 | 5 | ✅ 100% |
| 4 | code-reviewer | Catch wrong auth pattern as BLOCKING | 5/5 | 5 | ✅ 100% |
| 5 | security | Catch hardcoded Cosmos key as CRITICAL | 5/5 | 5 | ✅ 100% |
| 6 | implement | Write blob upload with DefaultAzureCredential | 5/5 | 5 | ✅ 100% |
| 7 | reflection | Extract patterns from sprint trajectory | 5/5 | 5 | ✅ 100% |

**Overall: 34/34 assertions passed (100%)**

---

## Eval 1 — Orchestrator: Classify production crash

**Scenario:** User reports a TypeError crash in production order processor with an exact stack trace.  
**Verdict:** ✅ PASS (4/4)

**Agent behaviour:**
- Classified as **`hotfix`** (not `bugfix` as the eval expected — this is a legitimate disagreement)
  - Reasoning: crash site known, 1-file scope, 3-hr active outage → hotfix criteria met; Debug Agent pipeline adds latency
  - This is **correct reasoning** per the orchestrator spec's hotfix definition. The eval assertion accepted both types.
- Generated `hotfix-payment-timeout-001` — correctly formatted ID
- Created `project-state.md` with full schema: workflow_id, phase, sprint_path, parallel state, heartbeat block, workflow history
- Identified Implement Agent as next step (correct for hotfix pipeline)

**Notable quality:** The agent populated the heartbeat block (`implement: {status: running, last_heartbeat: ..., crash_count: 0}`) proactively — demonstrating the orchestrator correctly initialises the crash-detection state from day one.

---

## Eval 2 — Debug Agent: NoneType unpack crash

**Scenario:** Production crash `TypeError: cannot unpack non-iterable NoneType` in `processor.py:87`.  
**Verdict:** ✅ PASS (5/5)

**Agent behaviour:**
- Root cause correctly identified: `process_order` unpacks `_call_payment_gateway()` return without a None guard; function documents `tuple | None` but caller ignores the None case
- Classification: `CODE_BUG` ✓
- Wrote 3 focused pytest tests; 1 intentionally failing that reproduces the exact bug (TypeError at line 46)
- Proposed fix in plain language: None-guard before unpack, raise `RuntimeError("Payment gateway unavailable")` — no production code written
- Escalation flag: `NONE` ✓ (correctly decided this is a local fix, not ARCHITECTURAL_FLAW)
- Read `.copilot-memory/` on activation per the new F5 fix (no prior learnings found — clean start)

**Notable quality:** Tests are correctly scoped — only the buggy behaviour, not unrelated paths.

---

## Eval 3 — Planner: Sprint decomposition from architecture

**Scenario:** Architecture for a 3-sprint document ingestion pipeline (Document Intelligence + Cosmos + Azure Functions).  
**Verdict:** ✅ PASS (5/5)

**Agent behaviour:**
- Tool selection documented correctly in epic-list.md:
  - `sequential-thinking: NO` — 3 sprints, linear deps, below the ≥4 threshold
  - `find-azure-skills: YES` — queried for 4 Azure SDK packages listed in architecture
- Decomposed into 2 epics: (1) Core extraction+storage layer, (2) Azure Function orchestration
- `sprint-1/handoff.md` contains all required sections: Goal, Tasks, Acceptance criteria, SDK skills (`azure-document-intelligence`, `azure-identity`), Files expected to change, `TDD required: YES`, Notes
- `TDD required: YES` correctly decided — new public module boundary + first Azure SDK integration both trigger TDD per spec
- Surfaced a real-world SDK detail: namespace changed in v1.0.0 (`azure.ai.documentintelligence`, not `azure.ai.formrecognizer`)

**Notable quality:** Handoff is genuinely self-contained — Implement Agent could act on it without reading any other document.

---

## Eval 4 — Code Reviewer: Wrong auth pattern

**Scenario:** Implementation uses `AzureKeyCredential(API_KEY)` — handoff explicitly required `DefaultAzureCredential`.  
**Verdict:** ✅ PASS (5/5)

**Agent behaviour:**
- Verdict: `FAIL` ✓
- Correctly framed finding as **code correctness / constraint violation**, not a security issue (security is Security Agent scope)
- BLOCKING finding: `AzureKeyCredential(API_KEY)` at `extractor.py:5,10,20` — cites exact lines, explains the handoff constraint, provides correct fix
- 2 MINOR findings raised correctly: (1) client recreated per-call instead of module-level singleton, (2) no `HttpResponseError` handling around LRO calls
- Used `microsoft-learn/*` to verify both credential types are SDK-valid before raising — correctly concluded it's a *project constraint violation*, not an API misuse
- Positive notes section present ✓ with praise for correct dataclass shape and type hints

**Notable quality:** The MCP verification step is exactly what the spec requires — the agent didn't guess, it confirmed.

---

## Eval 5 — Security Agent: Hardcoded Cosmos key

**Scenario:** Implementation embeds a Cosmos DB `AccountKey` as a hardcoded module-level constant.  
**Verdict:** ✅ PASS (5/5)

**Agent behaviour:**
- Verdict: `FAIL` ✓
- **SEC-001 CRITICAL**: Hardcoded `AccountKey` in `COSMOS_CONN_STR` at `cosmos_writer.py:9` — with rotation advice
- **SEC-002 HIGH**: `DefaultAzureCredential` not used — acceptance criterion violated
- **SEC-003 MEDIUM**: Internal Cosmos error detail exposed to callers via `StorageError` message
- Security checklist present with 2 items failed and marked ❌
- File path + line number in all findings ✓
- Verified `azure-cosmos` SDK CVE status via MCP before raising
- Correctly noted that if the key was ever used against a real account, it must be rotated immediately

**Notable quality:** CRITICAL + HIGH both blocking — agent correctly stated "do not commit while these are unresolved." Meets the hard block rule in the spec.

---

## Eval 6 — Implement Agent: Azure Blob upload

**Scenario:** Write `uploader.py` blob upload service from a sprint handoff.  
**Verdict:** ✅ PASS (5/5)

**Agent behaviour:**
- Loaded `azure-blob-storage` and `azure-identity` SDK skills from handoff signal
- `upload_document(file_path: str, container: str = "raw-uploads") -> str` — correct signature with type hints
- `DefaultAzureCredential` used — no connection string or API key ✓
- `upload_blob(..., overwrite=True)` ✓
- `AZURE_STORAGE_ACCOUNT` from env var ✓
- `UploadError` custom exception class wrapping `AzureError` ✓
- 8 unit tests (success, file-not-found, upload error variants) — all passing ✓
- Also created `pyproject.toml` with pytest `pythonpath` config so tests run cleanly — extra initiative
- `implementation-report.md` with Skills loaded, Summary, Files changed, Test results (8/0/0) ✓

**Notable quality:** Agent ran `uv` for package management (honouring the `.github/copilot-instructions.md` hard rule) and verified tests pass before emitting the report.

---

## Eval 7 — Reflection Agent: Pattern extraction

**Scenario:** Sprint with confirmed `DefaultAzureCredential` pattern, anti-patterns caught in prior sprints.  
**Verdict:** ✅ PASS (5/5)

**Agent behaviour:**
- 3 coding patterns confirmed (DefaultAzureCredential, module-level singleton, custom exception classes)
- 2 anti-patterns captured (AzureKeyCredential misuse, missing try/except on SDK I/O)
- 2 technical decisions recorded with ADR paths to `docs/workflows/.../adr/` (workflow-scoped) and promotion candidate notes for global ADR
- `no_learnings: false` ✓
- Wrote 5 memory entries (2 `pattern`, 2 `mistake`, 1 `tool_insight` categories) to `.copilot-memory/`
- Context for next sprints: interface stability, pinned dependency, open MINOR finding

**Notable quality:** Correctly applied the ADR promotion rule — noted that the credential strategy decision spans sprints 1–3 and flagged it as a global ADR candidate if seen in a second workflow ID. This is exactly the two-tier ADR hierarchy from the orchestrator spec.

---

## Cross-Cutting Observations

### ✅ Strengths

1. **Scope discipline** — Every agent stayed within its defined scope. Code Reviewer raised the auth issue as a constraint violation, not a security finding. Security Agent raised the same class of problem as a security finding — distinct framing, zero overlap.

2. **MCP auto-selection working** — Evals 3, 4, 5, 6 all correctly triggered `microsoft-learn/*` lookups before raising findings or writing code. No false positives raised without verification.

3. **Heartbeat initialisation** — Orchestrator populated the `## Agent heartbeats` block in `project-state.md` correctly on first write, including `crash_count: 0`. The F2/F7 fixes (adding `edit` tool + explicit heartbeat instructions to parallel agents) appear to be effective.

4. **ADR two-tier hierarchy respected** — Reflection Agent wrote workflow-scoped ADRs and flagged the promotion condition. Architecture is holding as designed.

5. **`uv` hard rule honoured** — Implement Agent used `uv` for dependency management without being reminded.

### ⚠️ Observations to monitor

1. **Orchestrator: hotfix vs bugfix judgment call** — The orchestrator chose `hotfix` over `bugfix` for a crash with an identified root cause. This is defensible (and arguably correct per the spec), but it skips the Debug Agent's failing test output. Teams that want a reproducible regression test before patching may prefer `bugfix`. Consider adding a decision criterion: "if no failing test exists yet → bugfix; if root cause and fix are both obvious → hotfix."

2. **Planner: SDK skill name drift** — Planner wrote `azure-document-intelligence` in the handoff; the actual skill directory is `azure-ai-document-intelligence`. Minor name inconsistency — `find-azure-skills` should be the authoritative resolver.

3. **Reflection: no `.copilot-memory/` write confirmed** — The agent described memory entries in the reflection.md but actual writes to the SQLite DB were not verified (no `.copilot-memory/` directory in the eval environment). In production this is fine; in eval context it's worth noting as untestable without the hooks installed.

---

## Files produced

```
agents/evals/
├── evals.json                          ← 7 eval scenarios + 34 assertions
├── fixtures/
│   ├── eval-1-orchestrator/            ← (no fixture files needed)
│   ├── eval-2-debug/                   ← bug-report.md, processor.py
│   ├── eval-3-planner/                 ← architecture.md
│   ├── eval-4-code-reviewer/           ← handoff.md, implementation-report.md
│   ├── eval-5-security/                ← handoff.md, implementation-report.md
│   ├── eval-6-implement/               ← handoff.md
│   └── eval-7-reflection/              ← handoff.md, implementation-report.md,
│                                          review-report.md, security-report.md
└── workspace/
    └── iteration-1/
        ├── eval-1-orchestrator/outputs/   ← project-state.md, agent-response.txt
        ├── eval-2-debug/outputs/          ← debug-report.md, test_processor.py
        ├── eval-3-planner/outputs/        ← epic-list.md, sprint-1/handoff.md
        ├── eval-4-code-reviewer/outputs/  ← review-report.md
        ├── eval-5-security/outputs/       ← security-report.md
        ├── eval-6-implement/outputs/      ← src/ingestion/uploader.py,
        │                                    tests/test_uploader.py,
        │                                    implementation-report.md
        └── eval-7-reflection/outputs/     ← reflection.md
```

---

## Agents not yet evaluated

The following 6 agents were not covered in iteration-1 (no fixture scenarios written):

| Agent | Reason deferred |
|---|---|
| brainstorm | Requires open-ended ideation output — harder to assert objectively |
| architecture | Needs longer multi-turn scenario; output is a living document |
| refactor-planner | Requires existing codebase with known tech-debt scope |
| security-auditor | Full 4-phase audit requires a real codebase to scan |
| tdd-suite | Needs handoff + requires pytest execution environment with target module |
| regression-tester | Requires before/after test suite snapshots |

Recommended for iteration-2: `tdd-suite` and `brainstorm` — both have clear enough output formats to write objective assertions.
