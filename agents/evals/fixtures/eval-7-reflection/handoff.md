## Sprint 3 — Handoff

## Goal
Implement Blob upload service as described in the handoff.

## Sprint summary
This sprint delivered a clean `uploader.py` using DefaultAzureCredential, with proper error handling.

## Patterns observed

### Coding patterns confirmed
- `DefaultAzureCredential` used for all Azure service auth — consistent across sprints 1–3
- Module-level client instantiation for `BlobServiceClient` — avoids recreating per request
- Custom exception classes (`UploadError`, `StorageError`) wrapping SDK exceptions — clean error boundary

### Anti-patterns caught
- Pattern: Using `AzureKeyCredential` or raw connection strings instead of `DefaultAzureCredential`
  - Caught in: review-report sprint-1
  - Correct approach: `DefaultAzureCredential` from `azure-identity` in all production code paths

- Pattern: Missing `try/except` around SDK I/O calls
  - Caught in: review-report sprint-2 (MINOR note)
  - Correct approach: Wrap every SDK call that does network I/O in try/except with appropriate typed exception

### Technical decisions made
- Using `DefaultAzureCredential` as the single auth strategy for all Azure services in this project
- Module-level singleton clients preferred over per-request instantiation

## No learnings: false
