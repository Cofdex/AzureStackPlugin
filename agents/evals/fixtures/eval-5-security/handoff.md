## Sprint 2 — Cosmos Writer

## Goal
Implement `src/storage/cosmos_writer.py` that persists `ExtractionResult` objects to Cosmos DB.

## Tasks
- [ ] Task 1: Create `src/storage/cosmos_writer.py` with `write_extraction(result: ExtractionResult) -> str` function
- [ ] Task 2: Use `CosmosClient` from `azure-cosmos`
- [ ] Task 3: Authenticate with `DefaultAzureCredential`

## Acceptance criteria
- [ ] `write_extraction` returns the Cosmos item ID
- [ ] Uses `DefaultAzureCredential` — not connection string or key
- [ ] Error handling: raises `StorageError` on Cosmos failures

## Relevant context
- SDK skills to load: `azure-cosmos`, `azure-identity`

## Files expected to change
- `src/storage/cosmos_writer.py`
- `tests/test_cosmos_writer.py`

## TDD required: YES
