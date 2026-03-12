---
name: azure-ai-foundry-agents
description: Build Azure AI Foundry agents using the Microsoft Agent Framework Python SDK (agent-framework-azure-ai). Use this skill whenever the user is creating persistent agents with AzureAIAgentsProvider, setting up AgentsClient, using hosted tools like code interpreter, file search, or Bing/web search grounding, integrating MCP servers (hosted or local), managing conversation threads and sessions, implementing streaming responses with event handlers, defining function tools, enforcing structured outputs with Pydantic, or building multi-tool agents. Trigger this skill any time the user mentions azure-ai-agents, azure-ai-projects, AzureAIAgentsProvider, agent-framework, AIProjectClient, AgentsClient, or Azure AI Foundry agent development in Python.
---

# Azure AI Foundry Agents Skill

You are an expert in building Azure AI Foundry agents using Python. This skill covers two complementary SDKs:

- **`azure-ai-agents`** (via `azure-ai-projects`) — the official Azure SDK, lower-level, full control
- **`agent-framework`** — a higher-level abstraction built on top, with `AzureAIAgentsProvider`

## Table of Contents

1. [Setup & Authentication](#1-setup--authentication)
2. [Two SDK Styles](#2-two-sdk-styles)
3. [Creating Agents](#3-creating-agents)
4. [Hosted Tools](#4-hosted-tools) — Code Interpreter, File Search, Bing, AI Search
5. [MCP Server Integration](#5-mcp-server-integration)
6. [Function Tools](#6-function-tools)
7. [Threads & Conversation Management](#7-threads--conversation-management)
8. [Running & Streaming](#8-running--streaming)
9. [Structured Outputs](#9-structured-outputs)
10. [Multi-Tool Agents](#10-multi-tool-agents)
11. [Cleanup & Resource Management](#11-cleanup--resource-management)
12. [Common Patterns & Pitfalls](#12-common-patterns--pitfalls)

---

## 1. Setup & Authentication

```bash
pip install azure-ai-projects azure-ai-agents azure-identity
# For agent-framework style (AzureAIAgentsProvider):
pip install agent-framework-azure-ai
# For async:
pip install aiohttp
```

**Required environment variables:**
```bash
PROJECT_ENDPOINT=https://<AIFoundryResourceName>.services.ai.azure.com/api/projects/<ProjectName>
MODEL_DEPLOYMENT_NAME=gpt-4o  # or your deployed model name
```

**Authentication** uses Azure Entra ID — no API keys needed:
```python
from azure.identity import DefaultAzureCredential
from azure.identity.aio import DefaultAzureCredential as AsyncDefaultAzureCredential
```

Run `az login` locally. In CI/CD or Azure-hosted environments, `DefaultAzureCredential` picks up managed identity or service principal automatically.

---

## 2. Two SDK Styles

### Style A: `azure-ai-projects` (recommended low-level)

```python
import os
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential

project_client = AIProjectClient(
    endpoint=os.environ["PROJECT_ENDPOINT"],
    credential=DefaultAzureCredential(),
)

# AgentsClient is accessed as project_client.agents
with project_client:
    agents_client = project_client.agents
    # ... all agent operations here
```

**Async variant** — import from `.aio` packages and use `async with`:
```python
from azure.ai.projects.aio import AIProjectClient
from azure.identity.aio import DefaultAzureCredential

async with AIProjectClient(endpoint=os.environ["PROJECT_ENDPOINT"], credential=DefaultAzureCredential()) as project_client:
    agents_client = project_client.agents
```

### Style B: `AzureAIAgentsProvider` (agent-framework, high-level)

```python
from agent_framework.azure import AzureAIAgentsProvider
from azure.identity.aio import AzureCliCredential

async with (
    AzureCliCredential() as credential,
    AzureAIAgentsProvider(credential=credential) as provider,
):
    agent = await provider.create_agent(
        name="MyAgent",
        instructions="You are a helpful assistant.",
        tools=my_function,
    )
    result = await agent.run("What's the weather?")
    print(result)
```

The provider handles agent lifecycle, sessions, and tool dispatch automatically. Use it when you want less boilerplate. Use Style A when you need full control (custom run polling, file management, approval flows).

---

## 3. Creating Agents

```python
# Minimal agent
agent = agents_client.create_agent(
    model=os.environ["MODEL_DEPLOYMENT_NAME"],
    name="my-agent",
    instructions="You are a helpful assistant.",
)
print(f"Created agent, ID: {agent.id}")

# Reuse an existing agent (avoid creating duplicates)
agent = agents_client.get_agent(agent_id="<existing-agent-id>")
```

Agents persist on Azure — they're not recreated per session. Pass `agent.id` around to reuse them, and call `agents_client.delete_agent(agent.id)` to clean up.

---

## 4. Hosted Tools

### Code Interpreter

Lets the agent execute Python in a secure sandbox — great for data analysis, charting, and math.

```python
from azure.ai.agents.models import CodeInterpreterTool, FilePurpose

# Optionally pre-load files
file = agents_client.files.upload_and_poll(
    file_path="data.csv", purpose=FilePurpose.AGENTS
)
code_interpreter = CodeInterpreterTool(file_ids=[file.id])

agent = agents_client.create_agent(
    model=os.environ["MODEL_DEPLOYMENT_NAME"],
    name="data-analyst",
    instructions="You analyze data and create visualizations.",
    tools=code_interpreter.definitions,
    tool_resources=code_interpreter.resources,
)
```

After the run, retrieve generated files (charts, processed data):
```python
messages = agents_client.messages.list(thread_id=thread.id)
for msg in messages:
    for img in msg.image_contents:
        agents_client.files.save(file_id=img.image_file.file_id, file_name="output.png")
    for ann in msg.file_path_annotations:
        agents_client.files.save(file_id=ann.file_path.file_id, file_name=ann.text.split("/")[-1])
```

### File Search (RAG over documents)

```python
from azure.ai.agents.models import FileSearchTool, FilePurpose

# Upload and index a document
file = agents_client.files.upload_and_poll(file_path="manual.pdf", purpose=FilePurpose.AGENTS)
vector_store = agents_client.vector_stores.create_and_poll(
    file_ids=[file.id], name="my-docs"
)

file_search = FileSearchTool(vector_store_ids=[vector_store.id])

agent = agents_client.create_agent(
    model=os.environ["MODEL_DEPLOYMENT_NAME"],
    name="doc-searcher",
    instructions="Search the uploaded documents to answer questions.",
    tools=file_search.definitions,
    tool_resources=file_search.resources,
)
```

For files already in Azure Blob Storage, use `VectorStoreDataSource` with `asset_type=VectorStoreDataSourceAssetType.URI_ASSET` instead of uploading. See `references/advanced-tools.md` for the full pattern.

### Bing Grounding (Web Search)

```python
from azure.ai.agents.models import BingGroundingTool

conn_id = project_client.connections.get(os.environ["BING_CONNECTION_NAME"]).id
bing = BingGroundingTool(connection_id=conn_id)

agent = agents_client.create_agent(
    model=os.environ["MODEL_DEPLOYMENT_NAME"],
    name="web-searcher",
    instructions="Search the web to answer questions with up-to-date information.",
    tools=bing.definitions,
)
```

### Azure AI Search

For Azure AI Search integration (enterprise RAG over existing search indexes), use `AzureAISearchTool` with a connection ID from `project_client.connections.get_default(ConnectionType.AZURE_AI_SEARCH).id`. See `references/advanced-tools.md`.

---

## 5. MCP Server Integration

MCP tools require explicit approval by default (the agent will pause and ask). You can set approval to `"never"` to auto-approve, or implement a `RunHandler` for custom logic.

```python
from azure.ai.agents.models import McpTool

mcp_tool = McpTool(
    server_label="my-mcp-server",
    server_url="https://my-mcp-server.example.com/sse",
    allowed_tools=["tool_a", "tool_b"],  # empty list = all tools allowed
)

agent = agents_client.create_agent(
    model=os.environ["MODEL_DEPLOYMENT_NAME"],
    name="mcp-agent",
    instructions="Use the MCP server tools to complete tasks.",
    tools=mcp_tool.definitions,
)

# Run with auto-approve (for trusted servers):
mcp_tool.set_approval_mode("never")
run = agents_client.runs.create(thread_id=thread.id, agent_id=agent.id, tool_resources=mcp_tool.resources)
```

**For manual MCP approval**, use a `RunHandler` — it's cleaner than a polling loop:
```python
from azure.ai.agents.models import RunHandler, RequiredMcpToolCall, ToolApproval, ThreadRun

class MyMcpHandler(RunHandler):
    def submit_mcp_tool_approval(
        self, *, run: ThreadRun, tool_call: RequiredMcpToolCall, **kwargs
    ) -> ToolApproval:
        # Add your approval logic here (e.g., check tool name, log, ask user)
        return ToolApproval(tool_call_id=tool_call.id, approve=True, headers=mcp_tool.headers)

run = agents_client.runs.create_and_process(
    thread_id=thread.id, agent_id=agent.id, run_handler=MyMcpHandler()
)
```

For the low-level polling approach (checking `requires_action` + `SubmitToolApprovalAction` in a loop), see the [samples on GitHub](https://github.com/Azure/azure-sdk-for-python/blob/main/sdk/ai/azure-ai-agents/samples/agents_tools/sample_agents_mcp.py).

---

## 6. Function Tools

Define Python functions and let the agent call them:

```python
from azure.ai.agents.models import FunctionTool, ToolSet
import json

def get_weather(city: str) -> str:
    """Get the current weather for a city."""
    return json.dumps({"city": city, "temp": "22°C", "condition": "sunny"})

def send_email(to: str, subject: str, body: str) -> str:
    """Send an email."""
    print(f"Email sent to {to}: {subject}")
    return "Email sent successfully"

# Wrap as FunctionTool
functions = FunctionTool({get_weather, send_email})
toolset = ToolSet()
toolset.add(functions)

# Enable automatic function dispatch (SDK calls your functions during runs)
agents_client.enable_auto_function_calls(toolset)

agent = agents_client.create_agent(
    model=os.environ["MODEL_DEPLOYMENT_NAME"],
    name="assistant",
    instructions="Help users with weather and email tasks.",
    toolset=toolset,
)

# create_and_process handles function calls automatically
run = agents_client.runs.create_and_process(thread_id=thread.id, agent_id=agent.id)
```

Function docstrings become the tool descriptions — write them clearly. Parameter types from annotations are used to build the JSON schema automatically.

**Async functions** — import from `azure.ai.agents.aio` and use `AsyncFunctionTool` + `AsyncToolSet`.

---

## 7. Threads & Conversation Management

Threads hold the conversation history. Reuse them across turns to maintain context.

```python
# Create a new thread
thread = agents_client.threads.create()
print(f"Thread ID: {thread.id}")  # Save this to continue the conversation later

# Resume an existing thread
thread = agents_client.threads.get(thread_id="<saved-thread-id>")

# Add a user message
message = agents_client.messages.create(
    thread_id=thread.id,
    role="user",
    content="Analyze this data and create a chart.",
)

# List all messages (ascending = chronological order)
from azure.ai.agents.models import ListSortOrder
messages = agents_client.messages.list(thread_id=thread.id, order=ListSortOrder.ASCENDING)
for msg in messages:
    for text in msg.text_messages:
        print(f"{msg.role}: {text.text.value}")

# List all threads
threads = agents_client.threads.list()

# Clean up when done
agents_client.threads.delete(thread_id=thread.id)
```

**Attach files to a thread** (thread-scoped):
```python
thread = agents_client.threads.create(tool_resources=file_search.resources)
```

**Attach files to a message** (message-scoped):
```python
from azure.ai.agents.models import MessageAttachment
attachment = MessageAttachment(file_id=file.id, tools=FileSearchTool().definitions)
message = agents_client.messages.create(
    thread_id=thread.id, role="user",
    content="What does this document say?", attachments=[attachment]
)
```

---

## 8. Running & Streaming

Three ways to execute a run:

| Method | Use when |
|--------|----------|
| `runs.create` + poll loop | Full manual control, custom function dispatch |
| `runs.create_and_process` | Auto function calls, no streaming needed |
| `runs.stream` | Real-time token streaming to users |

### Basic polling:
```python
import time
run = agents_client.runs.create(thread_id=thread.id, agent_id=agent.id)
while run.status in ["queued", "in_progress", "requires_action"]:
    time.sleep(1)
    run = agents_client.runs.get(thread_id=thread.id, run_id=run.id)
print(f"Run finished with status: {run.status}")
```

### Streaming with iteration:
```python
from azure.ai.agents.models import (
    MessageDeltaChunk, ThreadMessage, ThreadRun, RunStep, AgentStreamEvent
)

with agents_client.runs.stream(thread_id=thread.id, agent_id=agent.id) as stream:
    for event_type, event_data, _ in stream:
        if isinstance(event_data, MessageDeltaChunk):
            print(event_data.text, end="", flush=True)
        elif isinstance(event_data, ThreadRun) and event_data.status == "failed":
            print(f"\nRun failed: {event_data.last_error}")
        elif event_type == AgentStreamEvent.DONE:
            print()  # newline after streamed content
            break
```

### Streaming with a custom event handler:
```python
from typing import Optional
from azure.ai.agents.models import AgentEventHandler

class StreamingHandler(AgentEventHandler[str]):
    def on_message_delta(self, delta: MessageDeltaChunk) -> Optional[str]:
        print(delta.text, end="", flush=True)

    def on_done(self) -> Optional[str]:
        print()

with agents_client.runs.stream(
    thread_id=thread.id, agent_id=agent.id, event_handler=StreamingHandler()
) as stream:
    for _ in stream:
        pass
```

---

## 9. Structured Outputs

Use Pydantic models to enforce a specific response structure:

```python
from pydantic import BaseModel
from azure.ai.agents.models import ResponseFormatJsonSchema, ResponseFormatJsonSchemaType

class WeatherReport(BaseModel):
    city: str
    temperature_celsius: float
    condition: str
    forecast: list[str]

agent = agents_client.create_agent(
    model=os.environ["MODEL_DEPLOYMENT_NAME"],
    name="weather-agent",
    instructions="Always respond with structured weather data.",
    response_format=ResponseFormatJsonSchema(
        type=ResponseFormatJsonSchemaType.JSON_SCHEMA,
        json_schema=WeatherReport.model_json_schema(),
    ),
)
```

After the run, parse the response:
```python
import json
messages = agents_client.messages.list(thread_id=thread.id, order=ListSortOrder.DESCENDING)
for msg in messages:
    if msg.role == "assistant":
        raw = msg.text_messages[-1].text.value
        report = WeatherReport.model_validate(json.loads(raw))
        print(report.temperature_celsius)
        break
```

**With `agent-framework` (`AzureAIAgentsProvider`)**, pass the Pydantic model directly:
```python
result = await agent.run("Get weather for Seattle", response_format=WeatherReport)
```

---

## 10. Multi-Tool Agents

Combine tools by passing both `toolset` (for functions/code interpreter with auto-dispatch) and additional `tools`/`tool_resources` for hosted tools:

```python
from azure.ai.agents.models import CodeInterpreterTool, FileSearchTool, BingGroundingTool, FunctionTool, ToolSet

code_interpreter = CodeInterpreterTool()
file_search = FileSearchTool(vector_store_ids=[vector_store.id])
bing = BingGroundingTool(connection_id=bing_conn_id)
functions = FunctionTool({get_current_time, send_notification})

toolset = ToolSet()
toolset.add(functions)
toolset.add(code_interpreter)
agents_client.enable_auto_function_calls(toolset)

agent = agents_client.create_agent(
    model=os.environ["MODEL_DEPLOYMENT_NAME"],
    name="multi-tool-agent",
    instructions="Use the best tool for each task: code for analysis, documents for reference, web for current info.",
    toolset=toolset,
    tools=toolset.definitions + file_search.definitions + bing.definitions,
    tool_resources={**file_search.resources, **{"bing": {"connection_id": bing_conn_id}}},
)
```

When merging `tool_resources`, each tool type has its own key — don't overwrite existing entries.

---

## 11. Cleanup & Resource Management

Always clean up to avoid costs. Delete in order: agent → thread → files → vector stores:

```python
try:
    thread = agents_client.threads.create()
    # ... do work
finally:
    agents_client.threads.delete(thread_id=thread.id)
    agents_client.delete_agent(agent.id)
    if file:
        agents_client.files.delete(file_id=file.id)
    if vector_store:
        agents_client.vector_stores.delete(vector_store_id=vector_store.id)
```

---

## 12. Common Patterns & Pitfalls

**Agent reuse** — Agents are persistent resources. Don't recreate them on every call. Store the `agent.id` and retrieve with `get_agent()`.

**Function implementations aren't persisted** — If you fetch an existing agent with `get_agent()`, you MUST call `enable_auto_function_calls(toolset)` again with the function implementations before running it.

**File search requires both `tools` AND `tool_resources`** — Passing only `tools` with `FileSearchTool` won't work; you must also pass `tool_resources`.

**MCP approval flow** — By default, MCP tools require approval. Set `mcp_tool.set_approval_mode("never")` only for trusted, internal MCP servers.

**Thread scope vs agent scope** — Tools attached to the agent apply to all threads. Tools attached via thread creation or message attachments are scoped to that thread/message only.

**Endpoint format changed (May 2025)** — The old hub-based connection string format no longer works. Use the Foundry project endpoint: `https://<name>.services.ai.azure.com/api/projects/<project>`.

**Polling vs streaming** — For user-facing apps, always stream. For background batch jobs, polling with `create_and_process` is simpler and more reliable.

---

## Reference Links

- [azure-ai-agents Python README](https://github.com/Azure/azure-sdk-for-python/blob/main/sdk/ai/azure-ai-agents/README.md)
- [Azure AI Agents Quickstart](https://learn.microsoft.com/azure/ai-services/agents/quickstart?pivots=programming-language-python-azure)
- [agent-framework Azure AI examples](https://github.com/microsoft/agent-framework/tree/main/python/samples/02-agents/providers/azure_ai_agent)
- [Tool samples on GitHub](https://github.com/Azure/azure-sdk-for-python/tree/main/sdk/ai/azure-ai-agents/samples)
