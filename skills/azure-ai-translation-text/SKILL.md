---
name: azure-ai-translation-text
description: >
  Azure AI Text Translation SDK for real-time text translation, transliteration,
  language detection, and supported languages discovery. Use this skill whenever
  working with the `azure-ai-translation-text` package, `TextTranslationClient`,
  `TranslateInputItem`, `TranslationTarget`, or any of: translating text between
  languages, transliterating scripts (e.g., Chinese → Latin romanization),
  auto-detecting source language, handling HTML content translation, applying
  profanity filters, translating to multiple target languages simultaneously,
  or querying the supported language catalog. Always use this skill when the
  user mentions "text translation", "translator", "translate text",
  "transliterate", or "TextTranslationClient".
---

# Azure AI Text Translation SDK

Package: `pip install azure-ai-translation-text` (v1.x stable, v2.0b1 preview)

## Client setup

The `TextTranslationClient` needs either a **region** (for the global endpoint) or a **custom endpoint**. Most users go with region + API key:

```python
from azure.ai.translation.text import TextTranslationClient
from azure.core.credentials import AzureKeyCredential

credential = AzureKeyCredential(os.environ["AZURE_TEXT_TRANSLATION_APIKEY"])
client = TextTranslationClient(
    credential=credential,
    region=os.environ["AZURE_TEXT_TRANSLATION_REGION"]  # e.g., "eastus"
)
```

Custom/dedicated endpoint:
```python
client = TextTranslationClient(
    credential=AzureKeyCredential(key),
    endpoint="https://<resource>.cognitiveservices.azure.com/"
)
```

Async client (same constructor, different import):
```python
from azure.ai.translation.text.aio import TextTranslationClient
async with TextTranslationClient(credential=credential, region=region) as client:
    result = await client.translate(body=["hello"], to_language=["es"])
```

## Translating text — simple pattern

For most cases, pass a **list of strings** as `body` and a **list of target language codes** as `to_language`. The SDK auto-detects the source language:

```python
response = client.translate(body=["Hello world", "Good morning"], to_language=["fr", "es"])

for item in response:
    if item.detected_language:
        print(f"Detected: {item.detected_language.language} (confidence: {item.detected_language.score:.2f})")
    for t in item.translations:
        print(f"  → {t.language}: {t.text}")
```

- `to_language` is always a **list** — even for a single target: `["fr"]`
- `body` is a **list** — even for a single string: `["hello"]`
- `response[i]` corresponds to `body[i]`
- `detected_language.score` is a confidence float from 0.0 to 1.0

Specifying the source to skip detection:
```python
response = client.translate(body=["Bonjour le monde"], to_language=["en"], from_language="fr")
```

## Translating text — advanced pattern

Use `TranslateInputItem` and `TranslationTarget` when you need per-item control: HTML content, transliteration output, profanity handling, or custom/LLM models:

```python
from azure.ai.translation.text.models import (
    TranslateInputItem, TranslationTarget, TextType, ProfanityAction, ProfanityMarker
)

# HTML content — preserve tags, translate only visible text
item = TranslateInputItem(
    text="<p>This is <b>important</b>.</p>",
    targets=[TranslationTarget(language="de")],
    text_type=TextType.HTML
)
response = client.translate(body=[item])
```

Profanity filtering:
```python
item = TranslateInputItem(
    text="This sentence has profanity.",
    targets=[TranslationTarget(
        language="cs",
        profanity_action=ProfanityAction.MARKED,
        profanity_marker=ProfanityMarker.ASTERISK
    )]
)
```

Multiple targets per input item:
```python
item = TranslateInputItem(
    text="Azure is great",
    targets=[
        TranslationTarget(language="zh-Hans"),
        TranslationTarget(language="ja"),
        TranslationTarget(language="ar"),
    ]
)
response = client.translate(body=[item])
for t in response[0].translations:
    print(f"{t.language}: {t.text}")
```

Custom category / fine-tuned model:
```python
TranslationTarget(language="cs", deployment_name="<category-id>")
```

LLM-based translation (v2.0b1 preview only):
```python
TranslationTarget(language="zh-Hans", deployment_name="gpt-4o-mini", tone="formal", gender="female")
```

## Transliteration

Convert text between scripts without changing the language — useful for romanizing Chinese, Arabic, Japanese, etc.:

```python
response = client.transliterate(
    body=["这是个测试。"],
    language="zh-Hans",
    from_script="Hans",   # source script
    to_script="Latn"      # target script (romanization)
)

t = response[0]
print(f"{t.text}")   # "zhè shì gè cèshì。"
print(f"{t.script}") # "Latn"
```

You can also request transliterated output as part of a translation by setting `script` on `TranslationTarget`:

```python
TranslationTarget(language="zh-Hans", script="Latn")  # translate AND romanize
```

## Discovering supported languages

```python
languages = client.get_supported_languages()

# Languages available for translation
for code, lang in languages.translation.items():
    print(f"{code}: {lang.name} ({lang.native_name})")

# Languages available for transliteration + their scripts
for code, lang in languages.transliteration.items():
    print(f"{code}: {lang.name}")
    for script in lang.scripts:
        print(f"  {script.code}: {script.name} → {[t.code for t in script.to_scripts]}")

# Get names in a specific UI language
languages = client.get_supported_languages(accept_language="fr")

# Filter to a single capability
languages = client.get_supported_languages(scope="translation")  # "translation", "transliteration"
```

## Error handling

```python
from azure.core.exceptions import HttpResponseError

try:
    response = client.translate(body=["text"], to_language=["fr"])
except HttpResponseError as e:
    if e.error:
        print(f"Code: {e.error.code}")
        print(f"Message: {e.error.message}")
    raise
```

## Key notes

- **Dictionary lookup/examples were removed** from v1.0+. The REST API still supports them, but the Python SDK dropped these methods.
- The `to_language` parameter always takes a **list** — this is a common source of errors (`to_language=["fr"]` not `to_language="fr"`).
- For batch workloads, use `azure-ai-translation-document` (separate SDK) — this SDK is for real-time, in-memory text translation.
- The global endpoint (`api.cognitive.microsofttranslator.com`) requires the `region` parameter; dedicated endpoints do not.
- Import models from `azure.ai.translation.text.models`, not from the top-level package.
