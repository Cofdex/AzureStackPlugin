---
name: azure-queue-storage
description: >
  Azure Queue Storage SDK for Python (azure-storage-queue). Use for sending, receiving,
  and deleting messages from Azure Storage queues. Triggers on: "queue storage",
  "QueueClient", "QueueServiceClient", "receive_messages", "send_message",
  "pop_receipt", "azure-storage-queue". CRITICAL: delete_message requires BOTH
  message_id AND pop_receipt. pop_receipt changes every time you receive a message.
  receive_messages returns an iterator, not a list.
---

# Azure Queue Storage SDK for Python

## Package
```bash
pip install azure-storage-queue azure-identity
```

## Client setup

```python
from azure.storage.queue import QueueServiceClient, QueueClient
from azure.identity import DefaultAzureCredential

# AAD auth (production)
service = QueueServiceClient(
    account_url="https://myaccount.queue.core.windows.net",
    credential=DefaultAzureCredential(),
)

# Connection string (dev)
service = QueueServiceClient.from_connection_string("DefaultEndpointsProtocol=https;...")

# Direct queue client
queue = QueueClient(
    account_url="https://myaccount.queue.core.windows.net",
    queue_name="my-queue",
    credential=DefaultAzureCredential(),
)
# or
queue = service.get_queue_client("my-queue")
```

## Queue management

```python
# Create queue
queue.create_queue()

# List queues
for q in service.list_queues():
    print(q.name)

# Delete queue
queue.delete_queue()
```

## Send messages

```python
# Send string message
queue.send_message("hello world")

# Send with visibility timeout (invisible for 30s after send)
queue.send_message("delayed", visibility_timeout=30)

# Send with TTL (message expires after 1 hour)
queue.send_message("expiring", time_to_live=3600)
```

## Receive and delete messages

```python
# receive_messages returns an iterator — NOT a list
messages = queue.receive_messages(max_messages=10, visibility_timeout=30)

for msg in messages:
    print(msg.id)        # message ID
    print(msg.content)   # message body string
    
    # Process the message
    process(msg.content)
    
    # MUST delete with BOTH id AND pop_receipt
    # pop_receipt is a temporary token that changes on every receive
    queue.delete_message(msg.id, msg.pop_receipt)
```

## Peek (non-destructive read)

```python
# Peek does NOT lock messages (no pop_receipt)
peeked = queue.peek_messages(max_messages=5)
for msg in peeked:
    print(msg.content)
# Cannot delete from peek — must receive first
```

## Update message (extend visibility / change content)

```python
messages = queue.receive_messages(max_messages=1, visibility_timeout=30)
for msg in messages:
    # Extend visibility by another 60 seconds while processing
    updated = queue.update_message(
        msg.id,
        msg.pop_receipt,
        visibility_timeout=60,      # reset the clock
        content=msg.content,        # keep same content (or change it)
    )
    # update_message returns a new pop_receipt — use it for delete
    queue.delete_message(msg.id, updated.pop_receipt)
```

## Queue properties

```python
props = queue.get_queue_properties()
print(props.approximate_message_count)   # approximate count
```

## Common mistakes

| ❌ Wrong | ✅ Correct |
|---|---|
| `queue.delete_message(msg.id)` | `queue.delete_message(msg.id, msg.pop_receipt)` — both required |
| `list(queue.receive_messages())` without iterating | Iterate with `for msg in queue.receive_messages()` |
| Using pop_receipt from `peek_messages` | Peek returns no pop_receipt — must `receive_messages` to delete |
| Reusing stale pop_receipt | pop_receipt changes on each receive — use the latest one |
| `queue.receive_message()` (singular) | `queue.receive_messages(max_messages=1)` |
| Deleting without processing (messages lost) | Process first, then delete |
