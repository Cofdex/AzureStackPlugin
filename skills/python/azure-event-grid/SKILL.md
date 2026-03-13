---
name: azure-event-grid
description: >
  Azure Event Grid SDK for Python (azure-eventgrid). Use for publishing events to
  Event Grid topics, handling webhook delivery, and building event-driven integrations.
  Triggers on: "event grid", "EventGridPublisherClient", "CloudEvent", "EventGridEvent",
  "publish event", "topic endpoint", "event-driven", "webhook event", "system events".
  Always use CloudEvent schema for new code — EventGridEvent is the legacy format.
---

# Azure Event Grid SDK for Python

## Package
```bash
pip install azure-eventgrid azure-identity
```

## Two event schemas

| | CloudEvent (modern) | EventGridEvent (legacy) |
|---|---|---|
| Standard | CNCF CloudEvents v1.0 | Azure-proprietary |
| Import | `from azure.eventgrid import CloudEvent` | `from azure.eventgrid import EventGridEvent` |
| Required fields | `type`, `source` | `subject`, `event_type`, `data`, `data_version` |
| Use for | All new code | Existing systems only |

## Auth and client

```python
from azure.eventgrid import EventGridPublisherClient
from azure.identity import DefaultAzureCredential

# AAD auth (production)
client = EventGridPublisherClient(
    endpoint="https://mytopic.eastus-1.eventgrid.azure.net/api/events",
    credential=DefaultAzureCredential()
)

# AzureKeyCredential (access key)
from azure.core.credentials import AzureKeyCredential
client = EventGridPublisherClient(
    endpoint="https://mytopic.eastus-1.eventgrid.azure.net/api/events",
    credential=AzureKeyCredential("your-topic-key")
)
```

## Publish CloudEvents (recommended)

```python
from azure.eventgrid import EventGridPublisherClient, CloudEvent

events = [
    CloudEvent(
        type="order.created",           # identifies event category
        source="/order-service",        # identifies producer
        subject="order/12345",          # optional routing info
        data={"orderId": 12345, "amount": 99.99},
    ),
    CloudEvent(
        type="order.shipped",
        source="/order-service",
        subject="order/12345",
        data={"trackingNumber": "TRACK123"},
    ),
]

client.send(events)   # send(), NOT publish()
```

## Publish EventGridEvents (legacy)

```python
from azure.eventgrid import EventGridEvent

events = [
    EventGridEvent(
        subject="payments/txn-001",
        event_type="payment.processed",
        data={"amount": 150.00, "status": "completed"},
        data_version="1.0",             # REQUIRED — omitting raises error
    )
]
client.send(events)
```

## Webhook validation (system events)

When Event Grid sends a subscription validation, you must respond manually:

```python
# FastAPI webhook handler example
@app.post("/webhook")
async def handle_event(request: Request):
    body = await request.json()
    for event in body:
        if event.get("eventType") == "Microsoft.EventGrid.SubscriptionValidationEvent":
            # Return validation code to confirm subscription
            return {"validationResponse": event["data"]["validationCode"]}
        # process your custom events
```

## Async client
```python
from azure.eventgrid.aio import EventGridPublisherClient as AsyncPublisher

async with AsyncPublisher(endpoint, credential) as client:
    await client.send([CloudEvent(type="x", source="/y", data={})])
```

## Common mistakes

| ❌ Wrong | ✅ Correct |
|---|---|
| `client.publish(events)` | `client.send(events)` — only `send()` exists |
| `EventGridEvent(...)` without `data_version` | `data_version="1.0"` is **required** for EventGridEvent |
| `CloudEvent(data_version="1.0")` | CloudEvent has no `data_version` param — use `type`+`source` |
| `CloudEvent(event_type="x")` | CloudEvent uses `type=`, not `event_type=` |
| Omitting `endpoint` from constructor | `endpoint` is always required |
| Expecting auto-validation for subscriptions | Must manually return `validationResponse` in webhook handler |
