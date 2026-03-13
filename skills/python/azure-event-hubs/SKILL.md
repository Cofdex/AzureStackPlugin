---
name: azure-event-hubs
description: >
  Azure Event Hubs SDK for Python (azure-eventhub). Use for high-throughput event
  streaming, IoT telemetry ingestion, and Kafka-compatible event pipelines. Triggers on:
  "event hubs", "EventHubProducerClient", "EventHubConsumerClient", "EventData",
  "EventDataBatch", "send_batch", "partition", "consumer group", "checkpoint",
  "streaming events", "telemetry ingestion". Also use when building real-time data
  pipelines or connecting to Azure Event Hubs from Python.
---

# Azure Event Hubs SDK for Python

## Package
```bash
pip install azure-eventhub azure-eventhub-checkpointstoreblob azure-identity
```

## Main clients
- `EventHubProducerClient` — sends event batches
- `EventHubConsumerClient` — receives events with checkpoint support
- `EventData` — single event
- `EventDataBatch` — container for batched events (enforces size limits)

## Auth

```python
from azure.eventhub import EventHubProducerClient
from azure.identity import DefaultAzureCredential

# AAD
producer = EventHubProducerClient(
    fully_qualified_namespace="myns.servicebus.windows.net",
    eventhub_name="myhub",
    credential=DefaultAzureCredential()
)

# Connection string
producer = EventHubProducerClient.from_connection_string(
    conn_str="Endpoint=sb://myns.servicebus.windows.net/;EntityPath=myhub;SharedAccessKeyName=...;SharedAccessKey=..."
)
```

## Send events

```python
from azure.eventhub import EventHubProducerClient, EventData

with EventHubProducerClient.from_connection_string(conn_str) as producer:
    # Always create a batch first — enforces 1 MB size limit
    batch = producer.create_batch()
    batch.add(EventData(body="event 1"))
    batch.add(EventData(body="event 2"))
    producer.send_batch(batch)  # send_batch(), NOT send()
```

### Partition key routing
```python
batch = producer.create_batch(partition_key="customer-123")
# All events in this batch go to the same partition
```

## Receive events with checkpointing

```python
from azure.eventhub import EventHubConsumerClient
from azure.eventhub.extensions.checkpointstoreblobaio import BlobCheckpointStore

checkpoint_store = BlobCheckpointStore.from_connection_string(
    blob_conn_str, container_name="checkpoints"
)

consumer = EventHubConsumerClient.from_connection_string(
    conn_str,
    consumer_group="$Default",   # case-sensitive: $Default not $default
    eventhub_name="myhub",
    checkpoint_store=checkpoint_store,
)

def on_event(partition_context, event):
    # Callback signature: (partition_context, event) — both required
    print(f"Partition {partition_context.partition_id}: {event.body_as_str()}")
    partition_context.update_checkpoint(event)   # checkpoint after processing

with consumer:
    consumer.receive(
        on_event=on_event,
        starting_position="-1",  # "-1" = beginning, "@latest" = new only
    )
```

## EventData properties
```python
event = EventData(body="payload")
event.properties = {"sensor": "temp-1", "unit": "C"}  # custom properties

# Reading received events
event.body_as_str()       # decode body as UTF-8 string
event.body_as_json()      # decode body as JSON dict
event.sequence_number     # position in partition
event.offset              # offset string
event.enqueued_time       # datetime when enqueued
event.partition_key       # routing key if set
```

## Async client
```python
from azure.eventhub.aio import EventHubProducerClient as AsyncProducer

async with AsyncProducer.from_connection_string(conn_str) as producer:
    async with producer.create_batch() as batch:
        batch.add(EventData("async event"))
    await producer.send_batch(batch)
```

## Common mistakes

| ❌ Wrong | ✅ Correct |
|---|---|
| `producer.send(event)` | `producer.send_batch(batch)` — must use batch |
| `on_event(event)` callback | `on_event(partition_context, event)` — two args always |
| `consumer_group="$default"` | `consumer_group="$Default"` — case-sensitive |
| `receive_batch()` method | Does not exist — use `receive(on_event=...)` |
| `EventHubClient` unified client | Use `EventHubProducerClient` or `EventHubConsumerClient` |
| Adding events to batch without catching `ValueError` | `batch.add()` raises `ValueError` when full — handle it |
