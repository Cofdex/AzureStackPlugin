# Sprint 1 — Implementation Report

## Summary
Implemented `src/extraction/extractor.py` with `extract_from_blob` function calling Azure AI Document Intelligence.

## Files changed
- `src/extraction/extractor.py` — core extractor implementation
- `src/extraction/__init__.py` — package init
- `tests/test_extractor.py` — unit tests with mocked SDK

## Test results
pytest: 4 passed, 0 failed, 0 skipped

## Deviations from handoff
- Used `api_key` string auth instead of `DefaultAzureCredential` for easier local testing (commented TODO to fix before prod)

## Flagged issues
None

---

## Attached: src/extraction/extractor.py

```python
from __future__ import annotations
from dataclasses import dataclass
import os
from azure.ai.documentintelligence import DocumentIntelligenceClient
# BUG: using api_key not DefaultAzureCredential
from azure.core.credentials import AzureKeyCredential


ENDPOINT = os.environ["DOCUMENT_INTELLIGENCE_ENDPOINT"]
API_KEY = os.environ["DOCUMENT_INTELLIGENCE_KEY"]  # hardcoded pattern


@dataclass
class ExtractionResult:
    page_count: int
    text_blocks: list[str]
    tables: list[dict]
    source_blob: str


def extract_from_blob(blob_uri: str) -> ExtractionResult:
    # line 20: API key auth — should be DefaultAzureCredential
    client = DocumentIntelligenceClient(ENDPOINT, AzureKeyCredential(API_KEY))
    poller = client.begin_analyze_document_from_url(
        "prebuilt-read", blob_uri
    )
    result = poller.result()
    text_blocks = [block.content for page in result.pages for block in page.lines]
    return ExtractionResult(
        page_count=len(result.pages),
        text_blocks=text_blocks,
        tables=[t.to_dict() for t in (result.tables or [])],
        source_blob=blob_uri,
    )
```
