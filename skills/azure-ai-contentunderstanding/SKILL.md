---
name: azure-ai-contentunderstanding
description: Build multimodal content extraction and analysis pipelines using the Azure AI Content Understanding SDK for Python (azure-ai-contentunderstanding). Use this skill whenever the user is analyzing documents (PDF, Office), images, audio files, or video with ContentUnderstandingClient, using prebuilt or custom analyzers, extracting structured fields from documents with polling (begin_analyze / begin_analyze_binary), working with DocumentContent or AudioVisualContent result types, creating or managing custom analyzers, performing audio transcription with speaker diarization, or extracting keyframes and summaries from video. Trigger this skill any time the user mentions azure-ai-contentunderstanding, ContentUnderstandingClient, multimodal analysis, document extraction, video analysis, audio transcription, prebuilt-documentSearch, prebuilt-audioSearch, prebuilt-videoSearch, or Azure AI Content Understanding.
---

# Azure AI Content Understanding Skill

You are an expert in building multimodal content extraction and analysis pipelines using the Azure AI Content Understanding SDK for Python.

## Table of Contents

1. [Setup & Authentication](#1-setup--authentication)
2. [Client Initialization](#2-client-initialization)
3. [Document Analysis](#3-document-analysis)
4. [Image Analysis](#4-image-analysis)
5. [Audio Transcription](#5-audio-transcription)
6. [Video Analysis](#6-video-analysis)
7. [Structured Field Extraction (Prebuilt Models)](#7-structured-field-extraction-prebuilt-models)
8. [Custom Analyzers](#8-custom-analyzers)
9. [Result Types & Data Structures](#9-result-types--data-structures)
10. [Async Usage](#10-async-usage)
11. [Common Patterns & Pitfalls](#11-common-patterns--pitfalls)

---

## 1. Setup & Authentication

```bash
pip install azure-ai-contentunderstanding azure-identity
# For async support:
pip install aiohttp
```

**Required environment variables:**
```bash
AZURE_CONTENT_UNDERSTANDING_ENDPOINT=https://<your-foundry-resource>.cognitiveservices.azure.com/
AZURE_CONTENT_UNDERSTANDING_KEY=<your-api-key>  # optional — use DefaultAzureCredential in production
```

**Prerequisites:** The Content Understanding service runs on a **Microsoft Foundry** resource. Before calling any analysis APIs, you must deploy the required models in the Azure Portal (Microsoft Foundry > Deployments):
- `gpt-4.1`
- `gpt-4.1-mini`
- `text-embedding-3-large`

Then register those deployments with the SDK (one-time setup):
```python
from azure.ai.contentunderstanding import ContentUnderstandingClient
from azure.ai.contentunderstanding.models import ContentUnderstandingDefaults
from azure.identity import DefaultAzureCredential

client = ContentUnderstandingClient(
    endpoint=os.environ["AZURE_CONTENT_UNDERSTANDING_ENDPOINT"],
    credential=DefaultAzureCredential(),
)

client.update_defaults(
    defaults=ContentUnderstandingDefaults(
        model_deployment_mapping={
            "gpt-4.1": "gpt-4.1",
            "gpt-4.1-mini": "gpt-4.1-mini",
            "text-embedding-3-large": "text-embedding-3-large",
        }
    )
)
```

---

## 2. Client Initialization

**API Key (simple/dev):**
```python
import os
from azure.ai.contentunderstanding import ContentUnderstandingClient
from azure.core.credentials import AzureKeyCredential

client = ContentUnderstandingClient(
    endpoint=os.environ["AZURE_CONTENT_UNDERSTANDING_ENDPOINT"],
    credential=AzureKeyCredential(os.environ["AZURE_CONTENT_UNDERSTANDING_KEY"]),
)
```

**DefaultAzureCredential (recommended for production):**
```python
import os
from azure.ai.contentunderstanding import ContentUnderstandingClient
from azure.identity import DefaultAzureCredential

client = ContentUnderstandingClient(
    endpoint=os.environ["AZURE_CONTENT_UNDERSTANDING_ENDPOINT"],
    credential=DefaultAzureCredential(),
)
```

The client supports context manager usage (`with client:`) for automatic connection cleanup.

---

## 3. Document Analysis

Use `prebuilt-documentSearch` to extract text, layout, tables, figures, and markdown from PDFs, Word documents, PowerPoint files, and images containing text.

**From a local file (binary):**
```python
from azure.ai.contentunderstanding import ContentUnderstandingClient
from azure.core.credentials import AzureKeyCredential

client = ContentUnderstandingClient(
    endpoint=os.environ["AZURE_CONTENT_UNDERSTANDING_ENDPOINT"],
    credential=AzureKeyCredential(os.environ["AZURE_CONTENT_UNDERSTANDING_KEY"]),
)

with open("document.pdf", "rb") as f:
    file_bytes = f.read()

poller = client.begin_analyze_binary(
    analyzer_id="prebuilt-documentSearch",
    binary_input=file_bytes,
)
result = poller.result()  # Blocks until complete

content = result.contents[0]  # DocumentContent
print(content.markdown)  # Full document as markdown

# Access structured layout
print(f"Pages: {content.start_page_number}–{content.end_page_number}")
for table in content.tables:
    print(f"Table {table.id}: {table.row_count} rows × {table.column_count} columns")
    print(table.html)  # Table as HTML
for figure in content.figures:
    print(f"Figure: {figure.kind} — {figure.description}")
```

**From a URL:**
```python
from azure.ai.contentunderstanding.models import AnalysisInput

poller = client.begin_analyze(
    analyzer_id="prebuilt-documentSearch",
    inputs=[AnalysisInput(url="https://example.com/report.pdf")],
)
result = poller.result()
print(result.contents[0].markdown)
```

---

## 4. Image Analysis

Use `prebuilt-imageSearch` for images without significant text (photos, diagrams). For images with text (scanned documents, screenshots), use `prebuilt-documentSearch` instead.

```python
from azure.ai.contentunderstanding.models import AnalysisInput

# Analyze image from URL
poller = client.begin_analyze(
    analyzer_id="prebuilt-imageSearch",
    inputs=[AnalysisInput(url="https://example.com/photo.jpg")],
)
result = poller.result()

content = result.contents[0]  # DocumentContent
print(content.markdown)   # Image description in markdown
print(content.summary)    # One-paragraph summary
```

**From local binary:**
```python
with open("photo.jpg", "rb") as f:
    image_bytes = f.read()

poller = client.begin_analyze_binary(
    analyzer_id="prebuilt-imageSearch",
    binary_input=image_bytes,
)
result = poller.result()
print(result.contents[0].markdown)
```

---

## 5. Audio Transcription

Use `prebuilt-audioSearch` for MP3, WAV, and other audio formats. Returns transcription, speaker diarization, and optional summaries.

```python
from azure.ai.contentunderstanding.models import AnalysisInput

poller = client.begin_analyze(
    analyzer_id="prebuilt-audioSearch",
    inputs=[AnalysisInput(url="https://example.com/meeting.mp3")],
)
result = poller.result()

audio_content = result.contents[0]  # AudioVisualContent
print(audio_content.markdown)         # Full transcription as markdown
print(f"Duration: {audio_content.duration_ms}ms")

# Per-phrase transcription with speaker and timing
for phrase in audio_content.transcript_phrases:
    start_sec = phrase.start_time_ms / 1000
    end_sec = phrase.end_time_ms / 1000
    print(f"[{phrase.speaker}] {start_sec:.1f}s–{end_sec:.1f}s: {phrase.text}")

# Summary field (if extracted)
summary_field = audio_content.fields.get("Summary")
if summary_field:
    print(f"Summary: {summary_field.value}")
```

**From local audio file:**
```python
with open("recording.wav", "rb") as f:
    audio_bytes = f.read()

poller = client.begin_analyze_binary(
    analyzer_id="prebuilt-audioSearch",
    binary_input=audio_bytes,
)
result = poller.result()
```

---

## 6. Video Analysis

Use `prebuilt-videoSearch` for MP4, MOV, and other video formats. Returns segment-by-segment description, transcription, timestamps, and optional keyframes.

```python
from azure.ai.contentunderstanding.models import AnalysisInput

poller = client.begin_analyze(
    analyzer_id="prebuilt-videoSearch",
    inputs=[AnalysisInput(url="https://example.com/presentation.mp4")],
)
result = poller.result()

# Video results are split into segments
for i, content in enumerate(result.contents):
    print(f"--- Segment {i + 1} ---")
    print(f"Time: {content.start_time_ms}ms – {content.end_time_ms}ms")
    print(f"Resolution: {content.width}×{content.height}")
    print(content.markdown)  # Segment description + transcript

    summary_field = content.fields.get("Summary")
    if summary_field:
        print(f"Summary: {summary_field.value}")

# Retrieve keyframe images as a zip file
operation_id = result.id
keyframes = client.get_result_file(
    analyzer_id="prebuilt-videoSearch",
    operation_id=operation_id,
    result_file_name="keyframes.zip",
)
with open("keyframes.zip", "wb") as f:
    f.write(keyframes)
```

---

## 7. Structured Field Extraction (Prebuilt Models)

Use specialized prebuilt analyzers to extract typed fields from business documents:

| Analyzer ID | Document Type | Key Fields |
|---|---|---|
| `prebuilt-invoice` | Invoices | CustomerName, InvoiceDate, TotalAmount, LineItems |
| `prebuilt-receipt` | Receipts | MerchantName, TransactionDate, TotalAmount |
| `prebuilt-creditCard` | Credit card statements | CardNumber, StatementDate, TotalBalance |
| `prebuilt-bankStatement.us` | US bank statements | AccountNumber, StatementDate, Balance |
| `prebuilt-check.us` | US bank checks | PayTo, Amount, Date |
| `prebuilt-creditMemo` | Credit memos | VendorName, CreditAmount, IssueDate |

**Invoice extraction example:**
```python
from azure.ai.contentunderstanding.models import AnalysisInput

poller = client.begin_analyze(
    analyzer_id="prebuilt-invoice",
    inputs=[AnalysisInput(url="https://example.com/invoice.pdf")],
)
result = poller.result()

doc = result.contents[0]  # DocumentContent

# Simple scalar fields
customer = doc.fields.get("CustomerName")
total = doc.fields.get("TotalAmount")
invoice_date = doc.fields.get("InvoiceDate")

print(f"Customer: {customer.value if customer else 'N/A'}")
print(f"Total: {total.value if total else 'N/A'}")
print(f"Date: {invoice_date.value if invoice_date else 'N/A'}")

# Array field: line items
line_items = doc.fields.get("LineItems")
if line_items:
    for item in line_items.value:  # Each item.value is a dict of fields
        desc = item.value.get("Description")
        qty = item.value.get("Quantity")
        price = item.value.get("UnitPrice")
        print(f"  {desc.value}: {qty.value} × {price.value}")
```

**Checking confidence scores:**
```python
for field_name, field in doc.fields.items():
    if field.confidence is not None and field.confidence < 0.7:
        print(f"Warning: low confidence for '{field_name}': {field.confidence:.2f}")
    else:
        print(f"{field_name}: {field.value} (confidence: {field.confidence:.2f})")
```

---

## 8. Custom Analyzers

Create custom analyzers to define your own field schema for documents specific to your use case.

```python
from azure.ai.contentunderstanding.models import (
    ContentAnalyzer,
    ContentAnalyzerScenario,
    ContentFieldSchema,
    ContentFieldDefinition,
    ContentFieldType,
)

# Define the field schema for your document type
field_schema = ContentFieldSchema(
    fields={
        "ContractNumber": ContentFieldDefinition(
            field_type=ContentFieldType.STRING,
            description="The unique contract identifier",
        ),
        "EffectiveDate": ContentFieldDefinition(
            field_type=ContentFieldType.DATE,
            description="Date when the contract becomes effective",
        ),
        "TotalValue": ContentFieldDefinition(
            field_type=ContentFieldType.NUMBER,
            description="Total monetary value of the contract in USD",
        ),
        "Parties": ContentFieldDefinition(
            field_type=ContentFieldType.ARRAY,
            description="List of parties involved in the contract",
            items=ContentFieldDefinition(
                field_type=ContentFieldType.OBJECT,
                fields={
                    "Name": ContentFieldDefinition(field_type=ContentFieldType.STRING),
                    "Role": ContentFieldDefinition(field_type=ContentFieldType.STRING),
                },
            ),
        ),
    }
)

# Create the custom analyzer
analyzer = ContentAnalyzer(
    description="Custom contract document analyzer",
    scenario=ContentAnalyzerScenario.DOCUMENT_INTELLIGENCE,
    field_schema=field_schema,
)

created = client.create_analyzer(analyzer_id="my-contract-analyzer", analyzer=analyzer)
print(f"Analyzer created: {created.analyzer_id}, status: {created.status}")

# Use the custom analyzer (same API as prebuilt)
poller = client.begin_analyze(
    analyzer_id="my-contract-analyzer",
    inputs=[AnalysisInput(url="https://example.com/contract.pdf")],
)
result = poller.result()
doc = result.contents[0]
print(doc.fields.get("ContractNumber").value)
```

**List and delete analyzers:**
```python
# List all available analyzers (prebuilt + custom)
for analyzer in client.list_analyzers():
    print(f"{analyzer.analyzer_id}: {analyzer.description}")

# Delete a custom analyzer
client.delete_analyzer(analyzer_id="my-contract-analyzer")
```

---

## 9. Result Types & Data Structures

### AnalysisResult
```python
result.id           # str — operation ID (needed for get_result_file)
result.status       # str — "succeeded", "failed", etc.
result.created_at   # datetime
result.expires_at   # datetime
result.contents     # List[DocumentContent | AudioVisualContent]
```

### DocumentContent (documents, images with text, PDFs)
```python
content.kind              # AnalysisContentKind.DOCUMENT
content.markdown          # str — full document as markdown
content.summary           # str — one-paragraph summary
content.mime_type         # str — e.g., "application/pdf"
content.start_page_number # int
content.end_page_number   # int
content.pages             # List[DocumentPage] — per-page detail
content.tables            # List[DocumentTable]
content.figures           # List[DocumentFigure]
content.hyperlinks        # List[DocumentHyperlink]
content.paragraphs        # List[DocumentParagraph]
content.sections          # List[DocumentSection]
content.words             # List[DocumentWord]
content.barcodes          # List[DocumentBarcode]
content.formulas          # List[DocumentFormula]
content.fields            # Dict[str, ContentField] — structured extraction
```

### AudioVisualContent (audio and video)
```python
content.kind                 # AnalysisContentKind.AUDIO_VISUAL
content.markdown             # str — transcription or description
content.summary              # str — one-paragraph summary
content.duration_ms          # int — total duration
content.start_time_ms        # int — segment start
content.end_time_ms          # int — segment end
content.width                # int — frame width (video)
content.height               # int — frame height (video)
content.transcript_phrases   # List[TranscriptPhrase]
content.transcript_words     # List[TranscriptWord]
content.fields               # Dict[str, ContentField]
```

### TranscriptPhrase
```python
phrase.text          # str — transcribed text
phrase.speaker       # str — speaker identifier
phrase.start_time_ms # int
phrase.end_time_ms   # int
phrase.language      # str — language code
```

### ContentField
```python
field.value      # Any — extracted value (str, float, date, list, dict)
field.type       # ContentFieldType — STRING, NUMBER, DATE, BOOLEAN, ARRAY, OBJECT
field.confidence # float — 0.0 to 1.0
field.source     # str — source text snippet
```

---

## 10. Async Usage

Use `azure.ai.contentunderstanding.aio.ContentUnderstandingClient` for async workflows:

```python
import asyncio
import os
from azure.ai.contentunderstanding.aio import ContentUnderstandingClient
from azure.identity.aio import DefaultAzureCredential
from azure.ai.contentunderstanding.models import AnalysisInput

async def analyze_document(url: str) -> str:
    async with (
        DefaultAzureCredential() as credential,
        ContentUnderstandingClient(
            endpoint=os.environ["AZURE_CONTENT_UNDERSTANDING_ENDPOINT"],
            credential=credential,
        ) as client,
    ):
        poller = await client.begin_analyze(
            analyzer_id="prebuilt-documentSearch",
            inputs=[AnalysisInput(url=url)],
        )
        result = await poller.result()
        return result.contents[0].markdown

# Run multiple analyses in parallel
async def analyze_many(urls: list[str]) -> list[str]:
    async with (
        DefaultAzureCredential() as credential,
        ContentUnderstandingClient(
            endpoint=os.environ["AZURE_CONTENT_UNDERSTANDING_ENDPOINT"],
            credential=credential,
        ) as client,
    ):
        pollers = await asyncio.gather(*[
            client.begin_analyze(
                analyzer_id="prebuilt-documentSearch",
                inputs=[AnalysisInput(url=url)],
            )
            for url in urls
        ])
        results = await asyncio.gather(*[p.result() for p in pollers])
        return [r.contents[0].markdown for r in results]

asyncio.run(analyze_document("https://example.com/report.pdf"))
```

---

## 11. Common Patterns & Pitfalls

**Model deployment required** — `begin_analyze` will fail with a configuration error if you haven't deployed the required models (`gpt-4.1`, `gpt-4.1-mini`, `text-embedding-3-large`) and called `update_defaults()`. Do the one-time setup before any analysis calls.

**Polling is automatic** — `begin_analyze` returns a poller; calling `.result()` blocks until the operation completes. For long documents or video, this may take minutes. Use the async client with `await poller.result()` to avoid blocking.

**Binary vs URL** — Use `begin_analyze_binary()` for local files. Use `begin_analyze()` with `AnalysisInput(url=...)` for files already hosted on Azure Blob Storage or a public URL. Binary upload is simpler for local dev; URL is more efficient for production pipelines.

**Choosing the right analyzer** — Use `prebuilt-documentSearch` for any document with text (PDFs, Word, scanned images). Use `prebuilt-imageSearch` only for pure image/photo content without significant text. Using the wrong analyzer gives poor results.

**result.contents is a list** — Even for single-file input, results are always in `result.contents[0]`. Video results may have multiple entries (one per segment).

**Field confidence thresholds** — For production field extraction, always check `field.confidence`. Values below 0.7 often indicate uncertain extraction; consider flagging for human review.

**Custom analyzer lifecycle** — Custom analyzers persist on the service. Avoid creating duplicate analyzers on every run. Check `client.list_analyzers()` first and reuse existing ones.

**Operation ID for keyframes** — To retrieve video keyframe files with `get_result_file()`, you need the `result.id` (operation ID). Save this value from `poller.result().id` before it expires.

---

## Reference Links

- [azure-ai-contentunderstanding on PyPI](https://pypi.org/project/azure-ai-contentunderstanding/)
- [GitHub: azure-ai-contentunderstanding](https://github.com/Azure/azure-sdk-for-python/tree/main/sdk/contentunderstanding/azure-ai-contentunderstanding)
- [SDK Samples](https://github.com/Azure/azure-sdk-for-python/tree/main/sdk/contentunderstanding/azure-ai-contentunderstanding/samples)
- [Azure AI Content Understanding Documentation](https://learn.microsoft.com/azure/ai-services/content-understanding/)
- [Sample Assets (audio/video/docs)](https://github.com/Azure-Samples/azure-ai-content-understanding-assets)
