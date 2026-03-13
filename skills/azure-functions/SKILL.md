---
name: azure-functions
description: >
  Azure Functions Python SDK (v2 programming model). Use for writing serverless functions
  with HTTP, timer, queue, blob, Service Bus, and Event Hub triggers; output bindings;
  and async function patterns. Triggers on: "azure functions", "FunctionApp", "func.route",
  "timer trigger", "queue trigger", "blob trigger", "http trigger", "serverless", "func.HttpResponse",
  "azure-functions". CRITICAL: HTTP trigger is @app.route() not @app.http_trigger().
  req.get_body() is a method, not an attribute. Never add azure-functions-worker to requirements.txt.
---

# Azure Functions Python SDK (v2 Programming Model)

## Package
```bash
pip install azure-functions
# DO NOT add azure-functions-worker — it's platform-managed, not user-installed
```

## App initialization

```python
import azure.functions as func
import logging

# auth_level applies to all HTTP routes by default
app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)
# Options: ANONYMOUS, FUNCTION, ADMIN
```

## HTTP Trigger

```python
@app.route(route="hello", methods=["GET", "POST"])   # @app.route, NOT @app.http_trigger
def http_handler(req: func.HttpRequest) -> func.HttpResponse:
    # Query param
    name = req.params.get("name", "World")           # .params.get(), not req.args

    # JSON body
    try:
        body = req.get_json()                        # method call, NOT req.body or req.json
    except ValueError:
        return func.HttpResponse("Invalid JSON", status_code=400)

    # Raw bytes body
    raw = req.get_body()                             # method call, returns bytes

    # Route parameters (e.g., route="items/{id}")
    item_id = req.route_params.get("id")

    return func.HttpResponse(
        body='{"result": "ok"}',                     # body first positional arg
        status_code=200,                             # status_code, NOT status
        mimetype="application/json",
        headers={"X-Custom": "value"},
    )
```

## Timer Trigger

```python
@app.timer_trigger(arg_name="timer", schedule="0 */5 * * * *")  # cron: every 5 min
def timer_handler(timer: func.TimerRequest) -> None:
    if timer.past_due:                               # timer.past_due, NOT timer.next_execution
        logging.warning("Timer past due!")
    logging.info(f"Triggered at: {timer.triggered_at}")
```

## Queue Trigger + Output Binding

```python
@app.queue_trigger(
    arg_name="msg",
    queue_name="myqueue",                            # queue_name, NOT queue
    connection="AzureWebJobsStorage",
)
@app.queue_output(
    arg_name="output_queue",
    queue_name="processed",
    connection="AzureWebJobsStorage",
)
def queue_handler(msg: func.QueueMessage, output_queue: func.Out[str]) -> None:
    data = msg.get_json()
    output_queue.set('{"status": "done"}')           # func.Out.set() to write output
```

## Blob Trigger + Blob Output

```python
@app.blob_trigger(
    arg_name="input_blob",
    path="uploads/{name}",
    connection="AzureWebJobsStorage",
)
@app.blob_output(
    arg_name="output_blob",
    path="processed/{name}",
    connection="AzureWebJobsStorage",
)
def blob_handler(input_blob: func.InputStream, output_blob: func.Out[bytes]) -> None:
    content = input_blob.read()
    output_blob.set(content)
```

## Service Bus Triggers

```python
# Queue trigger
@app.service_bus_queue_trigger(
    arg_name="msg",
    connection="AzureWebJobsServiceBus",
    queue_name="orders",
)
def sb_queue_handler(msg: func.ServiceBusMessage) -> None:
    body = msg.get_json()
    logging.info(f"Order: {body}")

# Topic trigger
@app.service_bus_topic_trigger(
    arg_name="msg",
    connection="AzureWebJobsServiceBus",
    topic_name="events",
    subscription_name="my-subscription",             # subscription_name required for topics
)
def sb_topic_handler(msg: func.ServiceBusMessage) -> None:
    body = msg.get_json()
```

## Async functions

```python
import asyncio

@app.route(route="async-endpoint", methods=["GET"])
async def async_handler(req: func.HttpRequest) -> func.HttpResponse:
    result = await do_async_work()
    return func.HttpResponse(result)

async def do_async_work() -> str:
    await asyncio.sleep(0.1)
    return "done"
```

## local.settings.json (local dev)

```json
{
  "IsEncrypted": false,
  "Values": {
    "AzureWebJobsStorage": "UseDevelopmentStorage=true",
    "FUNCTIONS_WORKER_RUNTIME": "python"
  }
}
```

## requirements.txt

```
azure-functions
# Only user dependencies go here
# Do NOT include: azure-functions-worker, azure-functions-host
```

## Common mistakes

| ❌ Wrong | ✅ Correct |
|---|---|
| `@app.http_trigger(route="...")` | `@app.route(route="...")` |
| `queue_trigger(queue="q")` | `queue_trigger(queue_name="q")` |
| `req.body` (attribute) | `req.get_body()` (method) |
| `req.json` | `req.get_json()` |
| `HttpResponse(status=400)` | `HttpResponse(body="...", status_code=400)` |
| `func.FunctionApp()` no auth_level | `func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)` |
| `timer.next_execution` | `timer.past_due` |
| `azure-functions-worker` in requirements.txt | Remove it — platform-managed |
| `output.value = "..."` | `output.set("...")` — use `.set()` method |
