## Sprint 3 — Azure Blob Upload Function

## Goal
Implement `src/ingestion/uploader.py` that accepts a file path and uploads it to Azure Blob Storage container `raw-uploads`.

## Tasks
- [ ] Task 1: Create `upload_document(file_path: str, container: str = "raw-uploads") -> str` function that returns the blob URL
- [ ] Task 2: Use `BlobServiceClient` from `azure-storage-blob`
- [ ] Task 3: Use `DefaultAzureCredential` for auth
- [ ] Task 4: Handle file-not-found and upload errors gracefully

## Acceptance criteria
- [ ] Returns the full blob URL on success
- [ ] Raises `UploadError` with a descriptive message on failure
- [ ] Uses `DefaultAzureCredential` — no connection strings or API keys
- [ ] Type hints on all public functions

## Relevant context
- SDK skills to load: `azure-blob-storage`, `azure-identity`
- Storage account name comes from env var `AZURE_STORAGE_ACCOUNT`

## Files expected to change
- `src/ingestion/uploader.py` — new file
- `tests/test_uploader.py` — new file

## TDD required: YES

## Notes
- Blob name = filename extracted from the path
- If blob already exists, overwrite it (`overwrite=True`)
