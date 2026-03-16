---
name: azure-openai
description: >
  Azure OpenAI SDK for Python (openai library with Azure endpoint). Use for chat
  completions, embeddings, image generation, streaming, and function calling via
  Azure OpenAI Service. Triggers on: "azure openai", "AzureOpenAI", "chat completions",
  "gpt-4", "gpt-35-turbo", "embeddings", "DALL-E", "streaming completions",
  "function calling", "tool use", "azure_endpoint", "api_version", "deployment name".
  CRITICAL: model= is deployment name, not model family. api_version is required.
---

# Azure OpenAI SDK for Python

## Package
```bash
uv add openai azure-identity
```

## Clients
- `AzureOpenAI` — synchronous
- `AsyncAzureOpenAI` — async

## Auth

```python
from openai import AzureOpenAI
from azure.identity import DefaultAzureCredential, get_bearer_token_provider

# API key auth (dev/test)
client = AzureOpenAI(
    api_key="your-api-key",
    azure_endpoint="https://myresource.openai.azure.com/",
    api_version="2024-02-01",   # required — omitting raises an error
)

# Azure AD auth (production, recommended)
token_provider = get_bearer_token_provider(
    DefaultAzureCredential(),
    "https://cognitiveservices.azure.com/.default"
)
client = AzureOpenAI(
    azure_endpoint="https://myresource.openai.azure.com/",
    azure_ad_token_provider=token_provider,   # NOT azure_ad_token=credential
    api_version="2024-02-01",
)
```

## Chat completions

```python
# model= is your DEPLOYMENT NAME, not "gpt-4" or "gpt-35-turbo"
response = client.chat.completions.create(
    model="my-gpt4-deployment",     # deployment name in Azure portal
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Explain Cosmos DB in one sentence."},
    ],
    temperature=0.7,
    max_tokens=200,
)

# Access content
text = response.choices[0].message.content
finish_reason = response.choices[0].finish_reason
prompt_tokens = response.usage.prompt_tokens
```

## Streaming

```python
stream = client.chat.completions.create(
    model="my-gpt4-deployment",
    messages=[{"role": "user", "content": "Tell me a story"}],
    stream=True,
)

for chunk in stream:
    delta = chunk.choices[0].delta.content   # may be None — check before printing
    if delta:
        print(delta, end="", flush=True)
```

## Embeddings

```python
response = client.embeddings.create(
    model="my-embeddings-deployment",   # deployment name for text-embedding-ada-002
    input="The quick brown fox",        # str or List[str]
)
vector = response.data[0].embedding    # List[float]
```

## Image generation (DALL-E)

```python
response = client.images.generate(
    model="my-dalle3-deployment",
    prompt="A futuristic Azure data center",
    n=1,
    size="1024x1024",
)
image_url = response.data[0].url
```

## Function / tool calling

```python
tools = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Get weather for a city",
            "parameters": {
                "type": "object",
                "properties": {"city": {"type": "string"}},
                "required": ["city"],
            },
        },
    }
]

response = client.chat.completions.create(
    model="my-gpt4-deployment",
    messages=[{"role": "user", "content": "What's the weather in Seattle?"}],
    tools=tools,
    tool_choice="auto",
)

# Check if model wants to call a tool
tool_call = response.choices[0].message.tool_calls
if tool_call:
    import json
    args = json.loads(tool_call[0].function.arguments)
    # call your function with args["city"]
```

## JSON mode

```python
response = client.chat.completions.create(
    model="my-gpt4-deployment",
    messages=[{"role": "user", "content": "Return a JSON object with name and age"}],
    response_format={"type": "json_object"},
)
import json
data = json.loads(response.choices[0].message.content)
```

## Async client

```python
from openai import AsyncAzureOpenAI

async_client = AsyncAzureOpenAI(
    azure_endpoint="https://myresource.openai.azure.com/",
    api_key="your-key",
    api_version="2024-02-01",
)
response = await async_client.chat.completions.create(
    model="my-gpt4-deployment",
    messages=[{"role": "user", "content": "Hello"}],
)
```

## Common mistakes

| ❌ Wrong | ✅ Correct |
|---|---|
| `model="gpt-4"` or `model="gpt-35-turbo"` | `model="your-deployment-name"` from Azure portal |
| `AzureOpenAI(api_key=..., azure_endpoint=...)` without `api_version` | `api_version="2024-02-01"` is **required** |
| `azure_ad_token=DefaultAzureCredential()` | Use `azure_ad_token_provider=get_bearer_token_provider(cred, scope)` |
| `response.choices[0].content` | `response.choices[0].message.content` |
| `chunk.content` in streaming | `chunk.choices[0].delta.content` (may be `None`) |
| `openai.ChatCompletion.create(...)` (v0 API) | `client.chat.completions.create(...)` (v1+ API) |
