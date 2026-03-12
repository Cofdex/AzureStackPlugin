---
name: agent-framework-azure-ai
description: >
  Build Azure AI Foundry agents using the Microsoft Azure AI Agents Python SDK.
  Use this skill whenever the user wants to: create persistent AI agents with AzureAIAgentsProvider
  or AIProjectClient, use hosted tools (code interpreter, file search, Bing web search/grounding),
  integrate MCP (Model Context Protocol) servers with agents, manage conversation threads
  and runs, implement streaming responses with event handlers, define Python function tools,
  enforce structured JSON outputs with Pydantic or JSON Schema, or build multi-tool agents
  combining multiple capabilities. Triggers on phrases like "Azure AI agent", "AI Foundry agent",
  "agent with code interpreter", "agent with file search", "streaming agent", "function tool agent",
  "MCP agent", or any mention of azure-ai-agents SDK.
---

# Azure AI Foundry Agents — SDK Guide

**Package**: `azure-ai-agents` (+ `azure-ai-projects` for the project client)  
**Auth**: `DefaultAzureCredential` from `azure-identity`  
**Env vars needed**: `PROJECT_ENDPOINT`, `MODEL_DEPLOYMENT_NAME`

```bash
pip install azure-ai-projects azure-ai-agents azure-identity
```

---

## Core Lifecycle

Every agent interaction follows this pattern: **create agent → create thread → add message → run → poll/stream → read messages**.

```python
import os, time
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential
from azure.ai.agents.models import ListSortOrder

client = AIProjectClient(
    endpoint=os.environ["PROJECT_ENDPOINT"],
    credential=DefaultAzureCredential(),
)

with client:
    agents = client.agents

    # 1. Create (or reuse) agent — agents are persistent, identified by agent.id
    agent = agents.create_agent(
        model=os.environ["MODEL_DEPLOYMENT_NAME"],
        name="my-agent",
        instructions="You are a helpful assistant.",
        # tools=..., tool_resources=...  (see tool sections below)
    )

    # Reuse an existing agent: agent = agents.get_agent(agent_id)
    # List all: agents.list_agents()
    # Delete when done: agents.delete_agent(agent.id)

    # 2. Create a thread (conversation session)
    thread = agents.threads.create()
    # Reuse: thread = agents.threads.get(thread_id)

    # 3. Add user message
    agents.messages.create(thread_id=thread.id, role="user", content="Hello!")

    # 4a. Run (blocking helper — handles polling internally)
    run = agents.runs.create_and_process(thread_id=thread.id, agent_id=agent.id)

    # 4b. Manual poll (gives more control)
    run = agents.runs.create(thread_id=thread.id, agent_id=agent.id)
    while run.status in ["queued", "in_progress", "requires_action"]:
        time.sleep(1)
        run = agents.runs.get(thread_id=thread.id, run_id=run.id)
        # Handle requires_action here if using function tools (see Function Tools)

    # 5. Read response
    messages = agents.messages.list(thread_id=thread.id, order=ListSortOrder.ASCENDING)
    for msg in messages:
        if msg.text_messages:
            print(f"{msg.role}: {msg.text_messages[-1].text.value}")

    # Or get just the last agent message:
    last = agents.messages.get_last_message_by_role(thread_id=thread.id, role="assistant")
```

---

## Hosted Tools

### Code Interpreter

Executes Python code in a sandbox. Can upload files (CSV, Excel, images) for analysis and returns generated files.

```python
from azure.ai.agents.models import CodeInterpreterTool, FilePurpose, MessageRole

# Upload a file
file = agents.files.upload_and_poll(file_path="data.csv", purpose=FilePurpose.AGENTS)

code_interpreter = CodeInterpreterTool(file_ids=[file.id])

agent = agents.create_agent(
    model=os.environ["MODEL_DEPLOYMENT_NAME"],
    name="data-analyst",
    instructions="Analyze data and produce charts when asked.",
    tools=code_interpreter.definitions,
    tool_resources=code_interpreter.resources,
)

# After the run, retrieve generated images/files from messages:
for msg in agents.messages.list(thread_id=thread.id):
    for img in msg.image_contents:
        agents.files.save(file_id=img.image_file.file_id, file_name="output.png")
    for ann in msg.file_path_annotations:
        print(f"Generated file: {ann.file_path.file_id}")

# Clean up
agents.files.delete(file.id)
```

### File Search

Answers questions from uploaded documents via vector search. Requires creating a vector store.

```python
from azure.ai.agents.models import FileSearchTool, FilePurpose

file = agents.files.upload_and_poll(file_path="product_docs.md", purpose=FilePurpose.AGENTS)
vector_store = agents.vector_stores.create_and_poll(file_ids=[file.id], name="my-vectorstore")

file_search = FileSearchTool(vector_store_ids=[vector_store.id])

agent = agents.create_agent(
    model=os.environ["MODEL_DEPLOYMENT_NAME"],
    name="doc-search-agent",
    instructions="Answer questions based on the uploaded documents.",
    tools=file_search.definitions,
    tool_resources=file_search.resources,
)

# Clean up vector store and file when done
agents.vector_stores.delete(vector_store.id)
agents.files.delete(file.id)
```

### Bing Web Search (Grounding)

Lets the agent search the web via a Bing connection configured in Azure AI Foundry.

```python
from azure.ai.agents.models import BingGroundingTool, MessageRole

conn_id = client.connections.get(os.environ["BING_CONNECTION_NAME"]).id
bing = BingGroundingTool(connection_id=conn_id)

agent = agents.create_agent(
    model=os.environ["MODEL_DEPLOYMENT_NAME"],
    name="web-search-agent",
    instructions="Answer questions using web search.",
    tools=bing.definitions,
)

# After the run, citations come in url_citation_annotations:
response = agents.messages.get_last_message_by_role(thread_id=thread.id, role=MessageRole.AGENT)
for ann in response.url_citation_annotations:
    print(f"[{ann.url_citation.title}]({ann.url_citation.url})")
```

---

## Function Tools

Define Python callables with docstrings — the SDK introspects them to generate tool schemas automatically. Functions must return a JSON string.

```python
import json
from azure.ai.agents.models import FunctionTool, RequiredFunctionToolCall, SubmitToolOutputsAction, ToolOutput

def get_weather(location: str) -> str:
    """Get weather for a location.
    :param location: City name.
    :return: JSON weather data.
    """
    return json.dumps({"weather": "Sunny, 25°C", "location": location})

def send_email(to: str, subject: str, body: str) -> str:
    """Send an email.
    :param to: Recipient email address.
    :param subject: Email subject.
    :param body: Email body.
    :return: JSON confirmation.
    """
    return json.dumps({"status": f"Email sent to {to}"})

# Pass a set of callables — the SDK builds tool definitions from docstrings
functions = FunctionTool(functions={get_weather, send_email})

agent = agents.create_agent(
    model=os.environ["MODEL_DEPLOYMENT_NAME"],
    name="function-agent",
    instructions="Help the user with weather and email tasks.",
    tools=functions.definitions,
)

# When polling manually, handle requires_action to execute function calls:
while run.status in ["queued", "in_progress", "requires_action"]:
    time.sleep(1)
    run = agents.runs.get(thread_id=thread.id, run_id=run.id)
    if run.status == "requires_action" and isinstance(run.required_action, SubmitToolOutputsAction):
        tool_outputs = []
        for call in run.required_action.submit_tool_outputs.tool_calls:
            if isinstance(call, RequiredFunctionToolCall):
                output = functions.execute(call)  # SDK dispatches to the right function
                tool_outputs.append(ToolOutput(tool_call_id=call.id, output=output))
        agents.runs.submit_tool_outputs(thread_id=thread.id, run_id=run.id, tool_outputs=tool_outputs)
```

> For auto-function-call handling without manual polling, see `runs.create_and_process()` which handles `requires_action` automatically when using `FunctionTool`.

---

## Streaming Responses

Two streaming patterns: **iteration** (simple loop) and **event handler** (class-based hooks).

### Stream Iteration (simpler)

```python
from azure.ai.agents.models import MessageDeltaChunk, ThreadRun, RunStep

with agents.runs.stream(thread_id=thread.id, agent_id=agent.id) as stream:
    for event_type, event_data, _ in stream:
        if isinstance(event_data, MessageDeltaChunk):
            print(event_data.text, end="", flush=True)
        elif isinstance(event_data, ThreadRun) and event_data.status == "failed":
            print(f"Run failed: {event_data.last_error}")
```

### Event Handler (class-based, good for function tools in streaming)

```python
from typing import Any, Optional
from azure.ai.agents.models import (
    AgentEventHandler, MessageDeltaChunk, ThreadMessage, ThreadRun, RunStep,
    RequiredFunctionToolCall, SubmitToolOutputsAction, ToolOutput,
)

class MyHandler(AgentEventHandler[str]):
    def __init__(self, functions: FunctionTool):
        super().__init__()
        self.functions = functions

    def on_message_delta(self, delta: MessageDeltaChunk) -> Optional[str]:
        return delta.text  # printed/yielded to caller

    def on_thread_run(self, run: ThreadRun) -> Optional[str]:
        if run.status == "requires_action" and isinstance(run.required_action, SubmitToolOutputsAction):
            tool_outputs = []
            for call in run.required_action.submit_tool_outputs.tool_calls:
                if isinstance(call, RequiredFunctionToolCall):
                    output = self.functions.execute(call)
                    tool_outputs.append(ToolOutput(tool_call_id=call.id, output=output))
            # Re-attach handler to the continuation stream
            agents_client.runs.submit_tool_outputs_stream(
                thread_id=run.thread_id, run_id=run.id,
                tool_outputs=tool_outputs, event_handler=self
            )

    def on_error(self, data: str) -> Optional[str]:
        return f"Error: {data}"

    def on_done(self) -> Optional[str]:
        return "Done."

with agents.runs.stream(thread_id=thread.id, agent_id=agent.id,
                        event_handler=MyHandler(functions)) as stream:
    for _, _, result in stream:
        if result:
            print(result)
```

---

## MCP Server Integration

MCP lets agents call tools hosted on external Model Context Protocol servers.  
Requires `azure-ai-agents>=1.2.0b3`.

```python
from azure.ai.agents.models import McpTool, RequiredMcpToolCall, SubmitToolApprovalAction, ToolApproval

mcp_tool = McpTool(
    server_label="github",               # Friendly name for this server
    server_url="https://gitmcp.io/...",  # MCP server endpoint
    allowed_tools=[],                    # Empty = all tools allowed; or specify names
)
mcp_tool.allow_tool("search_code")       # Dynamically add an allowed tool
mcp_tool.update_headers("Authorization", "Bearer <token>")  # Auth headers if needed
# mcp_tool.set_approval_mode("never")   # Skip approval prompts (default requires approval)

agent = agents.create_agent(
    model=os.environ["MODEL_DEPLOYMENT_NAME"],
    name="mcp-agent",
    instructions="Use MCP tools to help the user.",
    tools=mcp_tool.definitions,
)

# Stream with tool_resources carrying MCP config
with agents.runs.stream(thread_id=thread.id, agent_id=agent.id,
                        tool_resources=mcp_tool.resources) as stream:
    for event_type, event_data, _ in stream:
        if isinstance(event_data, MessageDeltaChunk):
            print(event_data.text, end="")
        elif isinstance(event_data, ThreadRun) and event_data.status == "requires_action":
            # MCP tools require explicit approval by default
            if isinstance(event_data.required_action, SubmitToolApprovalAction):
                approvals = [
                    ToolApproval(tool_call_id=call.id, approve=True, headers=mcp_tool.headers)
                    for call in event_data.required_action.submit_tool_approval.tool_calls
                    if isinstance(call, RequiredMcpToolCall)
                ]
                agents.runs.submit_tool_outputs_stream(
                    thread_id=event_data.thread_id, run_id=event_data.id,
                    tool_approvals=approvals, event_handler=stream,
                )
```

See `references/mcp-advanced.md` for multiple MCP servers and header patterns.

---

## Structured Outputs

Force the agent to respond with a specific JSON schema. Best done with Pydantic models.

```python
from pydantic import BaseModel
from azure.ai.agents.models import ResponseFormatJsonSchemaType, ResponseFormatJsonSchema

class Sentiment(BaseModel):
    label: str        # "positive" | "negative" | "neutral"
    confidence: float
    summary: str

agent = agents.create_agent(
    model=os.environ["MODEL_DEPLOYMENT_NAME"],
    name="sentiment-agent",
    instructions="Analyze sentiment. Respond only with valid JSON.",
    response_format=ResponseFormatJsonSchemaType(
        json_schema=ResponseFormatJsonSchema(
            name="sentiment_result",
            description="Sentiment analysis result",
            schema=Sentiment.model_json_schema(),
        )
    ),
)

# Parse the response:
from pydantic import TypeAdapter
raw = agents.messages.get_last_message_text_by_role(thread_id=thread.id, role="assistant")
result = TypeAdapter(Sentiment).validate_json(raw.text.value)
```

---

## Multi-Tool Agents

Combine multiple tools by passing a list to `tools`. Use `ToolSet` to bundle tools with their resources cleanly.

```python
from azure.ai.agents.models import ToolSet

code_interpreter = CodeInterpreterTool(file_ids=[file.id])
file_search = FileSearchTool(vector_store_ids=[vs.id])
functions = FunctionTool(functions={get_weather})

toolset = ToolSet()
toolset.add(code_interpreter)
toolset.add(file_search)
toolset.add(functions)

agent = agents.create_agent(
    model=os.environ["MODEL_DEPLOYMENT_NAME"],
    name="multi-tool-agent",
    instructions="You can analyze data, search documents, and check weather.",
    tools=toolset.definitions,
    tool_resources=toolset.resources,
)
```

---

## Key Patterns & Tips

- **Persistent agents**: agents live until explicitly deleted; reuse with `agents.get_agent(agent_id)` across sessions
- **Thread-per-session**: create a new thread per conversation; threads accumulate all messages
- **`create_and_process` vs `create`**: `create_and_process` is a convenience that polls and dispatches function calls automatically — prefer it for simple cases; use manual polling when you need control over function dispatch
- **File cleanup**: always delete files and vector stores when done to avoid storage costs
- **`FilePurpose.AGENTS`**: required when uploading files for agent use
- **Async support**: all operations have async counterparts under `azure.ai.agents.aio`; usage mirrors sync but with `await` and `async with`

## Reference Files

- `references/mcp-advanced.md` — Multiple MCP servers, header auth, approval patterns
