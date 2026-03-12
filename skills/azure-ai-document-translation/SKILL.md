---
name: azure-ai-document-translation
description: Batch translation of documents with format preservation using the Azure AI Document Translation SDK for Python (azure-ai-translation-document). Use this skill whenever the user is translating Word documents, PDFs, Excel spreadsheets, PowerPoint presentations, HTML, or other document formats at scale while preserving formatting and layout. Trigger this skill any time the user mentions document translation, batch translation, translate documents, DocumentTranslationClient, azure-ai-translation-document, translating files, document localization, translating Word/PDF/Excel/PowerPoint files, or large-scale document translation pipelines.
---

# Azure AI Document Translation Skill

You are an expert in translating documents at scale using the Azure AI Document Translation SDK for Python (`azure-ai-translation-document`). This skill covers batch translation jobs, single-document translation, glossary integration, and progress monitoring.

## Table of Contents

1. [Setup & Authentication](#1-setup--authentication)
2. [Client Initialization](#2-client-initialization)
3. [Batch Translation (Multiple Documents)](#3-batch-translation-multiple-documents)
4. [Single Document Translation (Synchronous)](#4-single-document-translation-synchronous)
5. [Translation with Glossary](#5-translation-with-glossary)
6. [Monitoring Translation Jobs](#6-monitoring-translation-jobs)
7. [Listing & Managing Jobs](#7-listing--managing-jobs)
8. [Supported Formats & Languages](#8-supported-formats--languages)
9. [Common Patterns & Pitfalls](#9-common-patterns--pitfalls)

---

## 1. Setup & Authentication

```bash
pip install azure-ai-translation-document azure-identity azure-storage-blob
```

**Required environment variables:**
```bash
AZURE_DOCUMENT_TRANSLATION_ENDPOINT=https://<your-resource>.cognitiveservices.azure.com/
AZURE_DOCUMENT_TRANSLATION_KEY=<your-api-key>     # optional — use DefaultAzureCredential in production
AZURE_STORAGE_SOURCE_URL=https://<account>.blob.core.windows.net/<source-container>
AZURE_STORAGE_TARGET_URL=https://<account>.blob.core.windows.net/<target-container>
```

**Prerequisites:**
- Create an **Azure AI Translator** resource (or Azure AI services multi-service resource).
- Create an **Azure Blob Storage** account with separate containers for source and translated documents.
- Generate SAS tokens or use managed identity for storage access.

**Storage SAS token requirements:**
- **Source container:** Read + List permissions
- **Target container:** Write + List permissions (+ Delete to overwrite existing files)

---

## 2. Client Initialization

**API Key (dev/testing):**
```python
import os
from azure.ai.translation.document import DocumentTranslationClient
from azure.core.credentials import AzureKeyCredential

client = DocumentTranslationClient(
    endpoint=os.environ["AZURE_DOCUMENT_TRANSLATION_ENDPOINT"],
    credential=AzureKeyCredential(os.environ["AZURE_DOCUMENT_TRANSLATION_KEY"]),
)
```

**DefaultAzureCredential (recommended for production):**
```python
import os
from azure.ai.translation.document import DocumentTranslationClient
from azure.identity import DefaultAzureCredential

client = DocumentTranslationClient(
    endpoint=os.environ["AZURE_DOCUMENT_TRANSLATION_ENDPOINT"],
    credential=DefaultAzureCredential(),
)
```

---

## 3. Batch Translation (Multiple Documents)

Translate all documents in a source blob container to one or more target containers. The job runs asynchronously; the SDK polls until completion.

```python
import os
from azure.ai.translation.document import DocumentTranslationClient, TranslationTarget
from azure.core.credentials import AzureKeyCredential

client = DocumentTranslationClient(
    endpoint=os.environ["AZURE_DOCUMENT_TRANSLATION_ENDPOINT"],
    credential=AzureKeyCredential(os.environ["AZURE_DOCUMENT_TRANSLATION_KEY"]),
)

# Source container URL with SAS token (Read + List)
source_url = os.environ["AZURE_STORAGE_SOURCE_URL"]  # e.g., https://account.blob.core.windows.net/source?sas-token

# Translate to multiple languages simultaneously
targets = [
    TranslationTarget(
        target_url="https://account.blob.core.windows.net/translated-fr?sas-token",
        language="fr",
    ),
    TranslationTarget(
        target_url="https://account.blob.core.windows.net/translated-de?sas-token",
        language="de",
    ),
]

# begin_translation returns a poller — blocks until the job finishes
poller = client.begin_translation(source_url, targets[0].target_url, targets[0].language)
result = poller.result()

print(f"Status: {poller.status()}")
for document in result:
    print(f"Document: {document.source_document_url}")
    print(f"  Status: {document.status}")
    if document.error:
        print(f"  Error: {document.error.code} — {document.error.message}")
    else:
        print(f"  Translated to: {document.translated_to}")
        print(f"  Output: {document.translated_document_url}")
```

**Translate to multiple targets in a single job** using `begin_translation` with inputs:
```python
from azure.ai.translation.document import DocumentTranslationInput, TranslationTarget

inputs = [
    DocumentTranslationInput(
        source_url=source_url,
        targets=[
            TranslationTarget(target_url="https://.../fr-container?sas", language="fr"),
            TranslationTarget(target_url="https://.../de-container?sas", language="de"),
            TranslationTarget(target_url="https://.../ja-container?sas", language="ja"),
        ],
    )
]

poller = client.begin_translation(inputs)
result = poller.result()
```

A single job can target up to **10 languages** simultaneously.

---

## 4. Single Document Translation (Synchronous)

For translating one document at a time without blob storage, use `SingleDocumentTranslationClient`. This is synchronous and returns the translated bytes directly — no storage setup required.

```python
import os
from azure.ai.translation.document import SingleDocumentTranslationClient
from azure.ai.translation.document.models import DocumentTranslateContent
from azure.core.credentials import AzureKeyCredential

client = SingleDocumentTranslationClient(
    endpoint=os.environ["AZURE_DOCUMENT_TRANSLATION_ENDPOINT"],
    credential=AzureKeyCredential(os.environ["AZURE_DOCUMENT_TRANSLATION_KEY"]),
)

# Read source file
with open("report.docx", "rb") as f:
    document_content = f.read()

# Translate from English to Spanish
response = client.document_translate(
    target_language="es",
    body=DocumentTranslateContent(
        document=("report.docx", document_content, "application/vnd.openxmlformats-officedocument.wordprocessingml.document"),
    ),
)

# Write translated document
with open("report_es.docx", "wb") as f:
    f.write(response)

print("Translation complete: report_es.docx")
```

**MIME types for common formats:**

| Format | MIME Type |
|---|---|
| .docx (Word) | `application/vnd.openxmlformats-officedocument.wordprocessingml.document` |
| .pptx (PowerPoint) | `application/vnd.openxmlformats-officedocument.presentationml.presentation` |
| .xlsx (Excel) | `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet` |
| .pdf | `application/pdf` |
| .html / .htm | `text/html` |
| .txt | `text/plain` |
| .tsv | `text/tab-separated-values` |

---

## 5. Translation with Glossary

Apply a custom glossary (term list) to ensure specific terms are translated consistently or left untranslated. The glossary is a TSV or XLIFF file stored in blob storage.

```python
from azure.ai.translation.document import (
    DocumentTranslationInput, TranslationTarget, TranslationGlossary
)

# Glossary file format (TSV example):
# SourceTerm\tTargetTerm
# Azure Blob Storage\tStockage Blob Azure
# Contoso\tContoso   <- preserve brand names

glossary = TranslationGlossary(
    glossary_url="https://account.blob.core.windows.net/glossaries/en-fr.tsv?sas-token",
    file_format="TSV",
)

inputs = [
    DocumentTranslationInput(
        source_url=source_url,
        targets=[
            TranslationTarget(
                target_url="https://.../fr-output?sas",
                language="fr",
                glossaries=[glossary],
            )
        ],
    )
]

poller = client.begin_translation(inputs)
result = poller.result()
```

**Glossary file formats:** `TSV` (tab-separated, simplest), `XLIFF` (XML-based, richer metadata), `CSV`.

**TSV glossary structure:**
```
SourceTerm\tTargetTerm\tDescription (optional)
machine learning\tapprentissage automatique\tML term
Azure\tAzure\tBrand name — do not translate
```

---

## 6. Monitoring Translation Jobs

For long-running jobs, use the poller's callbacks instead of blocking on `.result()`.

```python
import time

poller = client.begin_translation(inputs)

# Non-blocking: check status periodically
while not poller.done():
    status = poller.status()
    print(f"Job status: {status}")
    time.sleep(5)

# After completion, iterate results
for doc in poller.result():
    if doc.status == "Succeeded":
        print(f"✓ {doc.source_document_url} → {doc.translated_to}")
    else:
        print(f"✗ {doc.source_document_url}: {doc.error.message}")
```

**Job metadata:**
```python
details = poller.details
print(f"Job ID: {details.id}")
print(f"Created: {details.created_on}")
print(f"Documents: {details.documents_total_count} total, "
      f"{details.documents_succeeded_count} succeeded, "
      f"{details.documents_failed_count} failed")
```

---

## 7. Listing & Managing Jobs

```python
# List all translation jobs (most recent first)
for job in client.list_translation_statuses():
    print(f"Job {job.id}: {job.status} — {job.documents_succeeded_count}/{job.documents_total_count} succeeded")

# Get a specific job by ID
job = client.get_translation_status(translation_id="<job-id>")

# Cancel a running job (documents already translated remain in the target container)
client.cancel_translation(translation_id="<job-id>")

# List documents within a job
for doc in client.list_document_statuses(translation_id="<job-id>"):
    print(f"  {doc.source_document_url}: {doc.status}")

# Get a specific document's status
doc = client.get_document_status(translation_id="<job-id>", document_id="<doc-id>")
```

---

## 8. Supported Formats & Languages

**Query supported document formats at runtime:**
```python
formats = client.get_supported_document_formats()
for fmt in formats:
    print(f"{fmt.file_format}: {fmt.file_extensions}")

# Also query supported glossary formats:
glossary_formats = client.get_supported_glossary_formats()
```

**Key supported document formats include:** DOCX, PPTX, XLSX, PDF (for translation), HTML, Markdown, plain text, TSV, and more (50+ formats total).

**Query supported language pairs:**
```python
# Use the Text Translation SDK for language support queries
# Document Translation supports the same language set as the Translator API
```

Common target languages: `fr` (French), `de` (German), `es` (Spanish), `it` (Italian), `pt` (Portuguese), `ja` (Japanese), `zh-Hans` (Simplified Chinese), `ar` (Arabic), `ru` (Russian), `ko` (Korean).

---

## 9. Common Patterns & Pitfalls

**SAS tokens expire** — Generate SAS tokens with sufficient expiry for your job. Large batches can take hours; a 24-hour SAS token is usually safe for batch jobs.

**PDF translation** — PDF-to-translated-PDF is supported, but the output quality depends on the PDF structure (text-selectable PDFs work; scanned/image PDFs do not). For scanned PDFs, run OCR first (Azure AI Document Intelligence).

**Target container must be empty (or separable)** — Translated files are written with the same filename as the source. If the target container already has files with the same names, they will be overwritten. Use separate containers per language to avoid collisions.

**Source URL must include SAS** — Managed identity access to blob storage for Document Translation requires configuring the Translator resource's managed identity on the storage account. SAS tokens are simpler for development.

**Single document vs. batch** — Use `SingleDocumentTranslationClient` when you have one file and don't want to set up blob storage. Use `DocumentTranslationClient` for batch jobs of 10+ documents.

**Glossary case sensitivity** — Glossary matching is case-sensitive by default. Include both capitalized and lowercase forms if needed.

**Preserve source formatting** — The service preserves formatting (fonts, tables, images, layout) automatically. You don't need to do anything special — just use the correct MIME type.

**Error handling:**
```python
from azure.core.exceptions import HttpResponseError

try:
    poller = client.begin_translation(source_url, target_url, "fr")
    result = poller.result()
except HttpResponseError as e:
    print(f"Service error {e.error.code}: {e.error.message}")
```

Per-document errors (e.g., unsupported format) don't fail the whole job — check each document's `status` and `error` after the job completes.

---

## Reference Links

- [azure-ai-translation-document on PyPI](https://pypi.org/project/azure-ai-translation-document/)
- [GitHub: azure-ai-translation-document](https://github.com/Azure/azure-sdk-for-python/tree/main/sdk/translation/azure-ai-translation-document)
- [SDK Samples](https://github.com/Azure/azure-sdk-for-python/tree/main/sdk/translation/azure-ai-translation-document/samples)
- [Document Translation Documentation](https://learn.microsoft.com/azure/ai-services/translator/document-translation/overview)
- [Supported Document Formats](https://learn.microsoft.com/azure/ai-services/translator/document-translation/overview#supported-document-formats)
- [Supported Languages](https://learn.microsoft.com/azure/ai-services/translator/language-support)
