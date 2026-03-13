# Sprint 1 — Code Review Report

## Verdict: FAIL

## Summary

The extraction service implementation fulfils the structural requirements — correct dataclass shape, type hints, `prebuilt-read` model — but contains a BLOCKING deviation from the handoff: authentication uses `AzureKeyCredential` (API key) instead of the explicitly mandated `DefaultAzureCredential`. This was acknowledged as a deviation in `implementation-report.md` and is not an oversight; it is a constraint violation that must be corrected before the sprint can be accepted. Two additional minor issues (no error handling, client recreated per call) were identified but do not block on their own.

## Findings

### [BLOCKING] Wrong authentication credential — AzureKeyCredential used instead of DefaultAzureCredential

- **File**: `src/extraction/extractor.py`, lines 5, 10, 20
- **Issue**: `DocumentIntelligenceClient` is constructed with `AzureKeyCredential(API_KEY)`, reading from a `DOCUMENT_INTELLIGENCE_KEY` environment variable. Handoff task 3 and acceptance criteria explicitly state: *"Authenticate with `DefaultAzureCredential` — not API key."* The deviation was self-reported in `implementation-report.md` as intentional ("for easier local testing") but was not approved; a TODO comment is not a waiver.
- **Impact**: The constraint exists because Managed Identity / workload identity is the required auth path for this service in all environments including local dev (via `az login`). Shipping `AzureKeyCredential` would require a long-lived API key to be provisioned, rotated, and stored — all outside the approved deployment model. The sprint cannot be signed off until this is corrected.
- **Suggested fix**:
  ```python
  # Remove:
  from azure.core.credentials import AzureKeyCredential
  API_KEY = os.environ["DOCUMENT_INTELLIGENCE_KEY"]

  # Add:
  from azure.identity import DefaultAzureCredential

  # In extract_from_blob (or as module-level singleton):
  client = DocumentIntelligenceClient(ENDPOINT, DefaultAzureCredential())
  ```

---

### [MINOR] SDK client recreated on every call — should be a module-level singleton

- **File**: `src/extraction/extractor.py`, line 20
- **Issue**: `DocumentIntelligenceClient(...)` is instantiated inside `extract_from_blob`, so a new client (and underlying HTTP connection pool) is created on every invocation.
- **Impact**: Unnecessary overhead; connection pool churn under load. The review checklist flags "credentials or clients recreated per-request" as a code quality issue.
- **Suggested fix**: Initialise the client once at module level (after switching to `DefaultAzureCredential`):
  ```python
  _client = DocumentIntelligenceClient(ENDPOINT, DefaultAzureCredential())

  def extract_from_blob(blob_uri: str) -> ExtractionResult:
      poller = _client.begin_analyze_document_from_url("prebuilt-read", blob_uri)
      ...
  ```

---

### [MINOR] No error handling around SDK calls — unhandled HttpResponseError will crash

- **File**: `src/extraction/extractor.py`, lines 21–22
- **Issue**: `begin_analyze_document_from_url` and `poller.result()` can both raise `azure.core.exceptions.HttpResponseError` (e.g., throttling, service unavailable, invalid blob URI). Neither call is wrapped.
- **Impact**: Any transient or permanent API failure will surface as an unhandled exception with no context for the caller.
- **Suggested fix**: Wrap with a `try/except HttpResponseError` and re-raise as a domain-level exception, or at minimum log the error before propagating.

---

## Test coverage assessment

The implementation report states `pytest: 4 passed, 0 failed, 0 skipped`. The handoff acceptance criteria requires four test scenarios: success path, empty document, service unavailable (mock SDK), and full type-hint coverage. All four map cleanly to the reported count, which is consistent.

However, the full `tests/test_extractor.py` source was not attached to the implementation report — only `extractor.py` was included. As a result, it is not possible to verify:

1. Whether the "service unavailable" test actually asserts the exception propagation path (rather than silently passing because no exception handling exists in the implementation).
2. Whether mocks match the actual `DocumentIntelligenceClient` method signatures (in particular, whether `begin_analyze_document_from_url` is mocked at the correct import path).

**Assessment**: Reported coverage is plausible given the test count, but the missing test source is a gap. On re-spin the test file should be attached to the implementation report, and tests for the error path should be re-validated once error handling is added to the implementation.

---

## Verification notes

- **`DefaultAzureCredential` as required auth pattern** — Confirmed via Microsoft Learn docs (SDK target REST API v4.0 GA): Microsoft documents `DefaultAzureCredential` as the recommended pattern for production Azure AI Document Intelligence clients in Python. `AzureKeyCredential` is documented as valid but is positioned as a simpler alternative for getting started, not for production managed deployments. Source: https://learn.microsoft.com/en-us/azure/ai-services/document-intelligence/how-to-guides/use-sdk-rest-api
- **`DocumentIntelligenceClient` constructor signature** — Confirmed: first arg is `endpoint: str`, second arg is `credential` (accepts both `AzureKeyCredential` and `TokenCredential` / `DefaultAzureCredential`). The BLOCKING finding is therefore a constraint violation, not an API misuse — both credential types are accepted by the SDK, but only `DefaultAzureCredential` is permitted by this project's handoff.
- **`begin_analyze_document_from_url` with `"prebuilt-read"`** — Model name and method call confirmed correct per SDK docs. No issue here.
- **`poller.result()` pattern** — Standard LRO (Long Running Operation) pattern for Azure SDK Python; confirmed correct.

---

## Positive notes

- `ExtractionResult` dataclass matches the handoff spec exactly: `page_count: int`, `text_blocks: list[str]`, `tables: list[dict]`, `source_blob: str`. No drift.
- All public functions carry complete type hints (`blob_uri: str -> ExtractionResult`), satisfying the acceptance criterion.
- `prebuilt-read` model is used correctly — the string is passed directly as the first positional argument to `begin_analyze_document_from_url`, which is the correct call pattern.
- Table extraction handles `None` gracefully with `result.tables or []`, avoiding an `AttributeError` if the document contains no tables.
- The deviation was self-reported in the implementation report rather than hidden — that transparency is good practice, even though the deviation itself is blocking.
