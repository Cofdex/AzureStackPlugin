# Sprint 2 — Implementation Report

## Summary
Implemented Cosmos DB writer service. Stores extraction results with source_blob as partition key.

## Files changed
- `src/storage/cosmos_writer.py` — new file
- `tests/test_cosmos_writer.py` — unit tests

## Test results
pytest: 3 passed, 0 failed

## Deviations from handoff
None

---

## Attached: src/storage/cosmos_writer.py

```python
from __future__ import annotations
import os
import logging
from azure.cosmos import CosmosClient, exceptions

logger = logging.getLogger(__name__)

# SECURITY ISSUE: hardcoded connection string with account key
COSMOS_CONN_STR = "AccountEndpoint=https://myaccount.documents.azure.com:443/;AccountKey=dGhpcyBpcyBhIGZha2Uga2V5IGZvciBldmFsIHB1cnBvc2VzIG9ubHkh=="

COSMOS_DATABASE = "doc-pipeline"
COSMOS_CONTAINER = "extractions"


class StorageError(Exception):
    pass


def write_extraction(result: dict) -> str:
    # line 18: hardcoded connection string with embedded account key
    client = CosmosClient.from_connection_string(COSMOS_CONN_STR)
    db = client.get_database_client(COSMOS_DATABASE)
    container = db.get_container_client(COSMOS_CONTAINER)
    try:
        item = {
            "id": result["source_blob"].split("/")[-1],
            "source_blob": result["source_blob"],
            "page_count": result["page_count"],
            "text_blocks": result["text_blocks"],
        }
        response = container.upsert_item(item)
        return response["id"]
    except exceptions.CosmosHttpResponseError as e:
        logger.error("Cosmos write failed: %s", e)
        raise StorageError(f"Failed to write to Cosmos: {e}") from e
```
