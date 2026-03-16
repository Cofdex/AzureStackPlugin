---
name: azure-ai-voicelive
description: >
  Azure AI Voice Live SDK for building real-time, bidirectional voice AI applications
  using WebSocket streaming. Use this skill whenever building with the
  `azure-ai-voicelive` package, `VoiceLiveConnection`, or `connect()`, and whenever
  the task involves: voice assistants that respond in real-time speech, streaming
  microphone audio to an Azure AI model, receiving synthesized audio back, Server
  VAD (voice activity detection) for hands-free conversation, handling interruptions
  when a user speaks over the AI, function calling or MCP tool use from within a
  voice session, transcribing spoken input via the voice pipeline, or avatar
  integration with real-time speech. Always invoke this skill for "azure-ai-voicelive",
  "VoiceLiveConnection", "voice assistant", "real-time voice", "speech-to-speech",
  "voice chatbot", "ServerVad", "audio streaming AI", or any task that streams audio
  to and from an Azure AI model over WebSocket.
---

# Azure AI Voice Live SDK

Package: `uv add "azure-ai-voicelive[aiohttp]"` (v1.1.0 GA, **async-only**)

For audio capture/playback in samples: `uv add pyaudio python-dotenv`

This SDK streams audio over a WebSocket to an Azure AI model (e.g., `gpt-4o-realtime-preview`) and receives typed events back — including synthesized audio, transcripts, and tool calls — enabling real-time voice conversations.

## Connect

Everything happens inside an `async with connect(...)` context. The `connect()` function is the entry point — it opens the WebSocket and returns a `VoiceLiveConnection`.

```python
from azure.ai.voicelive.aio import connect
from azure.core.credentials import AzureKeyCredential
import os, asyncio

async def main():
    async with connect(
        endpoint=os.environ["AZURE_VOICELIVE_ENDPOINT"],
        credential=AzureKeyCredential(os.environ["AZURE_VOICELIVE_API_KEY"]),
        model="gpt-4o-realtime-preview"
    ) as conn:
        # configure session, then process events
        ...

asyncio.run(main())
```

AAD / managed identity (recommended for production):
```python
from azure.identity.aio import DefaultAzureCredential
async with connect(endpoint=endpoint, credential=DefaultAzureCredential(), model=model) as conn:
    ...
```

## Configure the session

After connecting, send a `session.update` to configure the conversation before any audio flows. Import everything from `azure.ai.voicelive.models`:

```python
from azure.ai.voicelive.models import (
    RequestSession, Modality, InputAudioFormat, OutputAudioFormat,
    ServerVad, AzureStandardVoice, AudioInputTranscriptionOptions
)

await conn.session.update(session=RequestSession(
    modalities=[Modality.TEXT, Modality.AUDIO],
    instructions="You are a helpful voice assistant.",
    voice=AzureStandardVoice(name="en-US-AvaNeural", type="azure-standard"),
    # voice="alloy"  ← or use an OpenAI voice string directly
    input_audio_format=InputAudioFormat.PCM16,
    output_audio_format=OutputAudioFormat.PCM16,
    turn_detection=ServerVad(
        threshold=0.5,            # speech detection sensitivity (0.0–1.0)
        prefix_padding_ms=300,    # audio kept before speech detected
        silence_duration_ms=500   # silence before turn ends
    ),
    input_audio_transcription=AudioInputTranscriptionOptions(model="whisper-1"),
))
```

The `SESSION_UPDATED` event signals the session is ready and audio can flow.

## Audio format

The service expects **24 kHz, 16-bit PCM, mono** audio in both directions. Send input audio as base64-encoded bytes:

```python
import base64

# chunk_bytes: raw PCM16 mono audio bytes from your microphone
audio_b64 = base64.b64encode(chunk_bytes).decode()
await conn.input_audio_buffer.append(audio=audio_b64)
```

Received audio arrives in `RESPONSE_AUDIO_DELTA` events as raw bytes (`event.delta`) — write directly to your speaker/output stream.

## Event loop

Iterate over the connection with `async for` to receive all server events:

```python
from azure.ai.voicelive.models import ServerEventType

async for event in conn:
    match event.type:
        case ServerEventType.SESSION_UPDATED:
            print(f"Session ready: {event.session.id}")

        case ServerEventType.INPUT_AUDIO_BUFFER_SPEECH_STARTED:
            # User started speaking — interrupt current AI response
            await conn.response.cancel()

        case ServerEventType.INPUT_AUDIO_BUFFER_SPEECH_STOPPED:
            # User stopped — AI will generate a response automatically (Server VAD)
            pass

        case ServerEventType.RESPONSE_AUDIO_DELTA:
            # Play this chunk through your speaker
            play_audio(event.delta)  # event.delta is raw bytes

        case ServerEventType.RESPONSE_AUDIO_TRANSCRIPT_DELTA:
            print(event.delta, end="", flush=True)  # AI's spoken text

        case ServerEventType.CONVERSATION_ITEM_INPUT_AUDIO_TRANSCRIPTION_COMPLETED:
            print(f"User said: {event.transcript}")

        case ServerEventType.RESPONSE_DONE:
            # AI finished its turn
            pass

        case ServerEventType.ERROR:
            print(f"Error: {event.error.message}")
            break
```

## Function calling

Define functions as `FunctionTool`, register them in the session, and handle the `RESPONSE_FUNCTION_CALL_ARGUMENTS_DONE` event:

```python
from azure.ai.voicelive.models import (
    FunctionTool, FunctionCallOutputItem, Tool, ToolChoiceLiteral
)
import json

# 1. Define the function
get_weather = FunctionTool(
    name="get_weather",
    description="Get the current weather for a location",
    parameters={
        "type": "object",
        "properties": {
            "location": {"type": "string", "description": "City name"}
        },
        "required": ["location"]
    }
)

# 2. Register in session
await conn.session.update(session=RequestSession(
    tools=[Tool(function=get_weather)],
    tool_choice=ToolChoiceLiteral.AUTO,
    ...
))

# 3. Handle the call in the event loop
async for event in conn:
    if event.type == ServerEventType.RESPONSE_FUNCTION_CALL_ARGUMENTS_DONE:
        # event.call_id, event.name, event.arguments (JSON string)
        args = json.loads(event.arguments)
        
        if event.name == "get_weather":
            result = fetch_weather(args["location"])  # your implementation
            
            # 4. Submit the result back
            await conn.conversation.create(
                item=FunctionCallOutputItem(
                    call_id=event.call_id,
                    output=json.dumps(result)
                )
            )
            # 5. Trigger the AI to continue
            await conn.response.create()
```

## MCP tools

Connect the voice session to an MCP server so the AI can call tools hosted there. Requires API version `2026-01-01-preview`:

```python
from azure.ai.voicelive.models import (
    MCPServer, MCPApprovalResponseRequestItem
)

# 1. Register MCP server in session
await conn.session.update(session=RequestSession(
    mcp_servers=[MCPServer(
        url="https://your-mcp-server.example.com/mcp",
        server_label="my-tools",
        server_description="Business data tools"
    )],
    ...
))

# 2. Handle approval requests in event loop
async for event in conn:
    if event.type == ServerEventType.RESPONSE_MCP_CALL_ARGUMENTS_DONE:
        # Inspect event.name / event.arguments, then approve or deny
        await conn.conversation.create(
            item=MCPApprovalResponseRequestItem(
                call_id=event.call_id,
                approve=True   # False to deny
            )
        )
    elif event.type == ServerEventType.RESPONSE_MCP_CALL_COMPLETED:
        # Tool call finished; AI will incorporate the result
        pass
```

## Interruption handling

When Server VAD detects the user speaking, cancel the current response to stop audio playback mid-sentence:

```python
if event.type == ServerEventType.INPUT_AUDIO_BUFFER_SPEECH_STARTED:
    await conn.response.cancel()
    # Also clear any audio already queued in your speaker output buffer
```

## Manual turn mode

Disable Server VAD if you want explicit control over when the AI responds (e.g., push-to-talk):

```python
await conn.session.update(session=RequestSession(
    turn_detection=None,   # disables Server VAD
    ...
))

# When ready for AI to respond:
await conn.input_audio_buffer.commit()
await conn.response.create()
```

## Key imports reference

```python
from azure.ai.voicelive.aio import connect              # entry point
from azure.ai.voicelive.models import (
    # Session config
    RequestSession, Modality, InputAudioFormat, OutputAudioFormat,
    ServerVad, AzureStandardVoice, AudioInputTranscriptionOptions,
    ToolChoiceLiteral,
    # Events
    ServerEventType,
    # Function tools
    FunctionTool, FunctionCallOutputItem, Tool,
    ResponseFunctionCallItem,
    # MCP
    MCPServer, MCPApprovalResponseRequestItem,
    # Error handling
    ItemType,
)
from azure.core.credentials import AzureKeyCredential
from azure.identity.aio import DefaultAzureCredential
```

## Key notes

- **Async-only**: No synchronous API exists. All code must use `async/await`.
- **Audio format is fixed**: 24 kHz PCM16 mono — both send and receive. The service will reject other formats.
- **Input audio is base64**: Encode with `base64.b64encode(bytes).decode()` before calling `append()`.
- **Output audio is raw bytes**: `event.delta` is already decoded bytes ready to write to a speaker.
- **Server VAD is the default**: It auto-detects speech and triggers responses. Disable it (`turn_detection=None`) only for push-to-talk patterns.
- **Always cancel on speech start**: For smooth interruption, call `conn.response.cancel()` immediately when `INPUT_AUDIO_BUFFER_SPEECH_STARTED` fires.
- **Function call flow requires `response.create()`**: After submitting function output, explicitly trigger the next AI turn with `await conn.response.create()`.
