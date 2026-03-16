---
name: azure-ai-contentunderstanding
description: >
  Build multimodal content extraction applications using the Azure AI Content Understanding Python SDK
  (azure-ai-contentunderstanding). Use this skill whenever working with ContentUnderstandingClient,
  extracting text or structure from documents (PDF, Office), analyzing images, transcribing audio,
  or processing video with the Content Understanding service. Also use for creating custom analyzers
  with ContentAnalyzer/ContentFieldSchema, using prebuilt analyzers (prebuilt-documentSearch,
  prebuilt-invoice, prebuilt-audioSearch, prebuilt-videoSearch, prebuilt-imageSearch), polling with
  begin_analyze/begin_analyze_binary, reading AnalysisResult/DocumentContent/AudioVisualContent,
  or extracting structured fields from content. Triggers: "azure-ai-contentunderstanding",
  "ContentUnderstandingClient", "multimodal analysis", "document extraction", "video analysis",
  "audio transcription", "content analyzer", "prebuilt analyzer", "AnalysisResult".
---

# Azure AI Content Understanding SDK for Python

Azure AI Content Understanding is a multimodal service that extracts semantic content from documents, images, audio, and video. It returns structured, machine-readable data suitable for RAG pipelines, intelligent document processing (IDP), and agentic workflows.

## Install

```bash
uv add azure-ai-contentunderstanding
uv add azure-identity  # for DefaultAzureCredential
uv add aiohttp         # only needed for async operations
```

**Env vars:**
- `CONTENTUNDERSTANDING_ENDPOINT` — your Microsoft Foundry resource endpoint (e.g. `https://<name>.services.ai.azure.com/`)
- `CONTENTUNDERSTANDING_KEY` — API key (optional; omit to use DefaultAzureCredential)

## Create the Client

```python
import os
from azure.ai.contentunderstanding import ContentUnderstandingClient
from azure.core.credentials import AzureKeyCredential
from azure.identity import DefaultAzureCredential

endpoint = os.environ["CONTENTUNDERSTANDING_ENDPOINT"]
key = os.getenv("CONTENTUNDERSTANDING_KEY")
credential = AzureKeyCredential(key) if key else DefaultAzureCredential()

client = ContentUnderstandingClient(endpoint=endpoint, credential=credential)
```

For async:
```python
from azure.ai.contentunderstanding.aio import ContentUnderstandingClient
from azure.identity.aio import DefaultAzureCredential
```

> Prefer `DefaultAzureCredential` in production. API key is fine for testing.

---

## Analyzing Content — Two Methods

| Input type | Method | Example |
|---|---|---|
| URL (public) | `begin_analyze(analyzer_id, inputs=[AnalysisInput(url=...)])` | document, audio, video, image URLs |
| Local file (bytes) | `begin_analyze_binary(analyzer_id, binary_input=bytes)` | PDF, MP3, MP4, PNG from disk |

Both methods return a **poller** — call `.result()` to wait for completion.

### Analyze a URL

```python
from azure.ai.contentunderstanding.models import AnalysisInput, AnalysisResult

poller = client.begin_analyze(
    analyzer_id="prebuilt-documentSearch",
    inputs=[AnalysisInput(url="https://example.com/report.pdf")],
)
result: AnalysisResult = poller.result()
print(result.contents[0].markdown)
```

### Analyze a Local File

```python
with open("invoice.pdf", "rb") as f:
    file_bytes = f.read()

poller = client.begin_analyze_binary(
    analyzer_id="prebuilt-documentSearch",
    binary_input=file_bytes,
)
result: AnalysisResult = poller.result()
```

---

## Result Types

`AnalysisResult.contents` is a list of `AnalysisContent` items. Cast to the appropriate subtype:

| Content type | Class | When used |
|---|---|---|
| Documents, PDFs, Office | `DocumentContent` | `prebuilt-documentSearch`, `prebuilt-invoice`, any document analyzer |
| Audio, Video | `AudioVisualContent` | `prebuilt-audioSearch`, `prebuilt-videoSearch` |
| Images | `DocumentContent` | `prebuilt-documentSearch` (images with text), `prebuilt-imageSearch` |

```python
from typing import cast
from azure.ai.contentunderstanding.models import DocumentContent, AudioVisualContent

# For documents / images with text
doc = cast(DocumentContent, result.contents[0])
print(doc.markdown)            # full extracted markdown
print(doc.start_page_number)   # first page
print(doc.end_page_number)     # last page
print(doc.unit)                # coordinate unit: "inch", "pixel", etc.

# For audio / video
av = cast(AudioVisualContent, result.contents[0])
print(av.markdown)             # transcript in markdown
print(av.start_time_ms)        # segment start (ms)
print(av.end_time_ms)          # segment end (ms)
print(av.width, av.height)     # video frame dimensions (video only)
```

> `prebuilt-videoSearch` may return **multiple segments** — iterate `result.contents`, not just `[0]`.

---

## Prebuilt Analyzers

### RAG analyzers (return markdown + Summary field)

| Analyzer ID | Best for |
|---|---|
| `prebuilt-documentSearch` | PDF, Office docs, images with text — layout, tables, figures, formulas |
| `prebuilt-imageSearch` | Standalone images — returns a description paragraph |
| `prebuilt-audioSearch` | Audio files — transcript with speaker diarization |
| `prebuilt-videoSearch` | Video files — frames, audio transcript, structured summaries |

### Domain-specific analyzers (return structured fields)

| Category | Analyzer IDs |
|---|---|
| Finance | `prebuilt-invoice`, `prebuilt-receipt`, `prebuilt-creditCard`, `prebuilt-bankStatement.us`, `prebuilt-check.us` |
| Identity | `prebuilt-idDocument`, `prebuilt-passport`, `prebuilt-driverLicense` |
| Mortgage | `prebuilt-mortgage1003`, `prebuilt-appraisalReport` |
| Procurement | `prebuilt-purchaseOrder`, `prebuilt-contractAgreement` |
| Utilities | `prebuilt-utilityStatement` |

**Required setup:** Before using prebuilt analyzers, you must deploy GPT-4.1, GPT-4.1-mini, and text-embedding-3-large in your Foundry resource and run `sample_update_defaults.py` to configure model mappings. This is a one-time setup per resource.

---

## Extracting Structured Fields

Domain-specific analyzers populate `content.fields` — a dict of `ContentField` items:

```python
from azure.ai.contentunderstanding.models import (
    AnalysisInput, AnalysisResult, DocumentContent,
    ContentField, ArrayField, ObjectField,
)
from typing import cast

poller = client.begin_analyze(
    analyzer_id="prebuilt-invoice",
    inputs=[AnalysisInput(url="https://example.com/invoice.pdf")],
)
result: AnalysisResult = poller.result()
doc = cast(DocumentContent, result.contents[0])

# Simple field
customer = doc.fields.get("CustomerName")
if customer:
    print(customer.value)        # extracted value
    print(customer.confidence)   # 0.0–1.0 (if available)
    print(customer.source)       # location in markdown

# Array field (line items)
items_field = doc.fields.get("Items")
if items_field and isinstance(items_field, ArrayField):
    for item in items_field.value_array or []:
        if isinstance(item, ObjectField):
            desc = item.value_object.get("Description")
            price = item.value_object.get("UnitPrice")
            if desc: print(f"  {desc.value}: {price.value if price else 'N/A'}")
```

---

## Document-Specific Properties

When using `DocumentContent` from `prebuilt-documentSearch`:

```python
doc = cast(DocumentContent, result.contents[0])

# Pages
for page in doc.pages or []:
    print(f"Page {page.page_number}: {page.width}x{page.height} {doc.unit}")

# Tables
for table in doc.tables or []:
    print(f"Table: {table.row_count} rows × {table.column_count} cols")

# Hyperlinks (requires EnableLayout)
for link in doc.hyperlinks or []:
    print(f"Link: {link.url} — {link.content}")

# Formulas in LaTeX (requires EnableFormula)
for page in doc.pages or []:
    for formula in page.formulas or []:
        print(f"Formula: {formula.value} (kind={formula.kind})")

# Figures / charts
for figure in doc.figures or []:
    print(f"Figure: {figure.description}")
```

---

## Audio/Video Properties

```python
av = cast(AudioVisualContent, result.contents[0])

# Summary (from RAG analyzers)
summary = av.fields.get("Summary") if av.fields else None
if summary:
    print(summary.value)

# Transcript phrases with timing + speaker
for phrase in av.transcript_phrases or []:
    print(f"[{phrase.start_time_ms}ms–{phrase.end_time_ms}ms] "
          f"Speaker {phrase.speaker_id}: {phrase.text}")
```

---

## Custom Analyzers

Create a custom analyzer when prebuilt analyzers don't match your domain. Custom analyzers define a **field schema** to extract exactly the data you need.

```python
import time
from azure.ai.contentunderstanding.models import (
    ContentAnalyzer, ContentAnalyzerConfig,
    ContentFieldSchema, ContentFieldDefinition,
    ContentFieldType, GenerationMethod,
)

analyzer_id = f"my_analyzer_{int(time.time())}"

field_schema = ContentFieldSchema(
    name="my_schema",
    description="Schema for contract extraction",
    fields={
        "party_name": ContentFieldDefinition(
            type=ContentFieldType.STRING,
            method=GenerationMethod.EXTRACT,        # literal extraction
            description="Name of the contracting party",
            estimate_source_and_confidence=True,    # required for EXTRACT
        ),
        "contract_summary": ContentFieldDefinition(
            type=ContentFieldType.STRING,
            method=GenerationMethod.GENERATE,       # AI-generated from content
            description="One-paragraph summary of the contract",
        ),
        "contract_type": ContentFieldDefinition(
            type=ContentFieldType.STRING,
            method=GenerationMethod.CLASSIFY,       # picks from enum
            description="Type of legal document",
            enum=["NDA", "employment", "service", "lease", "other"],
        ),
    },
)

analyzer = ContentAnalyzer(
    base_analyzer_id="prebuilt-document",   # base: prebuilt-document/audio/video/image
    description="Contract field extractor",
    config=ContentAnalyzerConfig(
        enable_ocr=True,
        enable_layout=True,
        estimate_field_source_and_confidence=True,
    ),
    field_schema=field_schema,
    models={
        "completion": "gpt-4.1",
        "embedding": "text-embedding-3-large",
    },
)

poller = client.begin_create_analyzer(analyzer_id=analyzer_id, resource=analyzer)
poller.result()  # wait for creation

# Use it
poller = client.begin_analyze_binary(analyzer_id=analyzer_id, binary_input=file_bytes)
result = poller.result()
```

**Field extraction methods:**
| Method | Use when |
|---|---|
| `GenerationMethod.EXTRACT` | Literal text present in the document (requires `estimate_source_and_confidence=True`) |
| `GenerationMethod.GENERATE` | Value requires interpretation or summarization |
| `GenerationMethod.CLASSIFY` | Value must match one of a fixed set of categories (use with `enum`) |

**Base analyzers for custom:**
- `prebuilt-document` — for document/PDF/Office content
- `prebuilt-audio` — for audio content
- `prebuilt-video` — for video content
- `prebuilt-image` — for image content

---

## Analyzer Management

```python
# List all custom analyzers
analyzers = client.list_analyzers()
for a in analyzers:
    print(a.analyzer_id, a.description)

# Get a specific analyzer
analyzer = client.get_analyzer(analyzer_id="my_analyzer_123")

# Delete an analyzer
client.delete_analyzer(analyzer_id="my_analyzer_123")
```

---

## Async Usage

```python
import asyncio
from azure.ai.contentunderstanding.aio import ContentUnderstandingClient
from azure.identity.aio import DefaultAzureCredential
from azure.ai.contentunderstanding.models import AnalysisInput

async def analyze():
    async with ContentUnderstandingClient(
        endpoint=os.environ["CONTENTUNDERSTANDING_ENDPOINT"],
        credential=DefaultAzureCredential(),
    ) as client:
        poller = await client.begin_analyze(
            analyzer_id="prebuilt-documentSearch",
            inputs=[AnalysisInput(url="https://example.com/doc.pdf")],
        )
        result = await poller.result()
        print(result.contents[0].markdown)

asyncio.run(analyze())
```

---

## Error Handling

```python
from azure.core.exceptions import HttpResponseError

try:
    poller = client.begin_analyze(
        analyzer_id="prebuilt-invoice",
        inputs=[AnalysisInput(url=doc_url)],
    )
    result = poller.result()
except HttpResponseError as e:
    print(f"Service error {e.status_code}: {e.message}")
    # Common: 404 if analyzer not found, 400 if input format unsupported
```

---

## Common Patterns

**Check if content has fields before accessing:**
```python
if doc.fields:
    val = doc.fields.get("InvoiceTotal")
    if val:
        print(val.value)
```

**Video segments — always iterate all contents:**
```python
for segment in result.contents:
    av = cast(AudioVisualContent, segment)
    print(f"[{av.start_time_ms}–{av.end_time_ms}ms]: {av.markdown[:100]}")
```

**Using prebuilt vs custom:**
- Use **prebuilt analyzers** for common document types — no setup beyond model deployment.
- Use **custom analyzers** when you need domain-specific fields, classifications, or non-standard document structures.
- Custom analyzers require models (`gpt-4.1` + `text-embedding-3-large`) specified in `ContentAnalyzer.models`.
