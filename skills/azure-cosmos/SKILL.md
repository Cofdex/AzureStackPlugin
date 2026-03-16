---
name: azure-cosmos
description: >
  Azure Cosmos DB SDK for Python (NoSQL API). Use for document CRUD, queries, containers, and
  globally distributed data. Use this skill whenever the user mentions Cosmos DB, CosmosClient,
  NoSQL databases, document stores, partition keys, or needs to build or query a Cosmos container —
  including client setup with dual auth (DefaultAzureCredential for prod, connection string for dev),
  service layer classes, parameterized queries, patch operations, or TDD patterns for mocking Cosmos.
  Triggers on: "cosmos db", "CosmosClient", "container", "document", "NoSQL", "partition key",
  "azure-cosmos", "CosmosResourceNotFoundError", "query_items", "add persistence", "document store".
---

# Azure Cosmos DB NoSQL — Python SDK

## Installation & Imports

```python
uv add azure-cosmos azure-identity
```

```python
# Sync client
from azure.cosmos import CosmosClient, PartitionKey
from azure.cosmos.exceptions import (
    CosmosResourceNotFoundError,   # 404
    CosmosResourceExistsError,     # 409
    CosmosHttpResponseError,       # other HTTP errors
    CosmosAccessConditionFailedError,  # 412 (ETag conflicts)
)

# Async client (same API, add async/await)
from azure.cosmos.aio import CosmosClient as AsyncCosmosClient
```

## Client Construction — Dual Auth Pattern

The most important pattern: use `DefaultAzureCredential` in production (Azure), and a connection string or emulator key locally. Never hardcode credentials.

```python
import os
from azure.cosmos import CosmosClient
from azure.identity import DefaultAzureCredential

def get_cosmos_client() -> CosmosClient:
    # Production: uses managed identity / service principal
    if url := os.getenv("COSMOS_URL"):
        return CosmosClient(url=url, credential=DefaultAzureCredential())
    
    # Dev/emulator: uses connection string
    conn_str = os.getenv(
        "COSMOS_CONNECTION_STRING",
        # Local emulator default
        "AccountEndpoint=https://localhost:8081/;AccountKey=C2y6yDjf5/R+ob0N8A7Cgv30VRDJIWEHLM+4QDU5DE2nQ9nDuVTqobD4b8mGGyPMbIZnqyMcZSXHQjEMThqP=="
    )
    return CosmosClient.from_connection_string(conn_str)
```

## FastAPI — Singleton Client with Lifespan

Cosmos clients are expensive to create — create one at startup, reuse it across requests.

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends
from azure.cosmos import CosmosClient

_cosmos_client: CosmosClient | None = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global _cosmos_client
    _cosmos_client = get_cosmos_client()
    yield
    _cosmos_client.close()

app = FastAPI(lifespan=lifespan)

def get_db() -> CosmosClient:
    return _cosmos_client
```

## Database & Container Setup

```python
from azure.cosmos import CosmosClient, PartitionKey

client = get_cosmos_client()

# Get or create database
db = client.create_database_if_not_exists(id="myapp-db")
# Or just get (assumes already exists):
db = client.get_database_client("myapp-db")

# Get or create container — always define partition key upfront
container = db.create_container_if_not_exists(
    id="users",
    partition_key=PartitionKey(path="/userId"),
    offer_throughput=400,           # manual RU/s; omit for serverless
)
# Or just get:
container = db.get_container_client("users")
```

**Partition key design matters**: choose a field with high cardinality that appears in most queries (e.g., `/userId`, `/tenantId`, `/category`). Queries that include the partition key are 10-100x cheaper than cross-partition queries.

## Service Layer Pattern

Encapsulate all Cosmos operations in a class. This makes testing easy (inject a mock container) and keeps business logic separate from persistence.

```python
from dataclasses import dataclass, asdict
from azure.cosmos import ContainerProxy
from azure.cosmos.exceptions import CosmosResourceNotFoundError

@dataclass
class User:
    id: str
    userId: str          # must match partition key path
    name: str
    email: str

class UserService:
    def __init__(self, container: ContainerProxy):
        self._container = container

    def create(self, user: User) -> User:
        item = self._container.create_item(body=asdict(user))
        return User(**item)

    def get(self, user_id: str) -> User | None:
        try:
            item = self._container.read_item(
                item=user_id,
                partition_key=user_id,   # value, not path
            )
            return User(**item)
        except CosmosResourceNotFoundError:
            return None

    def upsert(self, user: User) -> User:
        item = self._container.upsert_item(body=asdict(user))
        return User(**item)

    def update(self, user_id: str, user: User) -> User:
        item = self._container.replace_item(
            item=user_id,
            body=asdict(user),
        )
        return User(**item)

    def delete(self, user_id: str) -> None:
        try:
            self._container.delete_item(item=user_id, partition_key=user_id)
        except CosmosResourceNotFoundError:
            pass  # idempotent delete

    def list_by_email_domain(self, domain: str) -> list[User]:
        items = self._container.query_items(
            query="SELECT * FROM c WHERE ENDSWITH(c.email, @domain)",
            parameters=[{"name": "@domain", "value": domain}],
            enable_cross_partition_query=True,
        )
        return [User(**i) for i in items]
```

## CRUD Operations Reference

```python
# CREATE — fails with CosmosResourceExistsError if id already exists
item = container.create_item(body={"id": "u1", "userId": "u1", "name": "Alice"})

# READ — provide the item id AND the partition key value
item = container.read_item(item="u1", partition_key="u1")

# UPSERT — creates if not exists, replaces if exists
item = container.upsert_item(body={"id": "u1", "userId": "u1", "name": "Alice Updated"})

# REPLACE — full document replacement; raises 404 if not found
item = container.replace_item(item="u1", body={...})

# DELETE — raises CosmosResourceNotFoundError if not found
container.delete_item(item="u1", partition_key="u1")

# PATCH — partial updates without fetching the document first
item = container.patch_item(
    item="u1",
    partition_key="u1",
    patch_operations=[
        {"op": "replace", "path": "/name", "value": "Bob"},
        {"op": "add", "path": "/tags", "value": ["premium"]},
        {"op": "remove", "path": "/legacyField"},
        {"op": "incr", "path": "/loginCount", "value": 1},
    ],
)
```

## Querying

Always use parameterized queries — never string-interpolate user input into queries.

```python
# Single-partition query (cheaper — always prefer when you know the partition)
items = list(container.query_items(
    query="SELECT * FROM c WHERE c.status = @status",
    parameters=[{"name": "@status", "value": "active"}],
    partition_key="user-123",          # restrict to one partition
))

# Cross-partition query (when partition key is unknown)
items = list(container.query_items(
    query="SELECT * FROM c WHERE c.email = @email",
    parameters=[{"name": "@email", "value": "alice@example.com"}],
    enable_cross_partition_query=True,
))

# Multiple parameters
items = list(container.query_items(
    query="SELECT * FROM c WHERE c.userId = @uid AND c.status = @status ORDER BY c._ts DESC",
    parameters=[
        {"name": "@uid", "value": "u1"},
        {"name": "@status", "value": "active"},
    ],
    partition_key="u1",
))

# COUNT / aggregates
results = list(container.query_items(
    query="SELECT VALUE COUNT(1) FROM c WHERE c.status = @status",
    parameters=[{"name": "@status", "value": "active"}],
    enable_cross_partition_query=True,
))
count = results[0] if results else 0
```

## Async Usage

The async client mirrors the sync API exactly — just add `async with` and `await`.

```python
from azure.cosmos.aio import CosmosClient
from azure.identity.aio import DefaultAzureCredential

async def main():
    async with CosmosClient(url=os.getenv("COSMOS_URL"), credential=DefaultAzureCredential()) as client:
        db = client.get_database_client("myapp-db")
        container = db.get_container_client("users")

        item = await container.create_item(body={"id": "u1", "userId": "u1"})
        
        # Async iteration over query results
        async for item in container.query_items(
            query="SELECT * FROM c WHERE c.userId = @uid",
            parameters=[{"name": "@uid", "value": "u1"}],
            partition_key="u1",
        ):
            print(item)
```

## TDD — Mocking Cosmos in Unit Tests

```python
from unittest.mock import MagicMock, patch
from azure.cosmos.exceptions import CosmosResourceNotFoundError
import pytest

@pytest.fixture
def mock_container():
    return MagicMock()

@pytest.fixture
def user_service(mock_container):
    return UserService(container=mock_container)

def test_get_user_not_found(user_service, mock_container):
    mock_container.read_item.side_effect = CosmosResourceNotFoundError(
        message="Not found", response=MagicMock(status_code=404)
    )
    result = user_service.get("nonexistent")
    assert result is None

def test_create_user(user_service, mock_container):
    expected = {"id": "u1", "userId": "u1", "name": "Alice", "email": "a@example.com"}
    mock_container.create_item.return_value = expected
    
    user = User(id="u1", userId="u1", name="Alice", email="a@example.com")
    result = user_service.create(user)
    
    mock_container.create_item.assert_called_once_with(body=expected)
    assert result.name == "Alice"

def test_query_users(user_service, mock_container):
    mock_container.query_items.return_value = [
        {"id": "u1", "userId": "u1", "name": "Alice", "email": "alice@example.com"}
    ]
    results = user_service.list_by_email_domain("example.com")
    assert len(results) == 1
    mock_container.query_items.assert_called_once_with(
        query="SELECT * FROM c WHERE ENDSWITH(c.email, @domain)",
        parameters=[{"name": "@domain", "value": "example.com"}],
        enable_cross_partition_query=True,
    )
```

## FastAPI Endpoint Integration

```python
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

router = APIRouter(prefix="/users", tags=["users"])

class UserCreate(BaseModel):
    name: str
    email: str

def get_user_service(client: CosmosClient = Depends(get_db)) -> UserService:
    container = client.get_database_client("myapp-db").get_container_client("users")
    return UserService(container)

@router.post("/", status_code=status.HTTP_201_CREATED)
def create_user(payload: UserCreate, svc: UserService = Depends(get_user_service)):
    import uuid
    user_id = str(uuid.uuid4())
    user = User(id=user_id, userId=user_id, name=payload.name, email=payload.email)
    return svc.create(user)

@router.get("/{user_id}")
def get_user(user_id: str, svc: UserService = Depends(get_user_service)):
    user = svc.get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(user_id: str, svc: UserService = Depends(get_user_service)):
    svc.delete(user_id)
```

## Error Handling Reference

| Exception | HTTP Status | When it occurs |
|-----------|-------------|----------------|
| `CosmosResourceNotFoundError` | 404 | `read_item`, `delete_item`, `replace_item` on missing item |
| `CosmosResourceExistsError` | 409 | `create_item` when id already exists |
| `CosmosAccessConditionFailedError` | 412 | ETag mismatch in conditional operations |
| `CosmosHttpResponseError` | varies | Rate limiting (429), server errors (500/503) |

```python
from azure.cosmos.exceptions import CosmosResourceNotFoundError, CosmosResourceExistsError

try:
    item = container.create_item(body=doc)
except CosmosResourceExistsError:
    # Document already exists — use upsert_item instead if idempotency is needed
    item = container.upsert_item(body=doc)
except CosmosHttpResponseError as e:
    if e.status_code == 429:
        # Throttled — retry with backoff
        time.sleep(e.retry_after_in_milliseconds / 1000)
```
