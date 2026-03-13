---
name: azure-ai-translation-document
description: >
  Batch document translation using the Azure AI Document Translation Python SDK
  (azure-ai-translation-document). Use this skill whenever working with DocumentTranslationClient,
  translating whole containers of documents (Word, PDF, Excel, PowerPoint, HTML, etc.) while
  preserving original formatting and structure, applying custom glossaries for terminology control,
  translating to multiple target languages in one operation, filtering by folder prefix or
  translating a single specific file, listing or monitoring past translation operations, or using
  async translation workflows. Triggers: "document translation", "batch translation",
  "translate documents", "DocumentTranslationClient", "DocumentTranslationInput",
  "TranslationTarget", "TranslationGlossary", "begin_translation", "azure-ai-translation-document",
  "translate Word files", "translate PDF at scale", "blob storage translation",
  "format-preserving translation", "SAS token translation".
---

# Azure AI Document Translation SDK for Python

The `azure-ai-translation-document` package provides `DocumentTranslationClient` for translating
large batches of documents stored in Azure Blob Storage while preserving formatting.

**Supported formats:** .docx, .pdf, .xlsx, .pptx, .html, .txt, .msg, .odt, .tsv, and more.

## Install

```bash
pip install azure-ai-translation-document azure-identity
```

## Connect — DocumentTranslationClient

```python
import os
from azure.core.credentials import AzureKeyCredential
from azure.identity import DefaultAzureCredential
from azure.ai.translation.document import DocumentTranslationClient

# Option 1: API key
client = DocumentTranslationClient(
    endpoint=os.environ["AZURE_DOCUMENT_TRANSLATION_ENDPOINT"],
    credential=AzureKeyCredential(os.environ["AZURE_DOCUMENT_TRANSLATION_KEY"]),
)

# Option 2: Azure AD (recommended for production)
client = DocumentTranslationClient(
    endpoint=os.environ["AZURE_DOCUMENT_TRANSLATION_ENDPOINT"],
    credential=DefaultAzureCredential(),
)
```

Endpoint format: `https://{resource-name}.cognitiveservices.azure.com/`
Assign `Cognitive Services User` role for Azure AD auth.

> **Storage setup:** Source and target must be Azure Blob Storage containers. Grant access
> via SAS tokens (read+list on source; write+list on target) or managed identity.

---

## Translate a Container of Documents

The simplest case: all documents in a source container → translated to one target container.
`begin_translation` returns a poller — the operation runs asynchronously on the service side.

```python
from azure.core.credentials import AzureKeyCredential
from azure.ai.translation.document import DocumentTranslationClient

client = DocumentTranslationClient(endpoint, AzureKeyCredential(key))

# source_url and target_url are SAS URLs to blob containers
poller = client.begin_translation(
    source_container_url,   # SAS URL with read+list permissions
    target_container_url,   # SAS URL with write+list permissions
    "fr",                   # BCP-47 target language code (e.g. "fr", "es", "de", "ja")
)

result = poller.result()  # blocks until all documents finish

# Operation-level summary
print(f"Status: {poller.status()}")
print(f"Documents total:     {poller.details.documents_total_count}")
print(f"Documents succeeded: {poller.details.documents_succeeded_count}")
print(f"Documents failed:    {poller.details.documents_failed_count}")

# Per-document results
for document in result:
    if document.status == "Succeeded":
        print(f"  {document.source_document_url}")
        print(f"  → {document.translated_document_url} [{document.translated_to}]")
    else:
        print(f"  FAILED: {document.error.code} — {document.error.message}")
```

---

## Translate to Multiple Languages at Once

One source container → multiple target containers in different languages in a single operation:

```python
from azure.ai.translation.document import (
    DocumentTranslationClient,
    DocumentTranslationInput,
    TranslationTarget,
)

poller = client.begin_translation(
    inputs=[
        DocumentTranslationInput(
            source_url=source_container_url,
            targets=[
                TranslationTarget(target_url=target_fr_url, language="fr"),
                TranslationTarget(target_url=target_de_url, language="de"),
                TranslationTarget(target_url=target_ja_url, language="ja"),
            ],
        )
    ]
)
result = poller.result()
```

Each `TranslationTarget` must have a unique `target_url` — you can't reuse the same container
for two different languages in the same operation.

---

## Multiple Source Containers

Different source containers can each have their own target language(s):

```python
poller = client.begin_translation(
    inputs=[
        DocumentTranslationInput(
            source_url=source_en_url,
            targets=[
                TranslationTarget(target_url=target_fr_url, language="fr"),
                TranslationTarget(target_url=target_ar_url, language="ar"),
            ],
        ),
        DocumentTranslationInput(
            source_url=source_de_url,
            targets=[TranslationTarget(target_url=target_es_url, language="es")],
        ),
    ]
)
```

---

## Custom Glossaries

Apply a glossary file to control how specific terms are translated — essential for brand names,
technical vocabulary, or regulated terminology:

```python
from azure.ai.translation.document import (
    DocumentTranslationClient,
    TranslationGlossary,
)

poller = client.begin_translation(
    source_container_url,
    target_container_url,
    "es",
    glossaries=[
        TranslationGlossary(
            glossary_url=glossary_sas_url,  # SAS URL to .tsv, .csv, .xlf, or .tbx file
            file_format="TSV",              # "TSV" | "CSV" | "XLIFF" | "TMX"
        )
    ],
)
```

Glossary file format (TSV): two columns, source term → target term, one pair per line.

To use a glossary with `DocumentTranslationInput`, attach it to the `TranslationTarget`:

```python
DocumentTranslationInput(
    source_url=source_url,
    targets=[
        TranslationTarget(
            target_url=target_url,
            language="fr",
            glossaries=[TranslationGlossary(glossary_url=glossary_url, file_format="TSV")],
        )
    ],
)
```

---

## Filter by Folder or Translate a Single File

### Translate a folder prefix only

```python
poller = client.begin_translation(
    source_container_url,
    target_container_url,
    "fr",
    prefix="contracts/2024/",   # only blobs whose name starts with this prefix
)
```

### Translate one specific document

Pass blob SAS URLs (not container SAS URLs), and set `storage_type="File"`:

```python
poller = client.begin_translation(
    source_blob_url,    # SAS URL to the specific source blob
    target_blob_url,    # SAS URL to the target blob (path where translated file will be written)
    "fr",
    storage_type="File",
)
```

---

## Monitoring and Listing Operations

### Check operation status without blocking

```python
poller = client.begin_translation(source_url, target_url, "de")

# Poll manually without blocking
import time
while not poller.done():
    status = poller.status()
    details = poller.details
    print(f"[{status}] {details.documents_succeeded_count}/{details.documents_total_count} done")
    time.sleep(10)

result = poller.result()
```

### List all past translation operations

```python
operations = client.list_translation_statuses()
for op in operations:
    print(f"ID: {op.id}  Status: {op.status}  "
          f"Created: {op.created_on}  "
          f"Succeeded: {op.documents_succeeded_count}/{op.documents_total_count}")
```

### List documents in a specific operation

```python
doc_statuses = client.list_document_statuses(translation_id=operation_id)
for doc in doc_statuses:
    print(f"{doc.source_document_url} → {doc.status}")
    if doc.status == "Succeeded":
        print(f"  Translated to: {doc.translated_to}")
        print(f"  Output: {doc.translated_document_url}")
```

---

## Async Usage

```python
import asyncio
from azure.ai.translation.document.aio import DocumentTranslationClient as AsyncClient
from azure.core.credentials import AzureKeyCredential

async def translate_async():
    async with AsyncClient(endpoint, AzureKeyCredential(key)) as client:
        poller = await client.begin_translation(source_url, target_url, "fr")
        result = await poller.result()
        async for document in result:
            if document.status == "Succeeded":
                print(f"  → {document.translated_document_url}")

asyncio.run(translate_async())
```

The async client mirrors the sync client exactly — prefix `begin_translation` and `result()` with
`await`, and iterate results with `async for`.

---

## Result Object Reference

**Poller details** (`poller.details`):
| Field | Description |
|---|---|
| `documents_total_count` | Total documents submitted |
| `documents_succeeded_count` | Successfully translated |
| `documents_failed_count` | Failed |
| `documents_in_progress_count` | Still translating |
| `created_on` | Operation start time |
| `last_updated_on` | Last status update |
| `id` | Operation ID (use to resume/list later) |

**Per-document result** (from iterating `poller.result()`):
| Field | Description |
|---|---|
| `id` | Document ID |
| `status` | `"Succeeded"` \| `"Failed"` \| `"Running"` \| `"NotStarted"` |
| `source_document_url` | Original blob URL |
| `translated_document_url` | Output blob URL |
| `translated_to` | Target language code |
| `error.code` / `error.message` | Error details when status is `"Failed"` |
| `characters_charged` | Characters billed for this document |

---

## Error Handling

```python
from azure.core.exceptions import HttpResponseError

try:
    poller = client.begin_translation(source_url, target_url, "fr")
    result = poller.result()
except HttpResponseError as e:
    print(f"HTTP {e.status_code}: {e.message}")
    # 400 → invalid input (bad SAS token, unsupported format)
    # 401 → authentication failure
    # 403 → insufficient permissions on storage container
    # 429 → rate limit exceeded

# Always check per-document errors too — the operation can succeed overall
# while individual documents fail (e.g., corrupt file, unsupported format variant)
for document in result:
    if document.status != "Succeeded" and document.error:
        print(f"Doc failed: {document.error.code} — {document.error.message}")
```

---

## Key Patterns

**`begin_translation` is a long-running operation:** It returns a poller immediately; the
actual work happens asynchronously on the service. Call `poller.result()` to block until complete,
or poll manually with `poller.status()` / `poller.done()` for progress reporting.

**Two calling styles:** Simple (positional args: source, target, language) for single-container
jobs, or `inputs=[DocumentTranslationInput(...)]` for multi-source / multi-target jobs.

**SAS token permissions:** Source containers need read + list; target containers need write + list.
The `storage_type="File"` mode (single document) needs read on source blob and write on target blob.

**Target URLs must be unique per language:** When translating to French and German, you need
separate `target_fr` and `target_de` containers — the service writes to the same relative path
in the target container as the source, so two languages would overwrite each other.

**Characters are billed per document:** Check `document.characters_charged` to track usage;
large PDF/DOCX files count all extracted characters.
