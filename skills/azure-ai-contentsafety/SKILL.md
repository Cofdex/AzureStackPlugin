---
name: azure-ai-contentsafety
description: Detect and moderate harmful content in text and images using the Azure AI Content Safety SDK for Python (azure-ai-contentsafety). Use this skill whenever the user is analyzing text or images for harmful content, implementing content moderation pipelines, working with ContentSafetyClient or BlocklistClient, interpreting severity scores across hate/violence/sexual/self-harm categories, managing custom text blocklists, configuring four-level vs eight-level severity output, or building safety guardrails for AI applications. Trigger this skill any time the user mentions azure-ai-contentsafety, ContentSafetyClient, content moderation, harmful content detection, text analysis for safety, image moderation, blocklist management, or Azure AI Content Safety.
---

# Azure AI Content Safety Skill

You are an expert in building content moderation and safety detection pipelines using the Azure AI Content Safety SDK for Python.

## Table of Contents

1. [Setup & Authentication](#1-setup--authentication)
2. [Client Initialization](#2-client-initialization)
3. [Text Analysis](#3-text-analysis)
4. [Image Analysis](#4-image-analysis)
5. [Severity Levels & Categories](#5-severity-levels--categories)
6. [Blocklist Management](#6-blocklist-management)
7. [Using Blocklists with Text Analysis](#7-using-blocklists-with-text-analysis)
8. [Eight-Level Severity Mode](#8-eight-level-severity-mode)
9. [Common Patterns & Pitfalls](#9-common-patterns--pitfalls)

---

## 1. Setup & Authentication

```bash
pip install azure-ai-contentsafety azure-identity
```

**Required environment variables:**
```bash
CONTENT_SAFETY_ENDPOINT=https://<your-resource>.cognitiveservices.azure.com/
CONTENT_SAFETY_KEY=<your-api-key>  # optional — use DefaultAzureCredential in production
```

Create an Azure AI Content Safety resource in the Azure Portal (resource type: **Azure AI services** or standalone **Content Safety**). The resource provides the endpoint and API key.

---

## 2. Client Initialization

Two client classes are available:
- **`ContentSafetyClient`** — analyze text and images for harmful content
- **`BlocklistClient`** — create and manage custom text blocklists

**API Key (simple/dev):**
```python
import os
from azure.ai.contentsafety import ContentSafetyClient, BlocklistClient
from azure.core.credentials import AzureKeyCredential

endpoint = os.environ["CONTENT_SAFETY_ENDPOINT"]
credential = AzureKeyCredential(os.environ["CONTENT_SAFETY_KEY"])

safety_client = ContentSafetyClient(endpoint, credential)
blocklist_client = BlocklistClient(endpoint, credential)
```

**DefaultAzureCredential (recommended for production):**
```python
import os
from azure.ai.contentsafety import ContentSafetyClient, BlocklistClient
from azure.identity import DefaultAzureCredential

endpoint = os.environ["CONTENT_SAFETY_ENDPOINT"]
credential = DefaultAzureCredential()

safety_client = ContentSafetyClient(endpoint, credential)
blocklist_client = BlocklistClient(endpoint, credential)
```

---

## 3. Text Analysis

Analyze text for harmful content across four categories. Returns severity scores for each.

```python
import os
from azure.ai.contentsafety import ContentSafetyClient
from azure.ai.contentsafety.models import AnalyzeTextOptions, TextCategory
from azure.core.credentials import AzureKeyCredential
from azure.core.exceptions import HttpResponseError

client = ContentSafetyClient(
    os.environ["CONTENT_SAFETY_ENDPOINT"],
    AzureKeyCredential(os.environ["CONTENT_SAFETY_KEY"]),
)

request = AnalyzeTextOptions(text="Your text to analyze here")

try:
    response = client.analyze_text(request)

    for category_result in response.categories_analysis:
        print(f"{category_result.category}: severity {category_result.severity}")

    # Access specific categories
    hate = next(r for r in response.categories_analysis if r.category == TextCategory.HATE)
    violence = next(r for r in response.categories_analysis if r.category == TextCategory.VIOLENCE)
    sexual = next(r for r in response.categories_analysis if r.category == TextCategory.SEXUAL)
    self_harm = next(r for r in response.categories_analysis if r.category == TextCategory.SELF_HARM)

    print(f"Hate: {hate.severity}")
    print(f"Violence: {violence.severity}")
    print(f"Sexual: {sexual.severity}")
    print(f"Self-harm: {self_harm.severity}")

except HttpResponseError as e:
    print(f"Error {e.error.code}: {e.error.message}")
```

**Analyze only specific categories** (faster, lower cost):
```python
request = AnalyzeTextOptions(
    text="Your text here",
    categories=[TextCategory.HATE, TextCategory.VIOLENCE],  # skip sexual and self-harm
)
response = client.analyze_text(request)
```

**Text limits:** Maximum 10,000 Unicode characters per request.

---

## 4. Image Analysis

Analyze images for harmful visual content. Accepts image bytes or an Azure Blob Storage URL.

**From a local file:**
```python
import os
from azure.ai.contentsafety import ContentSafetyClient
from azure.ai.contentsafety.models import AnalyzeImageOptions, ImageData, ImageCategory
from azure.core.credentials import AzureKeyCredential
from azure.core.exceptions import HttpResponseError

client = ContentSafetyClient(
    os.environ["CONTENT_SAFETY_ENDPOINT"],
    AzureKeyCredential(os.environ["CONTENT_SAFETY_KEY"]),
)

with open("image.jpg", "rb") as f:
    image_bytes = f.read()

request = AnalyzeImageOptions(image=ImageData(content=image_bytes))

try:
    response = client.analyze_image(request)

    for category_result in response.categories_analysis:
        print(f"{category_result.category}: severity {category_result.severity}")

except HttpResponseError as e:
    print(f"Error {e.error.code}: {e.error.message}")
```

**From an Azure Blob URL:**
```python
request = AnalyzeImageOptions(
    image=ImageData(blob_url="https://mystorage.blob.core.windows.net/images/photo.jpg")
)
response = client.analyze_image(request)
```

**Analyze only specific image categories:**
```python
request = AnalyzeImageOptions(
    image=ImageData(content=image_bytes),
    categories=[ImageCategory.SEXUAL, ImageCategory.VIOLENCE],
)
```

**Image constraints:**
- Max size: 2048 × 2048 pixels, 4 MB
- Min size: 50 × 50 pixels
- Supported formats: JPEG, PNG, GIF, BMP, TIFF, WEBP
- Image severity uses 4 levels only (0, 2, 4, 6) — no 8-level mode

---

## 5. Severity Levels & Categories

### Categories

| Category | Covers |
|---|---|
| **Hate** | Discriminatory/pejorative language based on race, ethnicity, nationality, gender, sexual orientation, religion, disability, body appearance |
| **Violence** | Physical harm, weapons, injury, death, gore |
| **Sexual** | Anatomical content, erotic acts, sexual violence, pornography |
| **SelfHarm** | Self-injury, suicide methods, eating disorders |

Content can be multi-labeled (e.g., the same text can be flagged for both Hate and Violence simultaneously).

### Default: Four Severity Levels (0, 2, 4, 6)

| Score | Meaning |
|---|---|
| **0** | Safe — no harmful content detected |
| **2** | Low — mild or implicit harmful content |
| **4** | Medium — moderately explicit harmful content |
| **6** | High — strongly explicit or dangerous content |

### Recommended action thresholds

```python
def get_action(severity: int) -> str:
    if severity == 0:
        return "allow"
    elif severity == 2:
        return "review"   # manual review recommended
    elif severity >= 4:
        return "block"    # automatic block
    return "allow"

for result in response.categories_analysis:
    action = get_action(result.severity)
    print(f"{result.category}: severity={result.severity} → {action}")
```

---

## 6. Blocklist Management

Custom blocklists let you define domain-specific terms that should be flagged in addition to the built-in model.

### Create a blocklist and add items

```python
import os
from azure.ai.contentsafety import BlocklistClient
from azure.ai.contentsafety.models import (
    TextBlocklist,
    TextBlocklistItem,
    AddOrUpdateTextBlocklistItemsOptions,
)
from azure.core.credentials import AzureKeyCredential

client = BlocklistClient(
    os.environ["CONTENT_SAFETY_ENDPOINT"],
    AzureKeyCredential(os.environ["CONTENT_SAFETY_KEY"]),
)

# Create (or update) a blocklist
blocklist_name = "my-custom-blocklist"
client.create_or_update_text_blocklist(
    blocklist_name=blocklist_name,
    options=TextBlocklist(
        blocklist_name=blocklist_name,
        description="Terms specific to my application",
    ),
)

# Add terms to the blocklist
result = client.add_or_update_blocklist_items(
    blocklist_name=blocklist_name,
    options=AddOrUpdateTextBlocklistItemsOptions(
        blocklist_items=[
            TextBlocklistItem(text="forbidden_term_1"),
            TextBlocklistItem(text="forbidden_term_2", description="Competitor brand name"),
        ]
    ),
)

for item in result.blocklist_items:
    print(f"Added: {item.blocklist_item_id} — {item.text}")
```

### List, get, and delete items

```python
# List all blocklists
for bl in client.list_text_blocklists():
    print(f"Blocklist: {bl.blocklist_name} — {bl.description}")

# List items in a blocklist
for item in client.list_text_blocklist_items(blocklist_name=blocklist_name):
    print(f"  {item.blocklist_item_id}: {item.text}")

# Get a specific item
item = client.get_text_blocklist_item(
    blocklist_name=blocklist_name,
    blocklist_item_id="<item-id>",
)

# Remove specific items
from azure.ai.contentsafety.models import RemoveTextBlocklistItemsOptions
client.remove_blocklist_items(
    blocklist_name=blocklist_name,
    options=RemoveTextBlocklistItemsOptions(blocklist_item_ids=["<item-id>"]),
)

# Delete entire blocklist
client.delete_text_blocklist(blocklist_name=blocklist_name)
```

---

## 7. Using Blocklists with Text Analysis

Pass blocklist names to `AnalyzeTextOptions` to check text against your custom terms alongside the built-in model.

```python
from azure.ai.contentsafety import ContentSafetyClient
from azure.ai.contentsafety.models import AnalyzeTextOptions
from azure.core.credentials import AzureKeyCredential

safety_client = ContentSafetyClient(
    os.environ["CONTENT_SAFETY_ENDPOINT"],
    AzureKeyCredential(os.environ["CONTENT_SAFETY_KEY"]),
)

request = AnalyzeTextOptions(
    text="This text might contain forbidden terms.",
    blocklist_names=["my-custom-blocklist"],    # apply one or more blocklists
    halt_on_blocklist_hit=False,               # True = stop analysis on first match
)
response = safety_client.analyze_text(request)

# Check severity from the built-in model
for cat in response.categories_analysis:
    print(f"{cat.category}: {cat.severity}")

# Check blocklist matches
if response.blocklists_match:
    for match in response.blocklists_match:
        print(
            f"Blocklist match: '{match.blocklist_item_text}' "
            f"from blocklist '{match.blocklist_name}' "
            f"(item ID: {match.blocklist_item_id})"
        )
else:
    print("No blocklist matches.")
```

**`halt_on_blocklist_hit=True`** — stops processing and returns immediately on the first blocklist match, skipping the ML model. Use when blocklist hits should unconditionally block content.

---

## 8. Eight-Level Severity Mode

By default, text analysis returns 4 levels (0, 2, 4, 6). Enable 8-level output (0–7) for finer granularity:

```python
from azure.ai.contentsafety.models import AnalyzeTextOptions, AnalyzeTextOutputType

request = AnalyzeTextOptions(
    text="Your text here",
    output_type=AnalyzeTextOutputType.EIGHT_SEVERITY_LEVELS,
)
response = client.analyze_text(request)

for result in response.categories_analysis:
    print(f"{result.category}: {result.severity}")  # 0–7 range
```

**Note:** Eight-level severity is only available for text analysis. Image analysis always returns 4 levels (0, 2, 4, 6).

---

## 9. Common Patterns & Pitfalls

**Error handling** — Always wrap calls in `try/except HttpResponseError`. Common error codes:

```python
from azure.core.exceptions import HttpResponseError

try:
    response = client.analyze_text(AnalyzeTextOptions(text=text))
except HttpResponseError as e:
    if e.error.code == "InvalidRequestBody":
        print("Request format issue")
    elif e.error.code == "TooManyRequests":
        print("Rate limit — add retry logic")
    elif e.error.code == "ServerBusy":
        print("Temporary — retry with backoff")
    else:
        print(f"Error {e.error.code}: {e.error.message}")
```

**Text length limit** — `analyze_text` accepts at most 10,000 Unicode characters. For longer content, split into chunks and aggregate the maximum severity across chunks:

```python
def analyze_long_text(client, text: str, chunk_size: int = 9000) -> dict:
    chunks = [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]
    max_severities = {}
    for chunk in chunks:
        response = client.analyze_text(AnalyzeTextOptions(text=chunk))
        for cat in response.categories_analysis:
            key = str(cat.category)
            max_severities[key] = max(max_severities.get(key, 0), cat.severity)
    return max_severities
```

**Blocklists don't replace the model** — The built-in ML model and blocklists run independently. Text can be flagged by the model even without blocklist matches, and vice versa. Always check both `categories_analysis` and `blocklists_match`.

**Image size validation** — The API rejects images outside the supported range (50×50 min, 2048×2048 max, 4 MB max). Validate and resize images before sending to avoid `InvalidRequestBody` errors.

**Severity 0 is not guaranteed safe** — A severity of 0 means the model did not detect content in that category above the detection threshold. It is not a guarantee of safety. Apply additional context-aware filtering in your application layer for high-stakes use cases.

**Use `categories` to reduce cost and latency** — If your use case only cares about specific categories (e.g., only Violence for a gaming platform), pass `categories=[TextCategory.VIOLENCE]` to skip unnecessary analysis.

**Blocklist item IDs** — When adding items, save the returned `blocklist_item_id` values if you need to remove specific items later. There is no search-by-text API; you must use the item ID.

**ContentSafetyClient vs BlocklistClient** — These are separate clients with different endpoints. `ContentSafetyClient` is for analysis. `BlocklistClient` is for CRUD on blocklists. Both use the same endpoint and credential.

---

## Reference Links

- [azure-ai-contentsafety on PyPI](https://pypi.org/project/azure-ai-contentsafety/)
- [GitHub: azure-ai-contentsafety](https://github.com/Azure/azure-sdk-for-python/tree/main/sdk/contentsafety/azure-ai-contentsafety)
- [SDK Samples](https://github.com/Azure/azure-sdk-for-python/tree/main/sdk/contentsafety/azure-ai-contentsafety/samples)
- [Azure AI Content Safety Documentation](https://learn.microsoft.com/azure/ai-services/content-safety/)
- [Harm categories reference](https://learn.microsoft.com/azure/ai-services/content-safety/concepts/harm-categories)
