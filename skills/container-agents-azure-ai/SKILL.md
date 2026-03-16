---
name: container-agents-azure-ai
description: >
  Build and deploy container-based Foundry Agents using the Azure AI agentserver and projects SDKs.
  Use this skill whenever the user mentions ImageBasedHostedAgentDefinition, HostedAgentDefinition,
  FoundryCBAgent, AgentRunContext, hosted agents, container agents, Foundry Agent with custom image,
  create_version with a container, ProtocolVersionRecord, AgentProtocol.RESPONSES, or running a
  custom agent image in Azure AI Foundry. Also triggers for "deploy my agent to Foundry", "containerize
  an agent", or "serve agent as HTTP" patterns. ALWAYS use this skill for these scenarios.
---

# Container-Based Foundry Agents

Two separate SDKs work together: one runs **inside your container** (server side), and one
**registers the container** with Azure AI Foundry (client side).

```
┌─────────────────────────────────────────────┐
│  Your Container Image                        │
│  azure-ai-agentserver-core  ← FoundryCBAgent │
│  Exposes POST /responses on :8088            │
└──────────────┬──────────────────────────────┘
               │ registered via
┌──────────────▼──────────────────────────────┐
│  Azure AI Foundry                            │
│  azure-ai-projects  ← AIProjectClient        │
│  agents.create_version(HostedAgentDefinition)│
└─────────────────────────────────────────────┘
```

---

## Part 1 — Server side (inside your container)

### Installation

```bash
uv add azure-ai-agentserver-core
```

### Minimal custom agent

```python
from azure.ai.agentserver.core import FoundryCBAgent, AgentRunContext
from azure.ai.agentserver.core.models import Response as OpenAIResponse

agent = FoundryCBAgent()

async def handle(context: AgentRunContext) -> OpenAIResponse:
    user_input = context.request.input   # str
    return OpenAIResponse(
        output=[{"type": "message", "role": "assistant",
                 "content": [{"type": "output_text", "text": f"You said: {user_input}"}]}]
    )

agent.agent_run = handle

if __name__ == "__main__":
    agent.run()   # starts HTTP server on 0.0.0.0:8088
```

The server handles all JSON serialisation and error responses. You only implement `agent_run`.

### AgentRunContext fields

| Field | Type | Description |
|---|---|---|
| `context.request` | `AgentRunRequest` | Full request object |
| `context.request.input` | `str` | User's text input |
| `context.stream` | `bool` | Whether client requested streaming |
| `context.response_id` | `str` | ID to use in response objects |
| `context.id_generator` | `Callable[[], str]` | Generate unique IDs for events |

### Streaming response

Return an **async generator** that yields events in this exact sequence:

```python
from azure.ai.agentserver.core.models.projects import (
    ResponseCreatedEvent,
    ResponseOutputItemAddedEvent,
    ResponseTextDeltaEvent,
    ResponseTextDoneEvent,
    ResponseCompletedEvent,
    ResponsesAssistantMessageItemResource,
    ItemContentOutputText,
)

async def handle(context: AgentRunContext):
    response_id = context.response_id
    item_id = context.id_generator()
    full_text = ""

    async def stream():
        nonlocal full_text
        yield ResponseCreatedEvent(response={"id": response_id, "status": "in_progress"})
        yield ResponseOutputItemAddedEvent(
            item=ResponsesAssistantMessageItemResource(id=item_id, status="in_progress")
        )

        chunks = ["Hello ", "from ", "my agent!"]
        for chunk in chunks:
            full_text += chunk
            yield ResponseTextDeltaEvent(item_id=item_id, delta=chunk)

        yield ResponseTextDoneEvent(item_id=item_id, text=full_text)
        yield ResponseCompletedEvent(response={"id": response_id, "status": "completed"})

    return stream()

agent.agent_run = handle
```

The framework detects a generator return value and switches to SSE streaming automatically.

---

## Part 1b — Wrap an Agent Framework agent (optional)

If you already have a Microsoft Agent Framework agent, you can host it without writing the HTTP
server manually:

```bash
uv add azure-ai-agentserver-agentframework
```

```python
from azure.ai.agentserver.agentframework import from_agent_framework

# `agent` is any Agent Framework agent instance
from_agent_framework(agent).run()          # sync
# from_agent_framework(agent).run_async()  # async
```

Environment variables needed:

```
AZURE_OPENAI_ENDPOINT=https://<name>.cognitiveservices.azure.com/
OPENAI_API_VERSION=2025-03-01-preview
AZURE_OPENAI_CHAT_DEPLOYMENT_NAME=<deployment>
```

---

## Local testing

While developing, run your agent locally and hit it with curl:

```bash
# Non-streaming
curl -sS -X POST http://localhost:8088/responses \
  -H "Content-Type: application/json" \
  -d '{"input": "Hello!", "stream": false}'

# Streaming (server-sent events)
curl -N -X POST http://localhost:8088/responses \
  -H "Content-Type: application/json" \
  -d '{"input": "Hello!", "stream": true}'
```

---

## Part 2 — Register the container with Azure AI Foundry

### Installation

```bash
uv add "azure-ai-projects>=2.0.0"
```

### Key requirement: `allow_preview=True`

`HostedAgentDefinition` and `ImageBasedHostedAgentDefinition` are preview features. You **must**
pass `allow_preview=True` when constructing `AIProjectClient`, otherwise `create_version` will
raise an error.

```python
from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient

client = AIProjectClient(
    endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
    credential=DefaultAzureCredential(),
    allow_preview=True,   # REQUIRED for hosted/container agents
)
```

### Register with HostedAgentDefinition (azure-ai-projects)

`HostedAgentDefinition` in `azure-ai-projects` already includes the `image` field:

```python
from azure.ai.projects.models import (
    HostedAgentDefinition,
    ProtocolVersionRecord,
    AgentProtocol,
)

agent = client.agents.create_version(
    agent_name="my-container-agent",
    definition=HostedAgentDefinition(
        container_protocol_versions=[
            ProtocolVersionRecord(
                protocol=AgentProtocol.RESPONSES,
                version="v0.1.1",
            )
        ],
        cpu="1",
        memory="2Gi",
        image="myregistry.azurecr.io/my-agent:latest",
        environment_variables={
            "MY_API_KEY": os.environ["MY_API_KEY"],
        },
    ),
)
print(f"Registered: {agent.name} v{agent.version} (id={agent.id})")
```

### Register with ImageBasedHostedAgentDefinition (azure-ai-agentserver-core)

`ImageBasedHostedAgentDefinition` is the same class with `image` promoted to a **required**
parameter — use it when you want the type system to enforce that an image is always provided:

```python
from azure.ai.agentserver.core.models.projects import (
    ImageBasedHostedAgentDefinition,
    ProtocolVersionRecord,
    AgentProtocol,
)

agent = client.agents.create_version(
    agent_name="my-container-agent",
    definition=ImageBasedHostedAgentDefinition(
        container_protocol_versions=[
            ProtocolVersionRecord(protocol=AgentProtocol.RESPONSES, version="v0.1.1")
        ],
        cpu="1",
        memory="2Gi",
        image="myregistry.azurecr.io/my-agent:latest",
    ),
)
```

Both classes produce identical payloads — pick whichever you prefer.

### ProtocolVersionRecord values

| Field | Value |
|---|---|
| `protocol` | `AgentProtocol.RESPONSES` (`"responses"`) — matches the `/responses` endpoint |
| `version` | `"v0.1.1"` — current protocol version |

`AgentProtocol.ACTIVITY_PROTOCOL` (`"activity_protocol"`) exists but is for a different server
protocol; use `RESPONSES` for `FoundryCBAgent`.

### CPU and memory sizing

These are **string** values representing container resource limits:

| Setting | Common values |
|---|---|
| `cpu` | `"0.5"`, `"1"`, `"2"`, `"4"` (vCPU) |
| `memory` | `"1Gi"`, `"2Gi"`, `"4Gi"`, `"8Gi"` |

---

## Part 3 — Conversing with a registered agent

Use `AIProjectClient.get_openai_client()` to get an OpenAI client scoped to your Foundry project,
then use Conversations + Responses:

```python
with client.get_openai_client() as openai_client:
    # Create a conversation (holds message history)
    conversation = openai_client.conversations.create(
        items=[{
            "type": "message",
            "role": "user",
            "content": "What's the weather in Seattle?"
        }],
    )

    # Route the conversation to your container agent
    response = openai_client.responses.create(
        conversation=conversation.id,
        extra_body={
            "agent_reference": {
                "name": "my-container-agent",   # matches agent_name used at registration
                "type": "agent_reference",
            }
        },
    )
    print(response.output_text)

    # Continue the conversation
    openai_client.conversations.items.create(
        conversation_id=conversation.id,
        items=[{"type": "message", "role": "user", "content": "And in New York?"}],
    )
    response = openai_client.responses.create(
        conversation=conversation.id,
        extra_body={"agent_reference": {"name": "my-container-agent", "type": "agent_reference"}},
    )
    print(response.output_text)

    # Clean up
    openai_client.conversations.delete(conversation_id=conversation.id)
```

This API is **different** from the `azure-ai-agents` Threads/Runs API. Container agents use the
OpenAI Responses API routed through Foundry.

### Agent lifecycle management

```python
# List all versions
agent_record = client.agents.get(agent_name="my-container-agent")
print(f"Latest version: {agent_record.versions.latest.version}")

# Delete a specific version
client.agents.delete_version(
    agent_name="my-container-agent",
    agent_version="1",
)
```

---

## Environment variables

| Variable | Required | Description |
|---|---|---|
| `AZURE_AI_PROJECT_ENDPOINT` | ✅ | Foundry project endpoint URL |
| `AZURE_AI_MODEL_DEPLOYMENT_NAME` | Optional | Model deployment name (for prompt agents) |
| `AGENT_ID` | Runtime | Injected by Foundry into container at runtime |
| `AGENT_NAME` | Runtime | Injected by Foundry into container at runtime |
| `_AGENT_RUNTIME_APP_INSIGHTS_CONNECTION_STRING` | Runtime | App Insights (injected by Foundry) |

---

## End-to-end pattern summary

```
1. Implement agent logic   →  FoundryCBAgent in your Python code
2. Containerize            →  Dockerfile: expose port 8088, run agent.run()
3. Push image              →  docker push myregistry.azurecr.io/my-agent:latest
4. Register in Foundry     →  AIProjectClient.agents.create_version(HostedAgentDefinition(...))
5. Converse                →  openai_client.responses.create(conversation=..., agent_reference=...)
```

The container protocol (`FoundryCBAgent` + `/responses` endpoint) is what makes step 4's
`AgentProtocol.RESPONSES` work — Foundry routes incoming requests to your container over that
protocol.
