---
name: azure-ai-video-indexer
description: >
  Azure Video Indexer via REST API with Python. Use for uploading videos, extracting
  insights (transcripts, keywords, faces, emotions, labels), and retrieving indexed
  content. Triggers on: "video indexer", "video analysis", "video transcription",
  "extract video insights", "azure video indexer", "VideoIndexer".
  CRITICAL: There is NO official Python SDK or pip package. Must use REST API
  with requests library and Azure AD tokens. No VideoIndexerClient class exists.
---

# Azure Video Indexer — REST API with Python

> **No official Python SDK exists.** Use the REST API directly with `requests` + Azure AD token.

## Setup

```bash
pip install requests azure-identity
```

## Authentication

```python
import requests
from azure.identity import DefaultAzureCredential

def get_video_indexer_token() -> str:
    credential = DefaultAzureCredential()
    token = credential.get_token("https://api.videoindexer.ai/.default")
    return token.token

TOKEN = get_video_indexer_token()
LOCATION = "trial"     # or your Azure region, e.g. "eastus"
ACCOUNT_ID = "your-account-id"

BASE_URL = f"https://api.videoindexer.ai/{LOCATION}/Accounts/{ACCOUNT_ID}"
HEADERS = {"Authorization": f"Bearer {TOKEN}"}
```

## Upload video

```python
import os

def upload_video(video_url: str = None, video_path: str = None, name: str = "my-video") -> str:
    """Returns video_id."""
    params = {
        "name": name,
        "privacy": "Private",
        "language": "en-US",
    }
    
    if video_url:
        params["videoUrl"] = video_url
        response = requests.post(
            f"{BASE_URL}/Videos",
            headers=HEADERS,
            params=params,
        )
    elif video_path:
        with open(video_path, "rb") as f:
            response = requests.post(
                f"{BASE_URL}/Videos",
                headers=HEADERS,
                params=params,
                files={"file": (os.path.basename(video_path), f, "video/mp4")},
            )
    
    response.raise_for_status()
    video_id = response.json()["id"]
    return video_id

video_id = upload_video(video_url="https://example.com/video.mp4")
```

## Poll for indexing completion

```python
import time

def wait_for_indexing(video_id: str, timeout: int = 600) -> dict:
    """Poll until video is indexed. Returns index data."""
    start = time.time()
    while time.time() - start < timeout:
        response = requests.get(
            f"{BASE_URL}/Videos/{video_id}/Index",
            headers=HEADERS,
        )
        data = response.json()
        state = data.get("state", "")
        print(f"State: {state}")
        if state == "Processed":
            return data
        elif state == "Failed":
            raise Exception(f"Indexing failed: {data.get('failureMessage')}")
        time.sleep(15)
    raise TimeoutError("Indexing timed out")

index = wait_for_indexing(video_id)
```

## Extract insights

```python
def extract_insights(index: dict) -> dict:
    """Extract key insights from video index."""
    videos = index.get("videos", [])
    if not videos:
        return {}
    
    insights = videos[0].get("insights", {})
    
    return {
        "transcript": [
            {"text": t["text"], "time": t.get("instances", [{}])[0].get("start")}
            for t in insights.get("transcript", [])
        ],
        "keywords": [kw["text"] for kw in insights.get("keywords", [])],
        "labels": [lb["name"] for lb in insights.get("labels", [])],
        "faces": [
            {"name": f["name"], "confidence": f["confidence"]}
            for f in insights.get("faces", [])
        ],
        "topics": [t["name"] for t in insights.get("topics", [])],
        "emotions": insights.get("emotions", []),   # NOT sentiment — emotions only
        "named_entities": [e["name"] for e in insights.get("namedEntities", [])],
    }

result = extract_insights(index)
print(result["keywords"])
print(result["transcript"][:3])
```

## Search within video

```python
response = requests.get(
    f"{BASE_URL}/Videos/Search",
    headers=HEADERS,
    params={"query": "machine learning", "pageSize": 10},
)
search_results = response.json()
```

## Delete video

```python
requests.delete(f"{BASE_URL}/Videos/{video_id}", headers=HEADERS)
```

## Common mistakes

| ❌ Wrong | ✅ Correct |
|---|---|
| `pip install azure-video-indexer` | No such package — use REST API + `requests` |
| `VideoIndexerClient(...)` | No such class — build REST calls manually |
| `insights["sentiment"]` | No sentiment — use `insights["emotions"]` instead |
| Expecting real-time results | Video Indexer is async — poll state until `"Processed"` |
| `Authorization: Bearer {api_key}` | Must use AAD token from `DefaultAzureCredential` |
| Using video URL before upload completes | Upload returns immediately; wait for `"Processed"` state |
