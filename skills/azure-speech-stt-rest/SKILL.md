---
name: azure-speech-stt-rest
description: >
  Azure Speech to Text REST API for short audio files in Python — no Speech SDK required.
  Use this skill for simple, synchronous speech recognition of audio files up to 60 seconds
  using plain HTTP requests. Triggers on: "speech to text REST", "short audio transcription",
  "speech recognition REST API", "STT REST", "recognize speech REST", "transcribe audio REST",
  "azure speech REST", "cognitive services speech", "stt without SDK", "speech API key".
  Use whenever the user wants to transcribe a short audio clip using only the requests library
  and an Azure Speech API key, even if they just say "transcribe this audio file".
  DO NOT use for: audio longer than 60 seconds (use Batch Transcription API), real-time
  streaming (use Speech SDK), custom speech models (use Speech SDK), or speech translation.
---

# Azure Speech to Text REST API — Short Audio

Transcribe audio files up to 60 seconds using a single HTTP POST. No SDK, no complex setup —
just `requests` and an Azure Speech resource API key.

## Two REST API options

Azure has two STT REST endpoints. Choose based on your use case:

| | Short Audio REST | Fast Transcription REST |
|--|-----------------|------------------------|
| Max duration | **60 seconds** | 120 minutes |
| Max file size | ~10 MB | 300 MB |
| Request body | Raw audio bytes | Multipart form-data |
| Best for | Quick scripts, ≤60s clips | Files > 60s, modern apps |

Both work without the Speech SDK. This skill focuses on the **Short Audio** endpoint (the
simpler one for ≤60s files), but the Fast Transcription alternative is shown below too.

---

## Short Audio REST API

### Endpoint

```
POST https://<region>.stt.speech.microsoft.com/speech/recognition/conversation/cognitiveservices/v1
```

Replace `<region>` with your Azure resource region (e.g., `eastus`, `westeurope`, `southeastasia`).

Recognition modes (all work the same for most cases):
- `conversation` — general use, recommended
- `dictation` — optimized for longer dictated text
- `interactive` — short commands and questions

### Required query parameters

| Parameter | Example | Notes |
|-----------|---------|-------|
| `language` | `en-US` | **Required.** Omitting causes 400. |
| `format` | `simple` or `detailed` | Optional. Default: `simple` |
| `profanity` | `masked`, `removed`, `raw` | Optional. Default: `masked` |

### Required headers

| Header | Value |
|--------|-------|
| `Ocp-Apim-Subscription-Key` | Your Azure Speech resource key |
| `Content-Type` | `audio/wav; codecs=audio/pcm; samplerate=16000` for WAV |

### Audio format

WAV (PCM, 16 kHz, 16-bit, mono) is the most reliable format. Other accepted formats:
`audio/ogg; codecs=opus`, `audio/mp3`, `audio/flac`, `audio/amr-wb`

For other WAV specs (e.g., 44.1 kHz stereo), the service often accepts them but 16kHz mono PCM
is guaranteed to work. If you're unsure of your audio format, convert with `pydub` or `ffmpeg`.

### Minimal example

```python
import requests

def transcribe_short_audio(audio_path: str, region: str, api_key: str,
                            language: str = "en-US") -> str:
    """Transcribe an audio file up to 60 seconds. Returns the transcribed text."""
    endpoint = (
        f"https://{region}.stt.speech.microsoft.com"
        "/speech/recognition/conversation/cognitiveservices/v1"
    )
    with open(audio_path, "rb") as f:
        audio_data = f.read()

    response = requests.post(
        endpoint,
        headers={
            "Ocp-Apim-Subscription-Key": api_key,
            "Content-Type": "audio/wav; codecs=audio/pcm; samplerate=16000",
        },
        params={
            "language": language,
            "format": "simple",
        },
        data=audio_data,
        timeout=30,
    )
    response.raise_for_status()
    result = response.json()

    status = result.get("RecognitionStatus")
    if status == "Success":
        return result["DisplayText"]
    else:
        raise ValueError(f"Recognition failed: {status}")
```

### Response format — `simple`

```json
{
  "RecognitionStatus": "Success",
  "DisplayText": "Remind me to buy five pencils.",
  "Offset": "1236645672289",
  "Duration": "1236645672289"
}
```

`Offset` and `Duration` are in 100-nanosecond units (divide by 10,000,000 for seconds).

### Response format — `detailed`

When `format=detailed`, you get the N-best list with confidence scores:

```json
{
  "RecognitionStatus": "Success",
  "NBest": [
    {
      "Confidence": 0.9053,
      "Display": "What's the weather like?",
      "ITN": "what's the weather like",
      "Lexical": "what's the weather like",
      "MaskedITN": "what's the weather like"
    }
  ]
}
```

- `Display` — punctuated, formatted text (what users see)
- `ITN` — inverse text normalized (numbers, dates converted)
- `Lexical` — raw words spoken
- `Confidence` — 0.0–1.0 score

### RecognitionStatus values

| Status | Meaning |
|--------|---------|
| `Success` | Speech recognized successfully |
| `NoMatch` | Speech detected but no words matched |
| `InitialSilenceTimeout` | Audio started with silence (no speech detected) |
| `EndSilenceTimeout` | Speech detected but ended early |
| `BabbleTimeout` | Background noise detected instead of speech |
| `Error` | Service-side error |

### Error handling

```python
import requests
from requests.exceptions import HTTPError, Timeout

def transcribe_with_error_handling(audio_path: str, region: str, api_key: str,
                                    language: str = "en-US") -> dict:
    endpoint = (
        f"https://{region}.stt.speech.microsoft.com"
        "/speech/recognition/conversation/cognitiveservices/v1"
    )
    try:
        with open(audio_path, "rb") as f:
            audio_data = f.read()

        response = requests.post(
            endpoint,
            headers={
                "Ocp-Apim-Subscription-Key": api_key,
                "Content-Type": "audio/wav; codecs=audio/pcm; samplerate=16000",
            },
            params={"language": language, "format": "detailed"},
            data=audio_data,
            timeout=30,
        )

        if response.status_code == 401:
            raise ValueError("Invalid API key or wrong region")
        if response.status_code == 429:
            retry_after = response.headers.get("Retry-After", "60")
            raise RuntimeError(f"Rate limited. Retry after {retry_after}s")
        response.raise_for_status()

        result = response.json()
        status = result.get("RecognitionStatus")

        if status == "Success":
            best = result["NBest"][0]
            return {"text": best["Display"], "confidence": best["Confidence"]}
        elif status == "NoMatch":
            return {"text": "", "confidence": 0.0, "status": "no_match"}
        elif status in ("InitialSilenceTimeout", "EndSilenceTimeout", "BabbleTimeout"):
            return {"text": "", "confidence": 0.0, "status": "silence_or_noise"}
        else:
            raise RuntimeError(f"Recognition error: {status}")

    except Timeout:
        raise RuntimeError("Request timed out — check network or increase timeout")
```

### HTTP error codes

| Code | Cause | Fix |
|------|-------|-----|
| 400 | Invalid language, missing `language` param, unsupported audio | Check params + audio format |
| 401 | Bad API key or wrong region in URL | Verify key and region match |
| 403 | Auth header missing entirely | Add `Ocp-Apim-Subscription-Key` header |
| 415 | Unsupported `Content-Type` | Use `audio/wav; codecs=audio/pcm; samplerate=16000` |
| 429 | Rate limit exceeded (600 req/min) | Back off, check `Retry-After` header |
| 5xx | Service error | Retry with exponential backoff |

---

## Fast Transcription API (alternative — works beyond 60s too)

For a more modern approach or files up to 120 minutes:

```python
import requests, json

def transcribe_fast(audio_path: str, region: str, api_key: str,
                    language: str = "en-US") -> str:
    endpoint = (
        f"https://{region}.api.cognitive.microsoft.com"
        "/speechtotext/transcriptions:transcribe?api-version=2025-10-15"
    )
    with open(audio_path, "rb") as f:
        audio_bytes = f.read()

    response = requests.post(
        endpoint,
        headers={"Ocp-Apim-Subscription-Key": api_key},
        files={
            "audio": ("audio.wav", audio_bytes, "audio/wav"),
            "definition": (None, json.dumps({"locales": [language]}),
                           "application/json"),
        },
        timeout=60,
    )
    response.raise_for_status()
    result = response.json()
    return result["combinedPhrases"][0]["text"]
```

Fast Transcription uses **multipart form-data** (not raw bytes) and a different endpoint domain.
Response has `combinedPhrases[0].text` (full text) and `phrases[]` (per-segment with timestamps).

---

## When NOT to use these REST APIs

| Scenario | Use instead |
|----------|------------|
| Audio > 60s (Short Audio) or > 2h (Fast Transcription) | Batch Transcription API |
| Real-time/streaming transcription | Azure Speech SDK |
| Custom speech models | Azure Speech SDK |
| Speech-to-speech translation | Azure Speech SDK |
| Partial/interim results while speaking | Azure Speech SDK |
| Pronunciation assessment | Short Audio REST API (supported) |

---

## Quick setup checklist

1. **Create** Azure AI Speech resource (Azure Portal → Create resource → Azure AI Speech)
2. **Copy** the resource key (Keys and Endpoint → KEY 1) and region
3. **Install** `uv add requests`
4. **Use** key as `Ocp-Apim-Subscription-Key`, region in the URL
5. **Audio** must be ≤60s for Short Audio REST, valid audio format

Free tier: 5 audio hours/month, 0.5M characters (F0 pricing tier).
