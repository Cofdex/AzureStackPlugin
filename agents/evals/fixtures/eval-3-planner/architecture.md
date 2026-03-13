# Architecture: feature-blob-ingestion-pipeline-001

## Goal
Build a document ingestion pipeline that reads PDF files uploaded to Azure Blob Storage, extracts text using Azure AI Document Intelligence, and stores the results in Azure Cosmos DB for later querying.

## Components

### 1. Blob Trigger
- Azure Function (Python, HTTP trigger for now, Blob trigger in sprint-3)
- Watches container `raw-uploads` for new `.pdf` files
- Passes blob URI to the extraction service

### 2. Extraction Service (`src/extraction/extractor.py`)
- Uses `azure-ai-document-intelligence` SDK
- Model: `prebuilt-read`
- Returns structured dict: `{page_count, text_blocks, tables, metadata}`

### 3. Storage Service (`src/storage/cosmos_writer.py`)
- Uses `azure-cosmos` SDK, NoSQL API
- Database: `doc-pipeline`, Container: `extractions`
- Partition key: `/source_blob`

### 4. Auth
- All services use `DefaultAzureCredential`
- No API keys in code

## External dependencies
- `azure-ai-document-intelligence>=1.0.0`
- `azure-cosmos>=4.7.0`
- `azure-identity>=1.15.0`
- `azure-functions>=1.18.0`

## Constraints for Planner
- Sprint 1: extraction service + unit tests (no Azure Function yet)
- Sprint 2: Cosmos writer + integration test
- Sprint 3: Azure Function + blob trigger
- Sprint 1 must be complete and committed before Sprint 2 starts
- All Azure SDK calls must use `DefaultAzureCredential`

## ADR index
| Slug | Decision |
|---|---|
| use-prebuilt-read | Use prebuilt-read model over custom model — sufficient for generic PDFs, cheaper |
| cosmos-nosql-over-sql | Cosmos NoSQL chosen over SQL API — partition key on source_blob gives natural distribution |
