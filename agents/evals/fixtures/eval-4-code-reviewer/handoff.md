## Sprint 1 — Extraction Service

## Goal
Implement `src/extraction/extractor.py` that accepts a blob URI, calls Azure AI Document Intelligence with the `prebuilt-read` model, and returns a structured result dict.

## Tasks
- [ ] Task 1: Create `src/extraction/extractor.py` with `extract_from_blob(blob_uri: str) -> ExtractionResult` function
- [ ] Task 2: Use `DocumentAnalysisClient` from `azure-ai-document-intelligence`
- [ ] Task 3: Authenticate with `DefaultAzureCredential` — not API key

## Acceptance criteria
- [ ] `extract_from_blob` accepts a blob URI string and returns `ExtractionResult` dataclass
- [ ] Uses `prebuilt-read` model
- [ ] All functions have type hints
- [ ] Unit tests cover: success path, empty document, service unavailable (mock SDK)

## Relevant context
- Architecture section: architecture.md#2-extraction-service
- SDK skills to load: `azure-ai-document-intelligence`, `azure-identity`
- Depends on: nothing (first sprint)

## Files expected to change
- `src/extraction/extractor.py` — new file
- `src/extraction/__init__.py` — new file
- `tests/test_extractor.py` — new file

## TDD required: YES

## Notes
- `DocumentAnalysisClient` endpoint comes from env var `DOCUMENT_INTELLIGENCE_ENDPOINT`
- Return dataclass fields: `page_count: int`, `text_blocks: list[str]`, `tables: list[dict]`, `source_blob: str`
