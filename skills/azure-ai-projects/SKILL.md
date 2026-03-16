---
name: azure-ai-projects
description: >
  Build AI applications using the Azure AI Projects Python SDK (azure-ai-projects) — the
  high-level Microsoft Foundry SDK. Use this skill whenever the user works with AIProjectClient,
  creates versioned agents with PromptAgentDefinition or WorkflowAgentDefinition, uses
  get_openai_client() for Responses/Conversations API, runs evaluations (evals.create,
  evals.runs.create), manages project connections (ConnectionType.AZURE_OPEN_AI), queries
  deployments or datasets or indexes, enables telemetry/tracing with AIProjectInstrumentor,
  or imports from azure.ai.projects. ALWAYS use this skill for any of these patterns. For
  low-level Thread/Run/Message agent operations, use azure-ai-agents-python instead.
---

# Azure AI Projects SDK

The `azure-ai-projects` package is the **high-level Microsoft Foundry SDK**. It gives you one
`AIProjectClient` entry point for everything in your Foundry project: versioned agents,
evaluations, connections, deployments, datasets, indexes, files, fine-tuning, and telemetry.

```
uv add "azure-ai-projects>=2.0.0"
uv add aiohttp          # async client only
```

---

## Client setup

```python
import os
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential

# Sync (context manager — preferred)
with (
    DefaultAzureCredential() as credential,
    AIProjectClient(
        endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
        credential=credential,
        # allow_preview=True  ← add this for WorkflowAgentDefinition / HostedAgentDefinition
    ) as project_client,
):
    ...
```

Async variant (requires `aiohttp`):

```python
from azure.ai.projects.aio import AIProjectClient
from azure.identity.aio import DefaultAzureCredential

async with (
    DefaultAzureCredential() as credential,
    AIProjectClient(endpoint=..., credential=credential) as project_client,
):
    ...
```

**Required env var:** `AZURE_AI_PROJECT_ENDPOINT` — the Foundry project endpoint, e.g.
`https://<account>.services.ai.azure.com/api/projects/<project>`.

---

## OpenAI-compatible client

`get_openai_client()` returns a standard `openai.OpenAI` client pre-authenticated for your
project. Use it for Responses, Conversations, Evaluations, Files, and Fine-tuning:

```python
with project_client.get_openai_client() as openai_client:
    response = openai_client.responses.create(
        model=os.environ["AZURE_AI_MODEL_DEPLOYMENT_NAME"],
        input="What is the capital of France?",
    )
    print(response.output_text)

    # Multi-turn via previous_response_id
    response2 = openai_client.responses.create(
        model=os.environ["AZURE_AI_MODEL_DEPLOYMENT_NAME"],
        input="And its population?",
        previous_response_id=response.id,
    )
```

---

## Agent Registry (`.agents`)

The `.agents` sub-client manages **versioned agents** stored in Foundry. This is different from
the azure-ai-agents SDK — here agents are registered by name and invoked via the Conversations +
Responses API rather than the Thread/Run API.

### PromptAgentDefinition — model-backed agent

```python
from azure.ai.projects.models import PromptAgentDefinition

agent = project_client.agents.create_version(
    agent_name="my-assistant",
    definition=PromptAgentDefinition(
        model=os.environ["AZURE_AI_MODEL_DEPLOYMENT_NAME"],
        instructions="You are a helpful assistant.",
    ),
)
print(f"Created: {agent.name} v{agent.version} (id={agent.id})")
```

### WorkflowAgentDefinition — multi-agent YAML workflow

Requires `allow_preview=True` on the client. The key pattern is:
1. Register all participant agents with `create_version` + `PromptAgentDefinition` **first**
2. Build a YAML string referencing those agent names via `InvokeAzureAgent`
3. Register the workflow itself with `WorkflowAgentDefinition`
4. Invoke the workflow via the Conversations + Responses API

```python
from azure.ai.projects.models import PromptAgentDefinition, WorkflowAgentDefinition

# Step 1: Create the participant agents
teacher = project_client.agents.create_version(
    agent_name="teacher-agent",
    definition=PromptAgentDefinition(
        model=os.environ["AZURE_AI_MODEL_DEPLOYMENT_NAME"],
        instructions="You ask math questions and check answers. Say [COMPLETE] when correct.",
    ),
)
student = project_client.agents.create_version(
    agent_name="student-agent",
    definition=PromptAgentDefinition(
        model=os.environ["AZURE_AI_MODEL_DEPLOYMENT_NAME"],
        instructions="You answer math questions from the teacher.",
    ),
)

# Step 2: Build the workflow YAML — reference agents by name with InvokeAzureAgent
workflow_yaml = f"""
kind: workflow
trigger:
  kind: OnConversationStart
  id: my_workflow
  actions:
    - kind: SetVariable
      id: set_input
      variable: Local.LatestMessage
      value: "=UserMessage(System.LastMessageText)"

    - kind: CreateConversation
      id: create_teacher_conv
      conversationId: Local.TeacherConvId

    - kind: CreateConversation
      id: create_student_conv
      conversationId: Local.StudentConvId

    - kind: InvokeAzureAgent
      id: student_turn
      conversationId: "=Local.StudentConvId"
      agent:
        name: {student.name}
      input:
        messages: "=Local.LatestMessage"
      output:
        messages: Local.LatestMessage

    - kind: InvokeAzureAgent
      id: teacher_turn
      conversationId: "=Local.TeacherConvId"
      agent:
        name: {teacher.name}
      input:
        messages: "=Local.LatestMessage"
      output:
        messages: Local.LatestMessage

    - kind: SendActivity
      id: send_reply
      activity: "{{Last(Local.LatestMessage).Text}}"

    - kind: SetVariable
      id: increment_turns
      variable: Local.TurnCount
      value: "=Local.TurnCount + 1"

    - kind: ConditionGroup
      id: check_done
      conditions:
        - condition: '=!IsBlank(Find("[COMPLETE]", Upper(Last(Local.LatestMessage).Text)))'
          id: is_complete
          actions:
            - kind: EndConversation
              id: end
        - condition: "=Local.TurnCount >= 4"
          id: max_turns
          actions:
            - kind: SendActivity
              id: send_timeout
              activity: "Max turns reached."
      elseActions:
        - kind: GotoAction
          id: loop_back
          actionId: student_turn
"""

# Step 3: Register the workflow
workflow = project_client.agents.create_version(
    agent_name="teacher-student-workflow",
    definition=WorkflowAgentDefinition(workflow=workflow_yaml),
)

# Step 4: Invoke via Conversations + Responses
with project_client.get_openai_client() as openai_client:
    conv = openai_client.conversations.create()
    stream = openai_client.responses.create(
        conversation=conv.id,
        extra_body={"agent_reference": {"name": workflow.name, "type": "agent_reference"}},
        input="What is 2 + 2?",
        stream=True,
    )
    for event in stream:
        if event.type == "response.completed":
            print(event.response.output_text)
    openai_client.conversations.delete(conversation_id=conv.id)

# Cleanup — delete all 3 versions
project_client.agents.delete_version(agent_name=workflow.name, agent_version=workflow.version)
project_client.agents.delete_version(agent_name=teacher.name, agent_version=teacher.version)
project_client.agents.delete_version(agent_name=student.name, agent_version=student.version)
```

### Conversations + Responses — invoke an agent

```python
with project_client.get_openai_client() as openai_client:
    # Create conversation (persists message history)
    conv = openai_client.conversations.create(
        items=[{"type": "message", "role": "user", "content": "Hello!"}]
    )

    # Invoke agent — route by name via agent_reference
    response = openai_client.responses.create(
        conversation=conv.id,
        extra_body={"agent_reference": {"name": "my-assistant", "type": "agent_reference"}},
    )
    print(response.output_text)

    # Continue the conversation
    openai_client.conversations.items.create(
        conversation_id=conv.id,
        items=[{"type": "message", "role": "user", "content": "Tell me more."}],
    )
    response2 = openai_client.responses.create(
        conversation=conv.id,
        extra_body={"agent_reference": {"name": "my-assistant", "type": "agent_reference"}},
    )

    # Streaming
    stream = openai_client.responses.create(
        conversation=conv.id,
        extra_body={"agent_reference": {"name": "my-assistant", "type": "agent_reference"}},
        input="One more question.",
        stream=True,
    )
    for event in stream:
        print(event)

    openai_client.conversations.delete(conversation_id=conv.id)

# Clean up the agent version
project_client.agents.delete_version(agent_name="my-assistant", agent_version=agent.version)
```

### Agent lifecycle

```python
# Retrieve latest version
record = project_client.agents.get(agent_name="my-assistant")
print(f"Latest: v{record.versions.latest.version}")

# Delete a specific version
project_client.agents.delete_version(agent_name="my-assistant", agent_version="1")
```

---

## Evaluations

Evaluations run via the **OpenAI client**, not `project_client.evaluations`. The pattern is:
create an eval object (defines schema + evaluators), then create runs against it with data.

```python
import time
from openai.types.evals.create_eval_jsonl_run_data_source_param import (
    CreateEvalJSONLRunDataSourceParam, SourceFileContent, SourceFileContentContent,
)
from openai.types.eval_create_params import DataSourceConfigCustom

with project_client.get_openai_client() as openai_client:
    # 1. Create eval — defines schema and evaluators
    eval_obj = openai_client.evals.create(
        name="my-quality-eval",
        data_source_config=DataSourceConfigCustom({
            "type": "custom",
            "item_schema": {
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "response": {"type": "string"},
                    "ground_truth": {"type": "string"},
                },
            },
        }),
        testing_criteria=[
            {
                "type": "azure_ai_evaluator",
                "name": "coherence",
                "evaluator_name": "builtin.coherence",
                "data_mapping": {"query": "{{item.query}}", "response": "{{item.response}}"},
                "initialization_parameters": {
                    "deployment_name": os.environ["AZURE_AI_MODEL_DEPLOYMENT_NAME"]
                },
            },
            {
                "type": "azure_ai_evaluator",
                "name": "violence",
                "evaluator_name": "builtin.violence",
                "data_mapping": {"query": "{{item.query}}", "response": "{{item.response}}"},
                "initialization_parameters": {
                    "deployment_name": os.environ["AZURE_AI_MODEL_DEPLOYMENT_NAME"]
                },
            },
        ],
    )

    # 2. Create a run with inline data
    run = openai_client.evals.runs.create(
        eval_id=eval_obj.id,
        name="my-run",
        data_source=CreateEvalJSONLRunDataSourceParam(
            type="jsonl",
            source=SourceFileContent(
                type="file_content",
                content=[
                    SourceFileContentContent(item={
                        "query": "What is the capital of France?",
                        "response": "Paris is the capital of France.",
                        "ground_truth": "Paris",
                    }),
                ],
            ),
        ),
    )

    # 3. Poll for completion
    while True:
        run = openai_client.evals.runs.retrieve(run_id=run.id, eval_id=eval_obj.id)
        if run.status in ("completed", "failed"):
            break
        time.sleep(5)

    # 4. Read output items and report URL
    for item in openai_client.evals.runs.output_items.list(run_id=run.id, eval_id=eval_obj.id):
        print(item)
    print(f"Report: {run.report_url}")

    openai_client.evals.delete(eval_id=eval_obj.id)
```

### Built-in evaluator names

| `evaluator_name` | What it measures |
|---|---|
| `builtin.coherence` | Logical flow of response |
| `builtin.violence` | Violent content (safety) |
| `builtin.f1_score` | Token overlap with ground truth |
| `builtin.similarity` | Semantic similarity to ground truth |
| `builtin.rouge_score` | ROUGE n-gram overlap |
| `builtin.bleu_score` | BLEU translation quality |
| `builtin.meteor_score` | METEOR translation quality |
| `builtin.gleu_score` | GLEU sentence-level quality |

---

## Connections (`.connections`)

```python
from azure.ai.projects.models import ConnectionType

# List all connections
for conn in project_client.connections.list():
    print(conn)

# Filter by type
for conn in project_client.connections.list(connection_type=ConnectionType.AZURE_OPEN_AI):
    print(conn)

# Get by name (without credentials)
conn = project_client.connections.get("my-search-connection")

# Get with credentials (e.g., API key or token)
conn = project_client.connections.get("my-search-connection", include_credentials=True)

# Get the default connection of a type
conn = project_client.connections.get_default(
    connection_type=ConnectionType.AZURE_OPEN_AI,
    include_credentials=True,
)
```

**`ConnectionType` values:** `AZURE_OPEN_AI`, `AZURE_AI_SEARCH`, `AZURE_BLOB_STORAGE`,
`CUSTOM`, `API_KEY`, `SERVERLESS`, `MANAGED_IDENTITY`, and others.

---

## Deployments (`.deployments`)

```python
from azure.ai.projects.models import ModelDeployment

# List all deployed models
for dep in project_client.deployments.list():
    print(dep)

# Filter by publisher or model name
for dep in project_client.deployments.list(model_publisher="Microsoft", model_name="Phi-4"):
    print(dep)

# Get a specific deployment
dep = project_client.deployments.get("gpt-4o-deployment")
if isinstance(dep, ModelDeployment):
    print(f"{dep.name}: {dep.model_name} v{dep.model_version} by {dep.model_publisher}")
    print(f"Capabilities: {dep.capabilities}")
```

---

## Datasets (`.datasets`)

Datasets are versioned file collections stored in Azure Blob Storage via a connection.

```python
# Upload a single file as a new dataset version
ds = project_client.datasets.upload_file(
    name="my-dataset",
    version="1",
    file_path="./data/eval_data.jsonl",
    connection_name="my-blob-connection",
)

# Upload a folder
ds = project_client.datasets.upload_folder(
    name="my-dataset",
    version="2",
    folder="./data/",
    connection_name="my-blob-connection",
)

# Get credentials (SAS URL etc.)
creds = project_client.datasets.get_credentials(name="my-dataset", version="1")

# List all datasets (latest versions)
for ds in project_client.datasets.list():
    print(ds)

# List all versions of a specific dataset
for ds in project_client.datasets.list_versions(name="my-dataset"):
    print(ds)

# Delete a version
project_client.datasets.delete(name="my-dataset", version="1")
```

---

## Indexes (`.indexes`)

Indexes connect to Azure AI Search resources for RAG workflows.

```python
from azure.ai.projects.models import AzureAISearchIndex

# Register (or update) an AI Search index
idx = project_client.indexes.create_or_update(
    name="my-index",
    version="1",
    index=AzureAISearchIndex(
        connection_name="my-search-connection",
        index_name="product-catalog",
    ),
)

# Get a specific version
idx = project_client.indexes.get(name="my-index", version="1")

# List latest versions
for idx in project_client.indexes.list():
    print(idx)

# Delete
project_client.indexes.delete(name="my-index", version="1")
```

---

## Files and Fine-tuning (via OpenAI client)

```python
with project_client.get_openai_client() as openai_client:
    # Upload a file
    with open("training.jsonl", "rb") as f:
        uploaded = openai_client.files.create(file=f, purpose="fine-tune")

    # Wait for processing
    processed = openai_client.files.wait_for_processing(uploaded.id)

    # List all files
    for f in openai_client.files.list():
        print(f.id, f.filename, f.status)

    # Fine-tuning job
    job = openai_client.fine_tuning.jobs.create(
        training_file=processed.id,
        model="gpt-4o-mini",
        method={"type": "supervised", "supervised": {"hyperparameters": {"n_epochs": 3}}},
        extra_body={"trainingType": "GlobalStandard"},
    )
```

---

## Telemetry and Tracing

### Get Application Insights connection string

```python
conn_str = project_client.telemetry.get_application_insights_connection_string()
```

### Enable tracing (experimental)

```bash
# Required env var before any import
AZURE_EXPERIMENTAL_ENABLE_GENAI_TRACING=true
```

```bash
uv add opentelemetry-sdk azure-core-tracing-opentelemetry azure-monitor-opentelemetry
```

```python
from azure.monitor.opentelemetry import configure_azure_monitor

configure_azure_monitor(
    connection_string=project_client.telemetry.get_application_insights_connection_string()
)
# All subsequent SDK calls are now traced to Azure Monitor
```

---

## When to use `azure-ai-projects` vs `azure-ai-agents`

| Task | Use |
|---|---|
| Create/register a versioned agent | `azure-ai-projects` (`.agents.create_version`) |
| Multi-turn conversation via Responses API | `azure-ai-projects` (`get_openai_client` + `conversations` + `responses`) |
| Multi-agent YAML workflow | `azure-ai-projects` (`WorkflowAgentDefinition`) |
| Run evaluations on datasets | `azure-ai-projects` (`openai_client.evals`) |
| Manage connections / deployments / datasets / indexes | `azure-ai-projects` |
| Low-level Thread + Run + Message operations | `azure-ai-agents` (separate SDK) |
| Agent with code interpreter / file search / Bing tools | Either; `azure-ai-agents` for Thread/Run pattern; `azure-ai-projects` for Responses pattern |

---

## Environment variables

| Variable | Required | Description |
|---|---|---|
| `AZURE_AI_PROJECT_ENDPOINT` | ✅ | Foundry project endpoint URL |
| `AZURE_AI_MODEL_DEPLOYMENT_NAME` | Common | Model deployment name for agents/eval |
| `AZURE_EXPERIMENTAL_ENABLE_GENAI_TRACING` | Tracing | Set to `true` to enable OTel tracing |
| `CONNECTION_NAME` | Connections sample | Name of a project connection |
