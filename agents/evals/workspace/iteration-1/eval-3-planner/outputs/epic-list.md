# Epic List: feature-blob-ingestion-pipeline-001

## Tool selection
- sequential-thinking: NO — only 3 sprints with linear dependencies; threshold for activation is ≥4 sprints with cross-sprint dependencies
- find-azure-skills: YES — `## External dependencies` in architecture.md lists four Azure SDK packages: `azure-ai-document-intelligence`, `azure-cosmos`, `azure-identity`, `azure-functions`. Queried `find-azure-skills` agent for each; results populated in each sprint's `SDK skills to load:` line.

---

## Epic 1: Document Extraction and Storage Layer

**Goal**: Build the core ingestion business logic — a Python extraction service that calls Azure AI Document Intelligence and a Cosmos DB writer that persists structured results. No Azure Function yet; all components are importable Python modules with full unit/integration test coverage.

**Sprints**: sprint-1, sprint-2

---

## Epic 2: Azure Function Orchestration and Blob Trigger

**Goal**: Wire the extraction and storage layer into a production-ready Azure Function with a Blob Storage trigger that automatically processes every `.pdf` file uploaded to the `raw-uploads` container. Deliver end-to-end integration proof.

**Sprints**: sprint-3

---

## Ordering constraints
- sprint-2 depends on sprint-1 (committed): `cosmos_writer.py` calls `DocumentExtractor` — the extractor module must exist and be tested before the writer can be integrated or integration-tested
- sprint-3 depends on sprint-2 (committed): the Azure Function imports both `extractor.py` and `cosmos_writer.py`; both must be stable before wiring the trigger
