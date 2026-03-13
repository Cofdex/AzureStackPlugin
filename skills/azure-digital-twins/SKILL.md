---
name: azure-digital-twins
description: >
  Azure Digital Twins SDK for Python (azure-digitaltwins-core). Use for creating and
  managing digital twin instances, models (DTDL), relationships, and querying the twin
  graph. Triggers on: "digital twins", "DigitalTwinsClient", "upsert_digital_twin",
  "DTDL", "twin model", "twin relationship", "query twins", "IoT digital twin",
  "Azure Digital Twins". CRITICAL: method is upsert_digital_twin (not create), JSON
  Patch for updates, relationships need both endpoints to exist.
---

# Azure Digital Twins SDK for Python

## Package
```bash
pip install azure-digitaltwins-core azure-identity
```

## Client

```python
from azure.digitaltwins.core import DigitalTwinsClient
from azure.identity import DefaultAzureCredential

client = DigitalTwinsClient(
    endpoint="https://myinstance.api.eus.digitaltwins.azure.net",
    credential=DefaultAzureCredential(),
)
```

## Models (DTDL)

```python
# Upload a DTDL model
model_json = [
    {
        "@id": "dtmi:com:example:Room;1",    # version number (;1) is required
        "@type": "Interface",
        "@context": "dtmi:dtdl:context;2",
        "displayName": "Room",
        "contents": [
            {"@type": "Property", "name": "Temperature", "schema": "double"},
            {"@type": "Property", "name": "Humidity",    "schema": "double"},
            {"@type": "Telemetry", "name": "Motion",     "schema": "boolean"},
        ],
    }
]

client.create_models(model_json)

# Get a model
model = client.get_model("dtmi:com:example:Room;1")
print(model.id, model.model)  # id, dtdl dict

# List models
for m in client.list_models():
    print(m.id)

# Decommission (disable) a model
client.decommission_model("dtmi:com:example:Room;1")

# Delete a model (only if no twins use it)
client.delete_model("dtmi:com:example:Room;1")
```

## Twins (CRUD)

```python
# Create or replace twin — method is upsert_digital_twin, NOT create_or_replace
twin = {
    "$metadata": {"$model": "dtmi:com:example:Room;1"},
    "Temperature": 22.5,
    "Humidity": 45.0,
}
client.upsert_digital_twin("room-001", twin)

# Read twin
twin = client.get_digital_twin("room-001")
print(twin["Temperature"])
print(twin["$metadata"]["$model"])   # model ID

# Update twin with JSON Patch — only add/replace/remove supported
from azure.core.exceptions import ResourceModifiedError

patch = [
    {"op": "replace", "path": "/Temperature", "value": 24.0},
    {"op": "add",     "path": "/Humidity",    "value": 50.0},
    {"op": "remove",  "path": "/OldProperty"},
]
client.update_digital_twin("room-001", patch)

# Update with optimistic concurrency (etag)
etag = twin["$etag"]
try:
    client.update_digital_twin("room-001", patch, if_match=etag)
except ResourceModifiedError:
    # Someone else updated the twin; re-read and retry
    twin = client.get_digital_twin("room-001")

# Delete twin (remove all relationships first!)
client.delete_digital_twin("room-001")
```

## Relationships

```python
# Create relationship (both source and target twins must already exist)
relationship = {
    "$relationshipId": "room-001-contains-sensor-a",
    "$sourceId":       "room-001",
    "$relationshipName": "contains",
    "$targetId":       "sensor-a",
    "since": "2024-01-01",
}
client.upsert_relationship(
    digital_twin_id="room-001",
    relationship_id="room-001-contains-sensor-a",
    relationship=relationship,
)

# List outgoing relationships from a twin
for rel in client.list_relationships("room-001"):
    print(rel["$relationshipName"], "→", rel["$targetId"])

# List incoming relationships
for rel in client.list_incoming_relationships("sensor-a"):
    print(rel["$sourceId"], "→", rel["$relationshipName"])

# Get specific relationship
rel = client.get_relationship("room-001", "room-001-contains-sensor-a")

# Update relationship (JSON Patch)
patch = [{"op": "replace", "path": "/since", "value": "2024-06-01"}]
client.update_relationship("room-001", "room-001-contains-sensor-a", patch)

# Delete relationship
client.delete_relationship("room-001", "room-001-contains-sensor-a")
```

## Query the twin graph

```python
# query_twins() returns ItemPaged — must iterate
results = client.query_twins("SELECT * FROM DIGITALTWINS")
for twin in results:
    print(twin["$dtId"], twin.get("Temperature"))

# Filter by model
results = client.query_twins(
    "SELECT * FROM DIGITALTWINS T WHERE IS_OF_MODEL(T, 'dtmi:com:example:Room;1')"
)

# Filter by property
results = client.query_twins(
    "SELECT * FROM DIGITALTWINS T WHERE T.Temperature > 25"
)

# Traverse relationships
results = client.query_twins("""
    SELECT Room, Sensor FROM DIGITALTWINS Room
    JOIN Sensor RELATED Room.contains
    WHERE Room.$dtId = 'room-001'
""")
for row in results:
    print(row["Room"]["$dtId"], row["Sensor"]["$dtId"])
```

## Telemetry

```python
import json
from datetime import datetime, timezone

# Publish telemetry (does not update twin properties)
client.publish_telemetry(
    digital_twin_id="sensor-a",
    payload=json.dumps({"Motion": True, "timestamp": datetime.now(timezone.utc).isoformat()}),
    message_id="unique-msg-id",
)

# Publish telemetry on a component
client.publish_component_telemetry(
    digital_twin_id="device-001",
    component_path="sensor",
    payload=json.dumps({"Temperature": 23.1}),
)
```

## Common mistakes

| ❌ Wrong | ✅ Correct |
|---|---|
| `client.create_digital_twin(...)` | `client.upsert_digital_twin(id, twin_dict)` |
| `client.create_or_replace_digital_twin(...)` | `client.upsert_digital_twin(...)` |
| JSON Patch with `"op": "update"` | Only `add`, `replace`, `remove` are valid ops |
| `client.query_twins(...)` used as a list directly | Returns `ItemPaged` — must iterate with `for` loop |
| DTDL `@id` without version: `"dtmi:com:example:Room"` | Must include version: `"dtmi:com:example:Room;1"` |
| Creating relationship before target twin exists | Create both twins first, then relationships |
| Deleting a twin with relationships attached | Delete all relationships first |
| `patch = {"op": "replace", ...}` (dict, not list) | JSON Patch must be a list of operations |
| `client.update_digital_twin("id", {"Temperature": 25})` | Must use JSON Patch list, not property dict |
