# MCP Advanced Patterns

## Multiple MCP Servers

```python
from azure.ai.agents.models import McpTool

# Create separate McpTool instances, one per server
github_mcp = McpTool(
    server_label="github",
    server_url="https://gitmcp.io/Azure/azure-rest-api-specs",
    allowed_tools=["search_code", "get_file_contents"],
)

docs_mcp = McpTool(
    server_label="docs",
    server_url="https://your-docs-mcp-server.example.com",
    allowed_tools=[],  # allow all tools on this server
)

# Merge tool definitions from all servers
all_tool_definitions = github_mcp.definitions + docs_mcp.definitions

agent = agents.create_agent(
    model=os.environ["MODEL_DEPLOYMENT_NAME"],
    name="multi-mcp-agent",
    instructions="Use MCP tools from GitHub and docs servers.",
    tools=all_tool_definitions,
)
```

## Header-Based Authentication

Many MCP servers use API key headers or OAuth Bearer tokens:

```python
mcp_tool = McpTool(
    server_label="private-api",
    server_url="https://internal.example.com/mcp",
    allowed_tools=[],
)

# Set a static header
mcp_tool.update_headers("X-API-Key", os.environ["MCP_API_KEY"])

# Or Bearer token
mcp_tool.update_headers("Authorization", f"Bearer {token}")

# Pass headers at stream time via tool_resources and ToolApproval
with agents.runs.stream(
    thread_id=thread.id,
    agent_id=agent.id,
    tool_resources=mcp_tool.resources,
) as stream:
    ...
```

## Approval Mode

By default MCP tool calls require explicit approval (`requires_action` with `SubmitToolApprovalAction`).

```python
# Disable approval (auto-approve everything) — useful for trusted internal servers
mcp_tool.set_approval_mode("never")

# Default (require approval for each tool call)
mcp_tool.set_approval_mode("always")
```

When approval is required, the run pauses at `requires_action`. You must submit approvals and re-attach your stream:

```python
from azure.ai.agents.models import (
    SubmitToolApprovalAction, RequiredMcpToolCall, ToolApproval
)

if (event_data.status == "requires_action" and
        isinstance(event_data.required_action, SubmitToolApprovalAction)):
    tool_calls = event_data.required_action.submit_tool_approval.tool_calls
    approvals = []
    for call in tool_calls:
        if isinstance(call, RequiredMcpToolCall):
            print(f"Approving: {call.function.name}({call.function.arguments})")
            approvals.append(ToolApproval(
                tool_call_id=call.id,
                approve=True,
                headers=mcp_tool.headers,  # pass auth headers with each approval
            ))

    # submit_tool_outputs_stream re-attaches the existing stream handler
    agents.runs.submit_tool_outputs_stream(
        thread_id=event_data.thread_id,
        run_id=event_data.id,
        tool_approvals=approvals,
        event_handler=stream,
    )
```

## Inspecting Available MCP Tools

When `allowed_tools=[]`, the agent can see all tools on the server. To discover what's available:

```python
# List tools from the mcp_tool object after server connection
print(mcp_tool.allowed_tools)  # empty means all are allowed

# To restrict dynamically:
mcp_tool.allow_tool("search_code")
mcp_tool.allow_tool("get_file")
# mcp_tool.allowed_tools is now ["search_code", "get_file"]
```

## MCP with Non-Streaming Runs

MCP tools work with `create_and_process` when `approval_mode="never"`:

```python
mcp_tool.set_approval_mode("never")

agent = agents.create_agent(
    model=os.environ["MODEL_DEPLOYMENT_NAME"],
    name="mcp-agent",
    tools=mcp_tool.definitions,
)
thread = agents.threads.create()
agents.messages.create(thread_id=thread.id, role="user", content="Search for auth examples.")

run = agents.runs.create_and_process(
    thread_id=thread.id,
    agent_id=agent.id,
    tool_resources=mcp_tool.resources,
)
```

When approval is required you must use manual polling or streaming to handle the `requires_action` state.
