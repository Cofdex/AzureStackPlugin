---
name: azure-data-tables
description: >
  Azure Tables SDK for Python — NoSQL key-value storage using azure-data-tables, covering both
  Azure Storage Tables and Cosmos DB Tables API. Use this skill whenever the user needs to
  work with table storage entities, including client setup with multiple auth methods,
  entity CRUD operations, OData query filters, batch/transaction operations, or UpdateMode
  strategies. Triggers on: "table storage", "TableServiceClient", "TableClient", "entities",
  "PartitionKey", "RowKey", "azure-data-tables", "table entities", "submit_transaction",
  "OData filter", "upsert entity", "query entities".
---

# Azure Tables SDK for Python

Covers both **Azure Storage Tables** and **Cosmos DB Tables API** — they share the same SDK.

## Installation & Imports

```python
uv add azure-data-tables azure-identity
```

```python
from azure.data.tables import (
    TableServiceClient,
    TableClient,
    UpdateMode,
    TableTransactionError,
)
from azure.core.credentials import AzureNamedKeyCredential, AzureSasCredential
from azure.core.exceptions import ResourceNotFoundError, ResourceExistsError, HttpResponseError
from azure.identity import DefaultAzureCredential
```

## Client Construction

Two clients to know:
- **`TableServiceClient`** — service-level: create/delete/list tables
- **`TableClient`** — table-level: CRUD on entities

### Production (DefaultAzureCredential / RBAC)
```python
# Azure Storage Tables
service = TableServiceClient(
    endpoint="https://<account>.table.core.windows.net/",
    credential=DefaultAzureCredential(),
)

# Cosmos DB Tables API (different endpoint format)
service = TableServiceClient(
    endpoint="https://<account>.table.cosmosdb.azure.com:443/",
    credential=DefaultAzureCredential(),
)
```

### Connection string (dev / local)
```python
service = TableServiceClient.from_connection_string(
    conn_str=os.environ["AZURE_STORAGE_CONNECTION_STRING"]
)

# Azurite (local emulator, port 10002)
service = TableServiceClient.from_connection_string(
    "DefaultEndpointsProtocol=http;AccountName=devstoreaccount1;"
    "AccountKey=Eby8vdM02xNOcqFlqUwJPLlmEtlCDXJ1OUzFT50uSRZ6IFsuFq2UVErCz4I6tq/K1SZFPTOtr/KBHBeksoGMGw==;"
    "TableEndpoint=http://127.0.0.1:10002/devstoreaccount1"
)
```

### Account name + key
```python
service = TableServiceClient(
    endpoint="https://<account>.table.core.windows.net/",
    credential=AzureNamedKeyCredential("<account_name>", "<account_key>"),
)
```

### Get a TableClient directly (skip TableServiceClient)
```python
table_client = TableClient.from_connection_string(
    conn_str=os.environ["AZURE_STORAGE_CONNECTION_STRING"],
    table_name="orders",
)
```

## Table Management

```python
with TableServiceClient.from_connection_string(conn_str) as service:
    # Create (idempotent — safe to call every startup)
    table_client = service.create_table_if_not_exists("orders")
    
    # Or just get a client for an existing table
    table_client = service.get_table_client("orders")
    
    # List all tables
    for table in service.list_tables():
        print(table.name)
    
    # Delete
    service.delete_table("orders")  # no error if not found
```

## Entity Structure

Every entity **must** have `PartitionKey` and `RowKey` as strings. Together they form the unique key. Everything else is a property.

```python
entity = {
    "PartitionKey": "electronics",   # logical group (e.g. category, tenant, user)
    "RowKey": "prod-001",            # unique within the partition
    "Name": "Laptop",
    "Price": 999.99,
    "InStock": True,
    "CreatedAt": datetime.now(timezone.utc),
}
```

**Choose PartitionKey wisely** — all entities in a batch must share the same PartitionKey, and queries filtering by PartitionKey are much faster (single-partition scan vs full table scan).

## Entity CRUD

```python
with service.get_table_client("products") as table:

    # CREATE — raises ResourceExistsError if PK+RK combo already exists
    table.create_entity(entity)

    # READ — raises ResourceNotFoundError if missing
    item = table.get_entity(partition_key="electronics", row_key="prod-001")
    print(item["Name"], item.metadata["etag"])

    # UPSERT — always succeeds (create if new, update if exists)
    # UpdateMode.MERGE: merge fields, keep unspecified properties (default)
    # UpdateMode.REPLACE: replace entire entity, deletes unspecified properties
    table.upsert_entity({"PartitionKey": "electronics", "RowKey": "prod-001", "Price": 899.99},
                        mode=UpdateMode.MERGE)

    # UPDATE — entity must already exist (raises HttpResponseError if not found)
    table.update_entity({"PartitionKey": "electronics", "RowKey": "prod-001", "Price": 849.99},
                        mode=UpdateMode.MERGE)

    # DELETE — no error if entity not found
    table.delete_entity(partition_key="electronics", row_key="prod-001")
    # or pass the entity dict directly:
    table.delete_entity(item)
```

**MERGE vs REPLACE:**
- `UpdateMode.MERGE` (default): sends a PATCH — only updates the fields you provide, leaves everything else alone. Use for partial updates.
- `UpdateMode.REPLACE`: sends a PUT — replaces the whole entity. Any fields not in your dict are deleted from storage. Use when you want to overwrite completely.

## Querying with OData Filters

Use `query_entities` for filtered reads. Always use **parameterized** queries — never string-interpolate user input.

```python
# Filter by PartitionKey (single-partition, fast)
items = table.query_entities(
    query_filter="PartitionKey eq @pk",
    parameters={"pk": "electronics"},
)
for item in items:
    print(item["Name"])

# Multiple conditions
items = table.query_entities(
    query_filter="PartitionKey eq @pk and Price le @max_price and InStock eq @in_stock",
    parameters={"pk": "electronics", "max_price": 500.0, "in_stock": True},
)

# Date range (datetime parameters work natively)
from datetime import datetime, timezone, timedelta
cutoff = datetime.now(timezone.utc) - timedelta(days=7)
items = table.query_entities(
    query_filter="PartitionKey eq @pk and CreatedAt ge @since",
    parameters={"pk": "orders", "since": cutoff},
)

# Select only specific fields (reduces payload)
items = table.query_entities(
    query_filter="PartitionKey eq @pk",
    parameters={"pk": "electronics"},
    select=["Name", "Price"],
)

# List ALL entities (no filter) — use for small tables or admin tasks
for item in table.list_entities():
    print(item)
```

**OData operators**: `eq`, `ne`, `gt`, `lt`, `ge`, `le`, `and`, `or`, `not`

## Batch / Transaction Operations

All operations in a batch must target the **same PartitionKey**. Transactions are atomic — all succeed or all fail. Max 100 operations per batch.

```python
operations = [
    ("create", {"PartitionKey": "orders", "RowKey": "o-001", "Total": 50.0}),
    ("upsert", {"PartitionKey": "orders", "RowKey": "o-002", "Total": 75.0}),
    ("update", {"PartitionKey": "orders", "RowKey": "o-003", "Total": 90.0}),
    ("delete", {"PartitionKey": "orders", "RowKey": "o-old"}),
]

try:
    responses = table.submit_transaction(operations)
except TableTransactionError as e:
    print(f"Transaction failed at operation {e.error.code}: {e}")
```

Valid operation types: `"create"`, `"upsert"`, `"update"`, `"delete"`

For bulk inserts, chunk into batches of up to 100:
```python
def batch_insert(table, entities: list, partition_key: str):
    chunk_size = 100
    for i in range(0, len(entities), chunk_size):
        ops = [("upsert", e) for e in entities[i:i + chunk_size]]
        table.submit_transaction(ops)
```

## Error Handling

```python
from azure.core.exceptions import ResourceNotFoundError, ResourceExistsError, HttpResponseError
from azure.data.tables import TableTransactionError

# Reading a missing entity
try:
    item = table.get_entity("electronics", "nonexistent")
except ResourceNotFoundError:
    return None  # common pattern: return None instead of raising

# Creating a duplicate
try:
    table.create_entity(entity)
except ResourceExistsError:
    table.upsert_entity(entity)  # fall back to upsert

# Batch failure
try:
    table.submit_transaction(operations)
except TableTransactionError as e:
    # e.error contains the failing operation details
    print(f"Failed: {e.error.code} — {e.error.message}")
```

## Async Usage

```python
from azure.data.tables.aio import TableServiceClient, TableClient
from azure.identity.aio import DefaultAzureCredential

async def main():
    async with TableServiceClient(
        endpoint="https://<account>.table.core.windows.net/",
        credential=DefaultAzureCredential(),
    ) as service:
        async with service.get_table_client("products") as table:
            item = await table.get_entity("electronics", "prod-001")
            
            async for entity in table.query_entities("PartitionKey eq @pk",
                                                      parameters={"pk": "electronics"}):
                print(entity["Name"])
            
            await table.submit_transaction(operations)
```

## Property Types

Python types are auto-mapped to EDM types:

| Python type | EDM type | Notes |
|-------------|----------|-------|
| `str` | Edm.String | |
| `int` | Edm.Int32 | Use `EntityProperty(val, EdmType.INT64)` for large ints |
| `float` | Edm.Double | |
| `bool` | Edm.Boolean | |
| `datetime` | Edm.DateTime | Use UTC-aware datetimes |
| `bytes` | Edm.Binary | |
| `UUID` | Edm.Guid | |

For int64, GUID, or binary blobs where auto-detection isn't enough:
```python
from azure.data.tables import EntityProperty, EdmType
entity["LargeId"] = EntityProperty(9_999_999_999, EdmType.INT64)
entity["Guid"] = EntityProperty(uuid.uuid4(), EdmType.GUID)
```

## Quick Reference

```python
# Full workflow
conn_str = os.environ["AZURE_STORAGE_CONNECTION_STRING"]

with TableServiceClient.from_connection_string(conn_str) as service:
    table = service.create_table_if_not_exists("inventory")

    # Write
    table.upsert_entity({"PartitionKey": "warehouse-a", "RowKey": "item-1", "Qty": 50})

    # Read
    item = table.get_entity("warehouse-a", "item-1")

    # Query
    low_stock = list(table.query_entities(
        "PartitionKey eq @pk and Qty lt @threshold",
        parameters={"pk": "warehouse-a", "threshold": 10},
    ))

    # Delete
    table.delete_entity("warehouse-a", "item-1")
```
