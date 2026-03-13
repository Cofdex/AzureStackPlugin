---
name: azure-ai-vision-imageanalysis
description: >
  Azure AI Vision Image Analysis SDK for extracting rich information from images:
  natural language captions, dense region captions, content tags, object detection
  with bounding boxes, OCR text extraction, people detection, and smart cropping
  for thumbnails. Use this skill whenever working with the
  `azure-ai-vision-imageanalysis` package or `ImageAnalysisClient`, or whenever
  the task involves computer vision, image understanding, OCR on images, detecting
  objects or people in photos, generating image captions, or extracting text from
  screenshots/images. Always invoke this skill for "image analysis", "computer
  vision", "OCR", "object detection", "image caption", "ImageAnalysisClient",
  "VisualFeatures", or any task that analyzes image content programmatically with Azure.
---

# Azure AI Vision Image Analysis SDK

Package: `pip install azure-ai-vision-imageanalysis` (v1.0.0 stable)

## Client setup

`ImageAnalysisClient` requires an endpoint and a credential. The endpoint is your Azure Computer Vision resource URL — **do not** append `/computervision` or any path; the SDK adds it automatically.

```python
from azure.ai.vision.imageanalysis import ImageAnalysisClient
from azure.core.credentials import AzureKeyCredential

client = ImageAnalysisClient(
    endpoint=os.environ["VISION_ENDPOINT"],   # "https://<resource>.cognitiveservices.azure.com"
    credential=AzureKeyCredential(os.environ["VISION_KEY"])
)
```

Managed identity / Entra ID:
```python
from azure.identity import DefaultAzureCredential
client = ImageAnalysisClient(endpoint=endpoint, credential=DefaultAzureCredential())
```

Async client (same constructor, different import):
```python
from azure.ai.vision.imageanalysis.aio import ImageAnalysisClient
async with ImageAnalysisClient(endpoint=endpoint, credential=credential) as client:
    result = await client.analyze_from_url(image_url=url, visual_features=[...])
```

## The two analyze methods

Choose based on where the image lives:

```python
# From a public URL
result = client.analyze_from_url(
    image_url="https://example.com/photo.jpg",
    visual_features=[VisualFeatures.CAPTION, VisualFeatures.TAGS]
)

# From local file bytes
with open("photo.jpg", "rb") as f:
    result = client.analyze(
        image_data=f.read(),
        visual_features=[VisualFeatures.CAPTION, VisualFeatures.TAGS]
    )
```

Both methods accept the same optional keyword arguments:
- `language` — two-letter code (default `"en"`); captions only support English
- `gender_neutral_caption` — `True` → uses "person"/"child" instead of gendered terms
- `smart_crops_aspect_ratios` — list of floats (e.g., `[1.0, 1.5]`); only relevant when requesting `SMART_CROPS`
- `model_version` — default `"latest"`

## VisualFeatures enum

Import from `azure.ai.vision.imageanalysis.models`. Always pass a list — you can request multiple features in one call:

```python
from azure.ai.vision.imageanalysis.models import VisualFeatures

VisualFeatures.CAPTION         # One sentence describing the whole image
VisualFeatures.DENSE_CAPTIONS  # Up to 10 region-level captions with bounding boxes
VisualFeatures.TAGS            # Keywords describing content (objects, scenes, actions)
VisualFeatures.OBJECTS         # Physical objects + their bounding boxes
VisualFeatures.PEOPLE          # Detected people + their bounding boxes
VisualFeatures.READ            # OCR: extracts printed and handwritten text
VisualFeatures.SMART_CROPS     # Optimal crop regions at requested aspect ratios
```

## Reading results

Each feature maps to a nullable attribute on the result. Always check for `None` before accessing:

```python
result = client.analyze_from_url(image_url=url, visual_features=[
    VisualFeatures.CAPTION, VisualFeatures.TAGS, VisualFeatures.OBJECTS,
    VisualFeatures.PEOPLE, VisualFeatures.READ, VisualFeatures.SMART_CROPS
])

# Image metadata (always present)
print(f"{result.metadata.width}x{result.metadata.height}px, model: {result.model_version}")

# Caption
if result.caption:
    print(f"Caption: {result.caption.text} ({result.caption.confidence:.2f})")

# Dense captions — regions of interest with individual captions
if result.dense_captions:
    for cap in result.dense_captions.list:
        bb = cap.bounding_box
        print(f"  '{cap.text}' conf={cap.confidence:.2f} at ({bb.x},{bb.y}) {bb.width}x{bb.height}")

# Tags — flat list of keywords
if result.tags:
    for tag in result.tags.list:
        print(f"  tag: {tag.name} ({tag.confidence:.2f})")

# Objects — each has a bounding box and one or more named tags
if result.objects:
    for obj in result.objects.list:
        bb = obj.bounding_box
        name = obj.tags[0].name if obj.tags else "unknown"
        print(f"  object: {name} at ({bb.x},{bb.y}) {bb.width}x{bb.height}")

# People — bounding box + confidence, no identity
if result.people:
    for person in result.people.list:
        bb = person.bounding_box
        print(f"  person conf={person.confidence:.2f} at ({bb.x},{bb.y})")

# Smart crops — one region per requested aspect ratio
if result.smart_crops:
    for crop in result.smart_crops.list:
        bb = crop.bounding_box
        print(f"  crop {crop.aspect_ratio:.2f} → ({bb.x},{bb.y}) {bb.width}x{bb.height}")
```

## OCR in detail

The `READ` feature returns a hierarchy: blocks → lines → words. In practice the SDK always returns a single block containing all detected text.

```python
result = client.analyze_from_url(image_url=url, visual_features=[VisualFeatures.READ])

if result.read:
    for block in result.read.blocks:
        for line in block.lines:
            print(f"Line: {line.text}")
            # line.bounding_polygon — list of 4 ImagePoint (x,y) forming a quad
            for word in line.words:
                print(f"  '{word.text}' conf={word.confidence:.3f}")
                # word.bounding_polygon — same quad structure

# To extract all text as a single string:
full_text = "\n".join(
    line.text
    for block in result.read.blocks
    for line in block.lines
)
```

`ImageBoundingBox` attributes: `.x`, `.y`, `.width`, `.height` (all in pixels, integer).
`ImagePoint` attributes: `.x`, `.y`.

## Error handling

```python
from azure.core.exceptions import HttpResponseError

try:
    result = client.analyze_from_url(image_url=url, visual_features=[VisualFeatures.CAPTION])
except HttpResponseError as e:
    print(f"Status {e.status_code}: {e.reason}")
    if e.error:
        print(f"Code: {e.error.code}, Message: {e.error.message}")
```

## Key notes

- **CAPTION** and **DENSE_CAPTIONS** are only available in regions that support GPU-backed models (East US, West Europe, etc.) — you'll get a 403 if unsupported.
- **CAPTION** only generates English descriptions regardless of the `language` parameter.
- **READ** works for both printed and handwritten text in 60+ languages.
- The URL passed to `analyze_from_url` must be publicly accessible — the Azure service fetches it server-side.
- `SMART_CROPS` aspect ratios must be between 0.75 and 1.8 when explicitly specified.
- For PDFs and multi-page documents, use **Azure Document Intelligence** instead — this SDK is designed for single images.
