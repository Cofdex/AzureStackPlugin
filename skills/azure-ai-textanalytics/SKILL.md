---
name: azure-ai-textanalytics
description: >
  Natural language processing using the Azure AI Text Analytics Python SDK (azure-ai-textanalytics).
  Use this skill whenever working with TextAnalyticsClient, sentiment analysis, named entity
  recognition (NER), key phrase extraction, language detection, PII detection and redaction,
  entity linking, healthcare NLP, extractive/abstractive text summarization, or multi-action
  batch analysis. Also use for opinion mining, confidence scores, and batch document processing.
  Triggers: "text analytics", "sentiment analysis", "entity recognition", "named entity",
  "key phrase extraction", "language detection", "PII detection", "PII redaction",
  "TextAnalyticsClient", "healthcare entities", "opinion mining", "text summarization",
  "azure-ai-textanalytics", "Azure Language service", "Cognitive Services NLP".
---

# Azure AI Text Analytics SDK for Python

The `azure-ai-textanalytics` package provides a `TextAnalyticsClient` for NLP operations on batches
of text documents — sentiment, entities, key phrases, language detection, PII redaction,
healthcare entity extraction, and text summarization.

## Install

```bash
pip install azure-ai-textanalytics azure-identity
```

## Connect — TextAnalyticsClient

```python
import os
from azure.core.credentials import AzureKeyCredential
from azure.identity import DefaultAzureCredential
from azure.ai.textanalytics import TextAnalyticsClient

# Option 1: API key (simplest for testing)
client = TextAnalyticsClient(
    endpoint=os.environ["AZURE_LANGUAGE_ENDPOINT"],
    credential=AzureKeyCredential(os.environ["AZURE_LANGUAGE_KEY"]),
)

# Option 2: Azure AD (recommended for production)
client = TextAnalyticsClient(
    endpoint=os.environ["AZURE_LANGUAGE_ENDPOINT"],
    credential=DefaultAzureCredential(),
)
```

The endpoint looks like `https://<resource-name>.cognitiveservices.azure.com/`.

---

## Input Format

All methods accept a list of strings (simple) or a list of `TextDocumentInput` dicts:

```python
# Simple list of strings — document IDs auto-assigned
documents = ["I love this product!", "This was terrible.", "C'est magnifique!"]

# Explicit with language hints
documents = [
    {"id": "1", "language": "en", "text": "I love this product!"},
    {"id": "2", "language": "fr", "text": "C'est magnifique!"},
]
```

**Error handling per document:** Each result has `.is_error`. Always filter before accessing results:
```python
results = client.analyze_sentiment(documents)
for doc in results:
    if doc.is_error:
        print(f"Document {doc.id} error: {doc.error.message}")
    else:
        print(doc.sentiment)
```

---

## Sentiment Analysis

```python
results = client.analyze_sentiment(documents, show_opinion_mining=True)

for doc in results:
    if doc.is_error:
        continue
    print(f"Overall: {doc.sentiment}")                    # "positive", "neutral", "negative", "mixed"
    print(f"Positive score: {doc.confidence_scores.positive:.2f}")
    print(f"Negative score: {doc.confidence_scores.negative:.2f}")

    # Per-sentence breakdown
    for sentence in doc.sentences:
        print(f"  Sentence: '{sentence.text}' → {sentence.sentiment}")

        # Opinion mining (aspect-based sentiment) — requires show_opinion_mining=True
        for mined_opinion in sentence.mined_opinions:
            target = mined_opinion.target
            print(f"  Target: {target.text} ({target.sentiment})")
            for assessment in mined_opinion.assessments:
                print(f"    Assessment: {assessment.text} ({assessment.sentiment})")
```

---

## Named Entity Recognition (NER)

```python
results = client.recognize_entities(documents)

for doc in results:
    if doc.is_error:
        continue
    for entity in doc.entities:
        print(f"Text: {entity.text}")
        print(f"  Category: {entity.category}")       # Person, Location, Organization, DateTime, etc.
        print(f"  Subcategory: {entity.subcategory}")
        print(f"  Confidence: {entity.confidence_score:.2f}")
        print(f"  Offset: {entity.offset}, Length: {entity.length}")
```

Common entity categories: `Person`, `Location`, `Organization`, `Event`, `Product`,
`DateTime`, `Quantity`, `URL`, `IP`, `Email`.

---

## PII Detection and Redaction

```python
results = client.recognize_pii_entities(
    documents,
    categories_filter=["SSN", "PhoneNumber", "Email"],  # optional: target specific PII types
    language="en",
)

for doc in results:
    if doc.is_error:
        continue
    print(f"Redacted text: {doc.redacted_text}")      # text with PII replaced by *****
    for entity in doc.entities:
        print(f"  PII: {entity.text} → {entity.category} (score: {entity.confidence_score:.2f})")
```

PII categories include: `Person`, `PhoneNumber`, `Email`, `Address`, `CreditCardNumber`,
`USSocialSecurityNumber`, `IPAddress`, `Password`, `BankAccountNumber`, and many more.

---

## Key Phrase Extraction

```python
results = client.extract_key_phrases(documents)

for doc in results:
    if doc.is_error:
        continue
    print(f"Key phrases: {', '.join(doc.key_phrases)}")
```

Key phrases are the most salient talking points in the document — useful for indexing,
search, tagging, and summarization pipelines.

---

## Language Detection

```python
results = client.detect_language(
    documents=["Bonjour tout le monde", "Hello world", "Hola mundo"],
)

for doc in results:
    if doc.is_error:
        continue
    lang = doc.primary_language
    print(f"Detected: {lang.name} ({lang.iso6391_name}), confidence: {lang.confidence_score:.2f}")
    # lang.name e.g. "French", lang.iso6391_name e.g. "fr"
```

---

## Entity Linking

Links entities to well-known knowledge base entries (Wikipedia):

```python
results = client.recognize_linked_entities(documents)

for doc in results:
    if doc.is_error:
        continue
    for entity in doc.entities:
        print(f"Entity: {entity.name}")
        print(f"  URL: {entity.url}")        # Wikipedia link
        print(f"  Data source: {entity.data_source}")  # "Wikipedia"
        for match in entity.matches:
            print(f"  Match: '{match.text}' (score: {match.confidence_score:.2f})")
```

---

## Healthcare Entity Analysis

Healthcare NLP uses a Long-Running Operation (LRO) pattern via `begin_analyze_healthcare_entities`:

```python
from azure.ai.textanalytics import HealthcareEntityRelation

poller = client.begin_analyze_healthcare_entities(documents)
result = poller.result()

for doc in result:
    if doc.is_error:
        continue
    for entity in doc.entities:
        print(f"Entity: {entity.text}")
        print(f"  Category: {entity.category}")          # MedicationName, Dosage, BodyStructure, etc.
        print(f"  Normalized: {entity.normalized_text}") # standardized form
        if entity.assertion:
            print(f"  Certainty: {entity.assertion.certainty}")      # "positive", "negative", "neutral"
            print(f"  Association: {entity.assertion.association}")  # "subject", "other"
        for source in entity.data_sources or []:
            print(f"  Data source: {source.name}, ID: {source.entity_id}")

    # Entity relations (e.g., drug-dosage pairs)
    for relation in doc.entity_relations:
        if relation.relation_type == HealthcareEntityRelation.DOSAGE_OF_MEDICATION:
            roles = {r.name: r.entity.text for r in relation.roles}
            print(f"Medication: {roles.get('Medication')} → Dosage: {roles.get('Dosage')}")
```

Healthcare entity categories: `MedicationName`, `Dosage`, `Frequency`, `BodyStructure`,
`Symptom`, `Diagnosis`, `ExaminationName`, `TreatmentName`, and more.

---

## Text Summarization (Extractive & Abstractive)

Both summarization types use `begin_analyze_actions` (multi-action batch API):

```python
from azure.ai.textanalytics import ExtractiveSummaryAction, AbstractiveSummaryAction

# Extractive: selects key sentences from the original text
poller = client.begin_analyze_actions(
    documents,
    actions=[ExtractiveSummaryAction(max_sentence_count=3)],
)
for result in poller.result():
    for action_result in result:
        if not action_result.is_error:
            for doc in action_result.documents:
                print(" ".join([s.text for s in doc.sentences]))

# Abstractive: generates new summary sentences (may not be in original text)
poller = client.begin_analyze_actions(
    documents,
    actions=[AbstractiveSummaryAction(sentence_count=2)],
)
for result in poller.result():
    for action_result in result:
        if not action_result.is_error:
            for doc in action_result.documents:
                for summary in doc.summaries:
                    print(summary.text)
```

---

## Multi-Action Batch Analysis

Run multiple NLP operations in a single API call using `begin_analyze_actions`:

```python
from azure.ai.textanalytics import (
    RecognizeEntitiesAction,
    RecognizePiiEntitiesAction,
    ExtractKeyPhrasesAction,
    AnalyzeSentimentAction,
    ExtractiveSummaryAction,
)

poller = client.begin_analyze_actions(
    documents,
    actions=[
        RecognizeEntitiesAction(),
        RecognizePiiEntitiesAction(categories_filter=["PhoneNumber", "Email"]),
        ExtractKeyPhrasesAction(),
        AnalyzeSentimentAction(show_opinion_mining=True),
        ExtractiveSummaryAction(max_sentence_count=2),
    ],
    display_name="full-nlp-pipeline",
)

document_results = poller.result()
for doc_idx, action_results in enumerate(document_results):
    print(f"--- Document {doc_idx} ---")
    for action_result in action_results:
        if action_result.is_error:
            continue
        kind = action_result.kind
        if kind == "EntityRecognition":
            for entity in action_result.entities:
                print(f"  Entity: {entity.text} ({entity.category})")
        elif kind == "PiiEntityRecognition":
            print(f"  Redacted: {action_result.redacted_text}")
        elif kind == "KeyPhraseExtraction":
            print(f"  Key phrases: {', '.join(action_result.key_phrases)}")
        elif kind == "SentimentAnalysis":
            print(f"  Sentiment: {action_result.sentiment}")
        elif kind == "ExtractiveSummarization":
            print(f"  Summary: {' '.join(s.text for s in action_result.sentences)}")
```

---

## Async Usage

All operations have async equivalents via `AsyncTextAnalyticsClient`:

```python
import asyncio
from azure.ai.textanalytics.aio import TextAnalyticsClient as AsyncTextAnalyticsClient
from azure.core.credentials import AzureKeyCredential

async def analyze():
    async with AsyncTextAnalyticsClient(endpoint, AzureKeyCredential(key)) as client:
        result = await client.analyze_sentiment(documents)
        for doc in result:
            if not doc.is_error:
                print(doc.sentiment)

asyncio.run(analyze())
```

The async client has the same methods — prefix with `await` for regular operations and
`await poller.result()` for LRO operations.

---

## Key Patterns

**Batch size limits:** Max 5 documents per request for healthcare analysis; max 25 for most other
operations. Split large inputs into chunks before calling.

**Language hints:** Pass `language="en"` (ISO 639-1) to most methods for better accuracy.
For `detect_language`, pass `country_hint` instead.

**LRO vs synchronous:** Healthcare, summarization, and multi-action analyses are long-running
operations — use `begin_*` methods and call `.result()` to wait for completion.

**Error isolation:** `.is_error` is per-document. A single malformed document doesn't fail the
entire batch — always check before accessing result properties.
