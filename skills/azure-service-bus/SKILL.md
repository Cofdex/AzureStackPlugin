---
name: azure-service-bus
description: >
  Azure Service Bus SDK for Python (azure-servicebus). Use for reliable message queuing,
  pub/sub with topics/subscriptions, and decoupled async communication. Triggers on:
  "service bus", "ServiceBusClient", "send_messages", "receive_messages", "queue",
  "topic", "subscription", "dead letter", "message broker", "ServiceBusMessage",
  "complete_message", "abandon_message". Also use when implementing message-driven
  architectures, background job queues, or producer/consumer patterns in Python.
---

# Azure Service Bus SDK for Python

## Package
```bash
uv add azure-servicebus azure-identity
```

## Client hierarchy
- `ServiceBusClient` — factory, creates senders/receivers
- `ServiceBusSender` — sends messages to queue or topic
- `ServiceBusReceiver` — receives from queue or topic subscription
- `ServiceBusMessage` — message you create to send
- `ServiceBusReceivedMessage` — message you get back (different class!)

## Auth

```python
from azure.servicebus import ServiceBusClient
from azure.identity import DefaultAzureCredential

# AAD (production)
client = ServiceBusClient(
    fully_qualified_namespace="myns.servicebus.windows.net",
    credential=DefaultAzureCredential()
)

# Connection string (dev/test)
client = ServiceBusClient.from_connection_string(
    conn_str="Endpoint=sb://myns.servicebus.windows.net/;SharedAccessKeyName=...;SharedAccessKey=..."
)
```

## Core patterns

### Send messages
```python
from azure.servicebus import ServiceBusClient, ServiceBusMessage

with ServiceBusClient.from_connection_string(conn_str) as client:
    sender = client.get_queue_sender(queue_name="orders")
    # send_messages() — always plural, accepts single or list
    sender.send_messages([
        ServiceBusMessage(body="Order 1"),
        ServiceBusMessage(body="Order 2"),
    ])
    sender.close()
```

### Receive and complete messages
```python
with client.get_queue_receiver(queue_name="orders", max_wait_time=5) as receiver:
    for message in receiver.receive_messages(max_message_count=10, max_wait_time=5):
        try:
            process(str(message.body))
            receiver.complete_message(message)   # acknowledge
        except Exception:
            receiver.abandon_message(message)    # return to queue
```

### Topic / subscription pattern
```python
# Send to topic
sender = client.get_topic_sender(topic_name="events")
sender.send_messages([ServiceBusMessage(body="event")])

# Receive from subscription
receiver = client.get_subscription_receiver(
    topic_name="events",
    subscription_name="processor"
)
```

### Dead letter
```python
receiver.dead_letter_message(
    message,
    reason="InvalidFormat",
    error_description="Parsing failed"
)
```

### Schedule delayed delivery
```python
from datetime import datetime, timedelta, timezone
future = datetime.now(timezone.utc) + timedelta(minutes=5)
sender.schedule_messages([msg], scheduled_enqueue_time=future)
```

### Async client
```python
from azure.servicebus.aio import ServiceBusClient as AsyncServiceBusClient

async with AsyncServiceBusClient(...) as client:
    async with client.get_queue_sender(queue_name="q") as sender:
        await sender.send_messages(ServiceBusMessage(body="hello"))
```

## Message properties
```python
msg = ServiceBusMessage(
    body="payload",
    subject="orders/created",                    # optional label
    message_id="unique-id",                      # idempotency key
    content_type="application/json",
    application_properties={"priority": "high"}, # custom key-value headers
    time_to_live=timedelta(minutes=30),
)
```

## Common mistakes

| ❌ Wrong | ✅ Correct |
|---|---|
| `sender.send_message(msg)` | `sender.send_messages([msg])` — always plural |
| `receiver.receive_message()` | `receiver.receive_messages(...)` — always plural, returns list |
| `ServiceBusAsyncClient` | `from azure.servicebus.aio import ServiceBusClient` |
| `receiver.get_message()` | Does not exist — use `receive_messages()` |
| Forget to `complete_message()` | Message stays locked and re-delivered after lock timeout |
| `ServiceBusClient(credential=cred)` | Must include `fully_qualified_namespace=` with credential auth |
