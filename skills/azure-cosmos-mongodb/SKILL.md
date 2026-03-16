---
name: azure-cosmos-mongodb
description: >
  Azure Cosmos DB MongoDB API with Python using pymongo. Use when migrating from
  MongoDB or needing MongoDB driver compatibility with Azure Cosmos DB. Triggers on:
  "cosmos mongodb", "pymongo cosmos", "MongoClient cosmos", "mongodb cosmos",
  "Cosmos MongoDB API", "cosmos mongo". CRITICAL: Use pymongo NOT azure-cosmos.
  Port is 10255 not 27017. Connection string must include replicaSet=globaldb.
  Do NOT use mongodb+srv:// protocol.
---

# Azure Cosmos DB MongoDB API with Python (pymongo)

> Use this when connecting to Cosmos DB via the **MongoDB API** (for MongoDB compatibility).
> For the native NoSQL API, use the `azure-cosmos` package instead.

## Package
```bash
uv add pymongo
```

## Connection

```python
from pymongo import MongoClient

# Connection string — exact format required
CONN_STR = (
    "mongodb://{account}:{key}@{account}.mongo.cosmos.azure.com:10255/"
    "?ssl=true&replicaSet=globaldb&retrywrites=false&maxIdleTimeMS=120000"
)
# CRITICAL: port=10255 (NOT 27017), mongodb:// (NOT mongodb+srv://), replicaSet=globaldb

client = MongoClient(CONN_STR)
db = client["mydb"]
collection = db["users"]
```

## CRUD operations

```python
# INSERT
result = collection.insert_one({"name": "Alice", "age": 30, "city": "Seattle"})
print(result.inserted_id)

# Bulk insert
result = collection.insert_many([
    {"name": "Bob", "age": 25},
    {"name": "Carol", "age": 35},
])

# FIND
user = collection.find_one({"name": "Alice"})
if user:
    print(user["_id"], user["name"])

# Find multiple (returns cursor — iterate or list())
users = collection.find({"age": {"$gt": 20}}, {"name": 1, "_id": 0})
for user in users:
    print(user["name"])

# UPDATE
collection.update_one(
    {"name": "Alice"},
    {"$set": {"age": 31}},
)

# Upsert pattern
collection.update_one(
    {"email": "alice@example.com"},
    {"$set": {"name": "Alice", "age": 31}},
    upsert=True,
)

# REPLACE
collection.replace_one({"_id": doc_id}, new_doc)

# DELETE
collection.delete_one({"name": "Alice"})
collection.delete_many({"status": "inactive"})
```

## Indexes

```python
# Create index (do during low-traffic periods — costs RUs)
collection.create_index("email", unique=True)
collection.create_index([("city", 1), ("age", -1)])   # compound index

# List indexes
for idx in collection.list_indexes():
    print(idx)
```

## Aggregation pipeline

```python
pipeline = [
    {"$match": {"status": "active"}},
    {"$group": {"_id": "$city", "count": {"$sum": 1}}},
    {"$sort": {"count": -1}},
]
results = list(collection.aggregate(pipeline))
```

## RU throttling / retry pattern

```python
import time
from pymongo.errors import OperationFailure

def execute_with_retry(operation, max_retries=3):
    for attempt in range(max_retries):
        try:
            return operation()
        except OperationFailure as e:
            if e.code == 16500:   # TooManyRequests / RU exceeded
                wait = (2 ** attempt) * 0.5
                time.sleep(wait)
            else:
                raise
    raise Exception("Max retries exceeded")

result = execute_with_retry(lambda: collection.insert_one({"data": "value"}))
```

## Common mistakes

| ❌ Wrong | ✅ Correct |
|---|---|
| `mongodb+srv://account.mongo.cosmos.azure.com` | `mongodb://account:key@account.mongo.cosmos.azure.com:10255/` |
| Port `27017` | Port `10255` for Cosmos DB |
| Missing `replicaSet=globaldb` | Always include in connection string |
| `from azure.cosmos import CosmosClient` | Use `from pymongo import MongoClient` for MongoDB API |
| No RU throttling handling | Catch `OperationFailure` with code `16500` and retry |
| `client.close()` omitted | Always close client when done |
| Partition key omitted from queries | Include partition key field in queries for performance |
