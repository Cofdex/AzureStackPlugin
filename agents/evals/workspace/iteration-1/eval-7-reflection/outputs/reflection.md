# Reflection — feature-blob-upload-001 sprint 3

## Sprint summary
Sprint 3 delivered `src/ingestion/uploader.py`, a Blob upload service using `DefaultAzureCredential` with module-level client instantiation, typed custom exceptions, and full test coverage (4/4 tests passing). Both code review and security review returned PASS with no blocking findings.

## Patterns observed

### Coding patterns confirmed
- `DefaultAzureCredential` instantiated once at module level, passed to `BlobServiceClient(account_url=..., credential=...)` — confirmed across handoff (sprints 1–3), implementation-report, review-report, and security-report
- Module-level `BlobServiceClient` singleton — avoids per-request auth overhead; confirmed as correct pattern in both review-report (positive note) and handoff
- Custom exception classes (`UploadError`, `StorageError`) wrapping SDK exceptions — clean error boundary; noted in handoff and praised in review-report

### Anti-patterns caught
- **Pattern**: Using `AzureKeyCredential` or raw connection strings instead of `DefaultAzureCredential`
  - **Caught in**: review-report sprint-1 (referenced in handoff sprint-3 as recurring awareness)
  - **Correct approach**: Always use `DefaultAzureCredential` from `azure-identity`; never use raw connection strings or key credentials in production code paths

- **Pattern**: Missing `try/except` around SDK I/O calls
  - **Caught in**: review-report sprint-2 (referenced in handoff sprint-3 as recurring awareness)
  - **Correct approach**: Wrap every SDK call that performs network I/O in a `try/except` block with typed, domain-specific exceptions

### Technical decisions recorded

- **Decision**: `DefaultAzureCredential` is the sole authentication strategy for all Azure services in this project — no fallback to `AzureKeyCredential` or connection strings
  - **Rationale**: Consistent managed-identity support, no secrets in code, aligns with MCSB guidance (confirmed by security-report)
  - **Sprint**: 3
  - **ADR written to**: `docs/workflows/feature-blob-upload-001/adr/azure-credential-strategy.md`
  - **Promotion candidate**: Pattern has appeared across sprints 1–3; if confirmed in a second distinct workflow ID, promote to `docs/learning/adr/azure-credential-strategy.md`

- **Decision**: Module-level singleton clients preferred over per-request instantiation for Azure SDK clients
  - **Rationale**: Avoids repeated credential resolution and connection overhead; endorsed by code reviewer
  - **Sprint**: 3
  - **ADR written to**: `docs/workflows/feature-blob-upload-001/adr/module-level-sdk-clients.md`

## Context for next sprints
- The `uploader.py` module interface (`upload_blob(file_path, container_name) -> str`) is now stable — callers in subsequent sprints should not change the signature without a new handoff
- `azure-storage-blob==12.19.0` was pinned this sprint and verified CVE-free; do not upgrade without re-running security checklist
- The one open MINOR finding (missing module docstring in `uploader.py` line 1) was not blocking but is unresolved; the next sprint touching this file should add it

## Memory written
- [pattern] `DefaultAzureCredential` instantiated at module level, not per-request — confirmed sprints 1–3 (feature-blob-upload-001)
- [pattern] Module-level SDK client singleton (BlobServiceClient) avoids per-request auth/connection overhead — confirmed sprint-3 review
- [pattern] Custom exception classes (`UploadError`, `StorageError`) wrap SDK exceptions at module boundary — confirmed sprint-3
- [mistake] `AzureKeyCredential` or raw connection strings used instead of `DefaultAzureCredential` — caught sprint-1 review; always use `DefaultAzureCredential` in production
- [mistake] Missing `try/except` around SDK network I/O calls — caught sprint-2 review; every SDK I/O call must be wrapped with typed exception handling

## No learnings: false
