---
name: azure-ai-contentsafety
description: >
  Detect harmful content in text and images using the Azure AI Content Safety Python SDK
  (azure-ai-contentsafety). Use this skill whenever the user works with ContentSafetyClient,
  BlocklistClient, AnalyzeTextOptions, AnalyzeImageOptions, ImageData, TextCategory,
  ImageCategory, or custom blocklists. ALWAYS use this skill for content moderation, harmful
  content detection, hate/violence/sexual/self-harm classification, severity scoring, text
  analysis, image analysis, blocklist management, or any scenario involving the
  azure-ai-contentsafety package. Triggers: "content safety", "content moderation",
  "harmful content", "hate speech detection", "violence detection", "azure-ai-contentsafety",
  "ContentSafetyClient", "text analysis", "image analysis", "blocklist".
---

# Azure AI Content Safety SDK

The `azure-ai-contentsafety` package provides text and image analysis APIs for detecting
harmful content across four categories (Hate, Violence, Sexual, SelfHarm) with multi-severity
scoring, plus custom blocklist management.

```bash
pip install azure-ai-contentsafety
```

---

## Two clients, two purposes

| Client | Purpose |
|---|---|
| `ContentSafetyClient` | Analyze text and images for harmful content |
| `BlocklistClient` | Create and manage custom word/phrase blocklists |

---

## Authentication

### API key (quickest)

```python
from azure.ai.contentsafety import ContentSafetyClient, BlocklistClient
from azure.core.credentials import AzureKeyCredential
import os

endpoint = os.environ["CONTENT_SAFETY_ENDPOINT"]
key = os.environ["CONTENT_SAFETY_KEY"]

client = ContentSafetyClient(endpoint, AzureKeyCredential(key))
blocklist_client = BlocklistClient(endpoint, AzureKeyCredential(key))
```

### Microsoft Entra ID (production recommended)

```python
from azure.ai.contentsafety import ContentSafetyClient
from azure.identity import DefaultAzureCredential

client = ContentSafetyClient(
    endpoint=os.environ["CONTENT_SAFETY_ENDPOINT"],
    credential=DefaultAzureCredential(),
)
```

**Required env vars:**
- `CONTENT_SAFETY_ENDPOINT` — e.g. `https://<resource>.cognitiveservices.azure.com/`
- `CONTENT_SAFETY_KEY` — API key (only for key-based auth)

---

## Text Analysis

Analyze text for harmful content across all four categories in a single call:

```python
from azure.ai.contentsafety import ContentSafetyClient
from azure.ai.contentsafety.models import AnalyzeTextOptions, TextCategory
from azure.core.credentials import AzureKeyCredential
from azure.core.exceptions import HttpResponseError

client = ContentSafetyClient(endpoint, AzureKeyCredential(key))

try:
    response = client.analyze_text(AnalyzeTextOptions(text="Your input text here"))
except HttpResponseError as e:
    print(f"Error {e.error.code}: {e.error.message}")
    raise

# Response contains a list — look up each category by name
for result in response.categories_analysis:
    print(f"{result.category}: severity {result.severity}")

# Or look up specific categories
hate = next(r for r in response.categories_analysis if r.category == TextCategory.HATE)
violence = next(r for r in response.categories_analysis if r.category == TextCategory.VIOLENCE)
sexual = next(r for r in response.categories_analysis if r.category == TextCategory.SEXUAL)
self_harm = next(r for r in response.categories_analysis if r.category == TextCategory.SELF_HARM)

print(f"Hate: {hate.severity}, Violence: {violence.severity}")
```

### Severity levels

The default response uses a 4-level scale. Severity 0 means safe; 6 is the most harmful.

| Severity | Meaning |
|---|---|
| `0` | Safe / negligible |
| `2` | Low |
| `4` | Medium |
| `6` | High |

To get the full 8-level scale (0–7):

```python
from azure.ai.contentsafety.models import AnalyzeTextOptions, AnalyzeTextOutputType

request = AnalyzeTextOptions(
    text="...",
    output_type=AnalyzeTextOutputType.EIGHT_SEVERITY_LEVELS,
)
```

### Filtering specific categories

To reduce cost/latency, request only the categories you care about:

```python
from azure.ai.contentsafety.models import TextCategory

request = AnalyzeTextOptions(
    text="...",
    categories=[TextCategory.HATE, TextCategory.VIOLENCE],
)
```

### Making a pass/fail decision

Severity 0 typically means safe; use a threshold appropriate for your use case:

```python
BLOCK_THRESHOLD = 4  # block medium and above

def is_safe(response) -> bool:
    return all(r.severity < BLOCK_THRESHOLD for r in response.categories_analysis)

response = client.analyze_text(AnalyzeTextOptions(text=user_input))
if not is_safe(response):
    print("Content blocked")
```

---

## Image Analysis

Supports local files (base64 bytes) or public URLs:

```python
from azure.ai.contentsafety.models import AnalyzeImageOptions, ImageData, ImageCategory

# From local file
with open("image.jpg", "rb") as f:
    request = AnalyzeImageOptions(image=ImageData(content=f.read()))

# From URL
request = AnalyzeImageOptions(image=ImageData(url="https://example.com/image.jpg"))

try:
    response = client.analyze_image(request)
except HttpResponseError as e:
    print(f"Error {e.error.code}: {e.error.message}")
    raise

for result in response.categories_analysis:
    print(f"{result.category}: severity {result.severity}")

# Image categories mirror text categories
hate = next(r for r in response.categories_analysis if r.category == ImageCategory.HATE)
violence = next(r for r in response.categories_analysis if r.category == ImageCategory.VIOLENCE)
```

Image severity uses the same 4-level scale (0, 2, 4, 6). There is no 8-level option for images.

---

## Custom Blocklists

Blocklists let you flag domain-specific terms that the ML model might miss. After creating and
populating a blocklist, reference it by name in `AnalyzeTextOptions`.

### Create a blocklist and add items

```python
from azure.ai.contentsafety import BlocklistClient
from azure.ai.contentsafety.models import (
    TextBlocklist,
    TextBlocklistItem,
    AddOrUpdateTextBlocklistItemsOptions,
)

blocklist_client = BlocklistClient(endpoint, AzureKeyCredential(key))

# Create (or update) the blocklist
blocklist_client.create_or_update_text_blocklist(
    blocklist_name="MyBlocklist",
    options=TextBlocklist(blocklist_name="MyBlocklist", description="Custom terms"),
)

# Add items (supports wildcards like "k*ll")
result = blocklist_client.add_or_update_blocklist_items(
    blocklist_name="MyBlocklist",
    options=AddOrUpdateTextBlocklistItemsOptions(
        blocklist_items=[
            TextBlocklistItem(text="k*ll"),
            TextBlocklistItem(text="h*te"),
        ]
    ),
)
for item in result.blocklist_items:
    print(f"Added: {item.blocklist_item_id} — {item.text}")
```

> Note: after adding/updating items, allow ~5 minutes before the blocklist takes effect.

### Analyze text with a blocklist

```python
from azure.ai.contentsafety.models import AnalyzeTextOptions

response = client.analyze_text(
    AnalyzeTextOptions(
        text="I h*te you and want to k*ll you.",
        blocklist_names=["MyBlocklist"],
        halt_on_blocklist_hit=False,  # True = stop immediately on first match
    )
)

# Blocklist matches are in a separate field
if response.blocklists_match:
    for match in response.blocklists_match:
        print(f"Matched '{match.blocklist_item_text}' in {match.blocklist_name}")

# Category severity is still returned alongside blocklist matches
for result in response.categories_analysis:
    print(f"{result.category}: severity {result.severity}")
```

### Manage blocklist items

```python
from azure.ai.contentsafety.models import RemoveTextBlocklistItemsOptions

# List all blocklists
for bl in blocklist_client.list_text_blocklists():
    print(f"{bl.blocklist_name}: {bl.description}")

# List items in a blocklist
for item in blocklist_client.list_text_blocklist_items("MyBlocklist"):
    print(f"{item.blocklist_item_id}: {item.text}")

# Remove specific items by ID
blocklist_client.remove_blocklist_items(
    blocklist_name="MyBlocklist",
    options=RemoveTextBlocklistItemsOptions(blocklist_item_ids=["<item-id>"]),
)

# Delete an entire blocklist
blocklist_client.delete_text_blocklist(blocklist_name="MyBlocklist")
```

---

## Async Client

All operations have async equivalents — import from `.aio`:

```python
import asyncio
from azure.ai.contentsafety.aio import ContentSafetyClient, BlocklistClient
from azure.identity.aio import DefaultAzureCredential
from azure.ai.contentsafety.models import AnalyzeTextOptions

async def analyze():
    async with ContentSafetyClient(endpoint, DefaultAzureCredential()) as client:
        response = await client.analyze_text(AnalyzeTextOptions(text="..."))
        for result in response.categories_analysis:
            print(f"{result.category}: {result.severity}")

asyncio.run(analyze())
```

---

## Categories quick reference

| Enum value | What it detects |
|---|---|
| `TextCategory.HATE` / `ImageCategory.HATE` | Discriminatory language, slurs, attacks on identity groups |
| `TextCategory.VIOLENCE` / `ImageCategory.VIOLENCE` | Physical harm, weapons, acts of violence |
| `TextCategory.SEXUAL` / `ImageCategory.SEXUAL` | Sexual content, explicit language |
| `TextCategory.SELF_HARM` / `ImageCategory.SELF_HARM` | Self-harm, suicide-related content |

Text and image use separate enum classes (`TextCategory` vs `ImageCategory`) but identical values.

---

## Error handling

Always wrap calls in `try/except HttpResponseError`:

```python
from azure.core.exceptions import HttpResponseError

try:
    response = client.analyze_text(AnalyzeTextOptions(text="..."))
except HttpResponseError as e:
    if e.error:
        print(f"Code: {e.error.code}, Message: {e.error.message}")
    raise
```

Common error codes: `InvalidRequestBody` (malformed input), `ContentSafetyOperationNotSupported`
(unsupported image format), `QuotaExceeded` (rate limit hit).
