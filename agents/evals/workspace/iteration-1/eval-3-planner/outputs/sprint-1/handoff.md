## Sprint 1 — Extraction Service

## Goal
Implement `src/extraction/extractor.py` — a self-contained Python module that accepts a blob URI, calls Azure AI Document Intelligence (`prebuilt-read` model), and returns a structured dict; ship full unit test coverage with mocked SDK calls.

## Tasks
- [ ] Task 1: Create `src/extraction/__init__.py` (empty, marks as package).
- [ ] Task 2: Create `src/extraction/extractor.py` with a `DocumentExtractor` class.
  - Constructor: `__init__(self, endpoint: str, credential: TokenCredential)` — accepts injected `DefaultAzureCredential` (do NOT instantiate credential inside the class).
  - Method: `extract(self, blob_uri: str) -> dict` — calls `DocumentIntelligenceClient.begin_analyze_document("prebuilt-read", ...)`, awaits the poller, and returns:
    ```python
    {
        "page_count": int,
        "text_blocks": list[str],   # one entry per paragraph/line block
        "tables": list[dict],       # raw table cell data as dicts
        "metadata": {
            "source_blob": str,     # the blob_uri argument
            "model_id": "prebuilt-read",
        },
    }
    ```
  - All type hints required on every function signature.
  - No API keys or connection strings anywhere in the file.
- [ ] Task 3: Create `tests/extraction/__init__.py` (empty).
- [ ] Task 4: Create `tests/extraction/test_extractor.py`.
  - Use `unittest.mock.patch` (or `pytest-mock`) to mock `DocumentIntelligenceClient`.
  - Cover: happy-path extraction returns correct dict shape; `page_count` matches mocked page count; `metadata.source_blob` equals the input URI; SDK client is constructed with the injected credential (not a key).
  - All tests must pass without real Azure credentials.
- [ ] Task 5: Add/update `pyproject.toml` (preferred) or `requirements.txt` with:
  ```
  azure-ai-document-intelligence>=1.0.0
  azure-identity>=1.15.0
  ```
  If using `uv`, run `uv add azure-ai-document-intelligence azure-identity` to lock the versions.

## Acceptance criteria
- [ ] `DocumentExtractor.extract(blob_uri)` returns a dict with exactly these top-level keys: `page_count`, `text_blocks`, `tables`, `metadata`.
- [ ] `metadata` contains `source_blob` (equals input URI) and `model_id` (`"prebuilt-read"`).
- [ ] The class constructor accepts a `credential` parameter; `DefaultAzureCredential` is never instantiated inside the module.
- [ ] All unit tests pass (`uv run pytest tests/extraction/` exits 0).
- [ ] No secrets, API keys, or hard-coded connection strings appear anywhere in `src/` or `tests/`.
- [ ] All public function signatures carry full type hints.

## Relevant context
- Architecture section: `agents/evals/fixtures/eval-3-planner/architecture.md#2-extraction-service-srcextractionextractorpy`
- SDK skills to load: `azure-document-intelligence`, `azure-identity`
- Depends on: nothing — this is sprint-1, no prior sprint required

## Files expected to change
- `src/extraction/__init__.py` — new file, marks extraction as a Python package
- `src/extraction/extractor.py` — new file, core extraction service
- `tests/extraction/__init__.py` — new file, marks test package
- `tests/extraction/test_extractor.py` — new file, unit tests with mocked SDK
- `pyproject.toml` (or `requirements.txt`) — add `azure-ai-document-intelligence>=1.0.0` and `azure-identity>=1.15.0`

## TDD required: YES

## Notes
- **Auth constraint (hard)**: All Azure SDK clients must receive a `DefaultAzureCredential` instance injected at construction time — never created inside the service class. This is an architecture-level decision; do not deviate.
- **Model choice (ADR `use-prebuilt-read`)**: Use `"prebuilt-read"` only. Do not use a custom model or a different prebuilt model variant.
- **No Azure Function in this sprint**: The extraction service is a plain Python class. The Azure Function trigger is sprint-3 scope — do not add any `azure-functions` imports or decorators here.
- **Package manager**: Use `uv` exclusively — no `pip install` or `python -m venv`.
- **SDK client import path** (as of `azure-ai-document-intelligence>=1.0.0`): `from azure.ai.documentintelligence import DocumentIntelligenceClient` (the namespace changed from `azure.ai.formrecognizer` in older versions — use the new one).
- Sprint-2 (Cosmos writer) will import `DocumentExtractor` directly, so keep the public interface stable: constructor signature and `extract()` return shape must not change after this sprint commits.
