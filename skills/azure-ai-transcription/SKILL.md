---
name: azure-ai-transcription
description: >
  Speech-to-text transcription using the Azure AI Transcription Python SDK (azure-ai-transcription).
  Use this skill whenever working with TranscriptionClient, transcribing audio files or URLs,
  getting word-level timestamps and phrase segments, speaker diarization, multi-language detection,
  profanity filtering, phrase lists for custom vocabulary, channel separation, or enhanced
  transcription mode. Also use for batch audio processing and async transcription workflows.
  Triggers: "transcription", "speech to text", "azure-ai-transcription", "TranscriptionClient",
  "TranscriptionOptions", "TranscriptionDiarizationOptions", "speaker diarization",
  "audio transcription", "Azure AI Speech", "speech recognition", "transcribe audio",
  "word timestamps", "speaker identification", "phrase list", "profanity filter".
---

# Azure AI Transcription SDK for Python

The `azure-ai-transcription` package provides a `TranscriptionClient` for converting audio
to text with timestamps, speaker diarization, multi-language detection, and phrase customization.

## Install

```bash
pip install azure-ai-transcription azure-identity
```

## Connect — TranscriptionClient

```python
import os
from azure.core.credentials import AzureKeyCredential
from azure.identity import DefaultAzureCredential
from azure.ai.transcription import TranscriptionClient

# Option 1: API key (simplest for testing)
client = TranscriptionClient(
    endpoint=os.environ["AZURE_SPEECH_ENDPOINT"],
    credential=AzureKeyCredential(os.environ["AZURE_SPEECH_API_KEY"]),
)

# Option 2: Azure AD — recommended for production
client = TranscriptionClient(
    endpoint=os.environ["AZURE_SPEECH_ENDPOINT"],
    credential=DefaultAzureCredential(),
)
```

The endpoint looks like `https://<resource-name>.cognitiveservices.azure.com/`.
Assign `Cognitive Services User` role for Azure AD auth.

---

## Transcribe an Audio File

```python
from azure.ai.transcription.models import TranscriptionContent, TranscriptionOptions

with open("audio.wav", "rb") as audio_file:
    options = TranscriptionOptions(locales=["en-US"])
    request = TranscriptionContent(definition=options, audio=audio_file)
    result = client.transcribe(request)

# Full transcript text
print(result.combined_phrases[0].text)

# Per-phrase breakdown with timestamps
for phrase in result.phrases:
    start = phrase.offset_milliseconds
    end = start + phrase.duration_milliseconds
    print(f"[{start}ms – {end}ms]: {phrase.text}")
```

**Supported audio formats:** WAV, MP3, FLAC, OGG, and other common formats.

---

## Transcribe from a URL

For publicly accessible audio files (no file upload needed):

```python
from azure.ai.transcription.models import TranscriptionOptions

audio_url = "https://example.com/recordings/meeting.wav"
options = TranscriptionOptions(locales=["en-US"])

result = client.transcribe_from_url(audio_url, options=options)

print(result.combined_phrases[0].text)
print(f"Duration: {result.duration_milliseconds / 1000:.1f}s")
```

---

## Speaker Diarization

Diarization labels each phrase with a speaker identifier — essential for meeting transcripts,
interviews, or call center recordings:

```python
from azure.ai.transcription.models import (
    TranscriptionContent,
    TranscriptionOptions,
    TranscriptionDiarizationOptions,
)

with open("meeting.wav", "rb") as audio_file:
    diarization = TranscriptionDiarizationOptions(
        max_speakers=5  # Hint: expected max number of speakers (2–35)
    )
    options = TranscriptionOptions(
        locales=["en-US"],
        diarization_options=diarization,
    )
    result = client.transcribe(TranscriptionContent(definition=options, audio=audio_file))

for phrase in result.phrases:
    speaker = phrase.speaker if phrase.speaker is not None else "Unknown"
    print(f"Speaker {speaker} [{phrase.offset_milliseconds}ms]: {phrase.text}")
```

> **Note:** Diarization requires single-channel (mono) audio. Don't use channel separation
> (`channels=[0, 1]`) at the same time as diarization.

---

## Multi-Language Detection

Pass multiple locale candidates — the service detects the language per phrase:

```python
with open("multilingual.wav", "rb") as audio_file:
    options = TranscriptionOptions(
        locales=["en-US", "es-ES", "fr-FR", "de-DE"]
        # Omit locales entirely for fully automatic language detection
    )
    result = client.transcribe(TranscriptionContent(definition=options, audio=audio_file))

for phrase in result.phrases:
    locale = phrase.locale or "auto-detected"
    print(f"[{locale}] {phrase.text}")
```

---

## Phrase List (Custom Vocabulary)

Boost recognition accuracy for domain-specific terms, product names, and proper nouns:

```python
from azure.ai.transcription.models import (
    TranscriptionContent,
    TranscriptionOptions,
    PhraseListProperties,
)

with open("audio.wav", "rb") as audio_file:
    phrase_list = PhraseListProperties(
        phrases=["Contoso", "Rehaan", "XR-7000"],
        biasing_weight=5.0,  # 1.0–20.0; higher = stronger bias toward listed phrases
    )
    options = TranscriptionOptions(locales=["en-US"], phrase_list=phrase_list)
    result = client.transcribe(TranscriptionContent(definition=options, audio=audio_file))

print(result.combined_phrases[0].text)
```

---

## Profanity Filtering

Control how profanity appears in the output:

```python
from azure.ai.transcription.models import (
    TranscriptionContent,
    TranscriptionOptions,
)

with open("audio.wav", "rb") as audio_file:
    options = TranscriptionOptions(
        locales=["en-US"],
        profanity_filter_mode="Masked",   # "None" | "Removed" | "Tags" | "Masked"
        # "None"    → profanity passed through unchanged
        # "Removed" → profanity words omitted entirely
        # "Tags"    → profanity replaced with <profanity> tags
        # "Masked"  → profanity replaced with asterisks (****)
    )
    result = client.transcribe(TranscriptionContent(definition=options, audio=audio_file))

print(result.combined_phrases[0].text)
```

---

## Enhanced Mode (Translation / Summarization)

Enhanced mode enables additional capabilities such as translation during transcription:

```python
from azure.ai.transcription.models import (
    TranscriptionContent,
    TranscriptionOptions,
    EnhancedModeProperties,
)

with open("audio.wav", "rb") as audio_file:
    enhanced = EnhancedModeProperties(task="transcribe")
    options = TranscriptionOptions(enhanced_mode=enhanced)
    result = client.transcribe(TranscriptionContent(definition=options, audio=audio_file))

print(result.combined_phrases[0].text)
```

---

## Accessing the Result Object

The `TranscriptionResult` returned by `transcribe()` / `transcribe_from_url()`:

```python
result = client.transcribe(...)

# Full transcript (per channel, combined)
for combined in result.combined_phrases:
    print(f"Channel {combined.channel}: {combined.text}")

# Individual timed phrases
for phrase in result.phrases:
    print(f"Text:       {phrase.text}")
    print(f"Locale:     {phrase.locale}")            # detected or specified language
    print(f"Speaker:    {phrase.speaker}")            # diarization speaker ID (int or None)
    print(f"Offset:     {phrase.offset_milliseconds}ms")
    print(f"Duration:   {phrase.duration_milliseconds}ms")
    print(f"Channel:    {phrase.channel}")            # 0 or 1 for stereo
    print(f"Confidence: {phrase.confidence}")         # 0.0–1.0

# Total audio duration
print(f"Total: {result.duration_milliseconds / 1000:.1f}s")
```

---

## Async Usage

```python
import asyncio
from azure.ai.transcription.aio import TranscriptionClient as AsyncTranscriptionClient
from azure.core.credentials import AzureKeyCredential
from azure.ai.transcription.models import TranscriptionContent, TranscriptionOptions

async def transcribe_async():
    async with AsyncTranscriptionClient(
        endpoint=os.environ["AZURE_SPEECH_ENDPOINT"],
        credential=AzureKeyCredential(os.environ["AZURE_SPEECH_API_KEY"]),
    ) as client:
        with open("audio.wav", "rb") as audio_file:
            options = TranscriptionOptions(locales=["en-US"])
            result = await client.transcribe(
                TranscriptionContent(definition=options, audio=audio_file)
            )
        print(result.combined_phrases[0].text)

asyncio.run(transcribe_async())
```

The async client mirrors the sync client — prefix `transcribe()` and `transcribe_from_url()` with `await`.

---

## Error Handling

```python
from azure.core.exceptions import HttpResponseError

try:
    result = client.transcribe(request)
except HttpResponseError as e:
    print(f"HTTP {e.status_code}: {e.message}")
    # 401 → invalid API key or insufficient role
    # 400 → bad request (unsupported format, invalid options)
    # 413 → audio file too large
```

---

## Key Patterns

**`TranscriptionContent` wraps options + audio:** Always create `TranscriptionOptions` first,
then pass it as `definition` along with the audio binary or use `transcribe_from_url` with options
as a keyword argument.

**`combined_phrases` vs `phrases`:** `combined_phrases` gives the full transcript per channel.
`phrases` gives the segmented timed phrases — use these for timestamps, diarization labels,
and confidence scores.

**`phrase.speaker` is an integer, not a string:** Speaker IDs start at 0 or 1 (SDK-dependent);
always guard with `if phrase.speaker is not None` before using.

**Batch processing:** For large audio libraries, create one `TranscriptionClient` and reuse it
across many calls — connection pooling is handled automatically.
