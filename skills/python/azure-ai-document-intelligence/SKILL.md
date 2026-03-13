---
name: azure-ai-document-intelligence
description: >
  Azure AI Document Intelligence SDK for Python (azure-ai-documentintelligence).
  Use for extracting text, tables, key-value pairs, and structured fields from PDFs
  and images using prebuilt and custom models. Triggers on: "document intelligence",
  "form recognizer", "DocumentIntelligenceClient", "begin_analyze_document",
  "prebuilt-invoice", "prebuilt-receipt", "prebuilt-layout", "extract tables",
  "OCR", "document extraction". NOTE: use azure-ai-documentintelligence NOT the
  deprecated azure-ai-formrecognizer package.
---

# Azure AI Document Intelligence SDK for Python

## Package
```bash
pip install azure-ai-documentintelligence azure-identity
```

**⚠️ Use `azure-ai-documentintelligence`, NOT the deprecated `azure-ai-formrecognizer`.**

## Client

```python
from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.core.credentials import AzureKeyCredential
from azure.identity import DefaultAzureCredential

# API key
client = DocumentIntelligenceClient(
    endpoint="https://myresource.cognitiveservices.azure.com/",
    credential=AzureKeyCredential("your-key"),
)

# AAD
client = DocumentIntelligenceClient(
    endpoint="https://myresource.cognitiveservices.azure.com/",
    credential=DefaultAzureCredential(),
)
```

## Analyze a document (always use `poller.result()`)

```python
# From file bytes
with open("invoice.pdf", "rb") as f:
    poller = client.begin_analyze_document(
        model_id="prebuilt-invoice",   # string literal, not enum
        body=f,                         # file-like object or bytes
    )
result = poller.result()   # REQUIRED — begin_analyze returns a poller, not the result

# From URL
from azure.ai.documentintelligence.models import AnalyzeDocumentRequest
poller = client.begin_analyze_document(
    model_id="prebuilt-invoice",
    body=AnalyzeDocumentRequest(url_source="https://example.com/invoice.pdf"),
)
result = poller.result()
```

## Prebuilt model IDs (string literals)

| Model ID | Use for |
|---|---|
| `"prebuilt-read"` | Extract all text (OCR) |
| `"prebuilt-layout"` | Text + tables + structure |
| `"prebuilt-invoice"` | Invoice fields (vendor, amount, dates) |
| `"prebuilt-receipt"` | Receipt fields (merchant, total, items) |
| `"prebuilt-idDocument"` | Passports, driver's licenses |
| `"prebuilt-businessCard"` | Business card fields |
| `"prebuilt-tax.us.w2"` | W-2 tax form fields |

## Reading results

### Text extraction (prebuilt-read, prebuilt-layout)
```python
for page in result.pages:
    print(f"Page {page.page_number}")
    for line in page.lines:
        print(line.content)   # .content for raw text
    for word in page.words:
        print(f"{word.content} (confidence: {word.confidence})")
```

### Tables (prebuilt-layout)
```python
for table in result.tables:
    for cell in table.cells:
        print(f"[{cell.row_index},{cell.column_index}]: {cell.content}")
```

### Key-value pairs (prebuilt-layout)
```python
for kvp in result.key_value_pairs:
    key = kvp.key.content if kvp.key else ""
    val = kvp.value.content if kvp.value else ""
    print(f"{key}: {val}")
```

### Structured fields (prebuilt-invoice, prebuilt-receipt, etc.)
```python
for doc in result.documents:
    print(f"Model: {doc.doc_type}, Confidence: {doc.confidence}")
    
    # .value for the extracted value, NOT .content
    vendor = doc.fields.get("VendorName")
    if vendor:
        print(f"Vendor: {vendor.value} (confidence: {vendor.confidence})")
    
    # Currency fields
    total = doc.fields.get("InvoiceTotal")
    if total:
        print(f"Total: {total.value.amount} {total.value.currency_symbol}")
    
    # Date fields
    date = doc.fields.get("InvoiceDate")
    if date:
        print(f"Date: {date.value}")   # datetime object
    
    # Array fields (line items)
    items = doc.fields.get("Items")
    if items and items.value:
        for item in items.value:
            desc = item.value.get("Description")
            if desc:
                print(f"Item: {desc.value}")
```

## Common mistakes

| ❌ Wrong | ✅ Correct |
|---|---|
| `from azure.ai.formrecognizer import FormRecognizerClient` | `from azure.ai.documentintelligence import DocumentIntelligenceClient` |
| `result = client.begin_analyze_document(...)` | `poller = client.begin_analyze_document(...); result = poller.result()` |
| `model_id=PrebuiltModels.INVOICE` | `model_id="prebuilt-invoice"` — string literal |
| `doc.fields.get("VendorName").content` | `.value` for structured fields (not `.content`) |
| `doc.fields["VendorName"]` without null check | Use `.get("VendorName")` — field may be absent |
| `result.content` for full text | `result.content` works on AnalyzeResult but `page.lines[].content` for per-page |
