---
name: azure-blob-storage
description: >
  Azure Blob Storage SDK for Python (azure-storage-blob) — correct patterns for
  uploading, downloading, listing, and managing blobs and containers. Use this skill
  whenever working with Azure Blob Storage in Python, including: uploading files or
  streams, downloading blobs, listing blobs/containers, managing metadata, generating
  SAS tokens, copying or deleting blobs, or setting access tiers. Triggers on:
  "blob storage", "BlobServiceClient", "ContainerClient", "BlobClient", "upload blob",
  "download blob", "list blobs", "azure storage", "SAS token", "container", "block blob",
  "azure-storage-blob". Always use this skill when the user mentions Azure storage,
  blobs, or any azure-storage-blob SDK usage.
---

# Azure Blob Storage SDK for Python

The SDK has three client classes. Choose the right one for your scope:

| Client | Scope | Instantiate from |
|--------|-------|-----------------|
| `BlobServiceClient` | Storage account | Account URL + credential |
| `ContainerClient` | One container | `BlobServiceClient.get_container_client()` or directly |
| `BlobClient` | One blob | `ContainerClient.get_blob_client()` or directly |

## Authentication

```python
from azure.storage.blob import BlobServiceClient
from azure.identity import DefaultAzureCredential

# Recommended for production: managed identity / service principal
client = BlobServiceClient(
    account_url="https://<account>.blob.core.windows.net",
    credential=DefaultAzureCredential()
)

# Connection string (dev/test)
client = BlobServiceClient.from_connection_string(conn_str)

# Account key
client = BlobServiceClient(
    account_url="https://<account>.blob.core.windows.net",
    credential="<account_key>"
)

# SAS URL (pre-authorized, no additional credential needed)
client = BlobServiceClient(sas_url)
```

## Getting sub-clients

```python
container_client = service_client.get_container_client("my-container")
blob_client = container_client.get_blob_client("folder/file.txt")

# Or get blob client directly from service
blob_client = service_client.get_blob_client(container="my-container", blob="file.txt")
```

---

## Upload

`upload_blob()` returns `Dict[str, Any]` (not `BlobProperties`). The dict contains `etag`,
`last_modified`, `version_id`, etc.

**By default `overwrite=False` — raises `ResourceExistsError` if the blob already exists.**

```python
# From bytes
blob_client.upload_blob(b"Hello world", overwrite=True)

# From file path
with open("report.pdf", "rb") as f:
    blob_client.upload_blob(f, overwrite=True)

# With metadata and content type
blob_client.upload_blob(
    data,
    overwrite=True,
    metadata={"author": "alice", "project": "demo"},  # Dict[str, str]
    content_settings=ContentSettings(content_type="application/pdf"),
)

# Large file — SDK handles chunking automatically; no need for manual chunking
with open("large_video.mp4", "rb") as f:
    blob_client.upload_blob(f, overwrite=True, max_concurrency=4)
```

For **generators/iterables**, `length` is required:
```python
blob_client.upload_blob(data=my_generator, length=expected_bytes)
```

---

## Download

`download_blob()` returns a `StorageStreamDownloader`. There is **no `open_blob_stream()`** method.

```python
downloader = blob_client.download_blob()

# To bytes
data = downloader.readall()

# To file
with open("local_copy.pdf", "wb") as f:
    downloader.readinto(f)      # efficient streaming into file

# In chunks (for large blobs)
for chunk in downloader.chunks():
    process(chunk)

# Partial download (byte range)
downloader = blob_client.download_blob(offset=0, length=1024)

# As text
text = blob_client.download_blob(encoding="utf-8").readall()
```

---

## List blobs

`list_blobs()` returns a **lazy** `ItemPaged[BlobProperties]` — iterating triggers HTTP calls.

```python
# List all blobs in container
for blob in container_client.list_blobs():
    print(blob.name, blob.size, blob.last_modified)

# Filter by prefix
for blob in container_client.list_blobs(name_starts_with="logs/2024/"):
    print(blob.name)

# Include snapshots or metadata in results
for blob in container_client.list_blobs(include=["snapshots", "metadata"]):
    print(blob.name, blob.metadata)

# List containers in account
for container in service_client.list_containers():
    print(container.name)
```

There is **no complex server-side filtering** — only `name_starts_with` prefix filtering.
Filter further in Python if needed.

---

## Container management

```python
# Create — raises ResourceExistsError if already exists
container_client.create_container()

# Create if not exists
try:
    container_client.create_container()
except ResourceExistsError:
    pass  # already exists, that's fine

# Get properties (includes metadata, public access level)
props = container_client.get_container_properties()

# Delete (all blobs inside are deleted too)
container_client.delete_container()
```

---

## Blob metadata

Metadata values must be `str`. Keys are case-insensitive.

```python
# Set metadata (replaces all existing metadata)
blob_client.set_blob_metadata({"env": "prod", "version": "3"})

# Read metadata via get_blob_properties()
props = blob_client.get_blob_properties()
print(props.metadata)          # Dict[str, str]
print(props.size)
print(props.last_modified)
print(props.content_settings.content_type)
```

---

## Delete

```python
# Delete a blob
blob_client.delete_blob()

# Delete blob AND all its snapshots
blob_client.delete_blob(delete_snapshots="include")

# Batch delete (ContainerClient)
container_client.delete_blobs("file1.txt", "file2.txt", "file3.txt")
```

---

## Copy blob

```python
# Copy from another blob's URL
source_url = source_blob_client.url
copy_props = dest_blob_client.start_copy_from_url(source_url)
# Returns immediately; copy happens server-side. Check copy_props["copy_status"]
```

---

## SAS token generation

`expiry` is **required**. Returns the SAS token string (not a full URL).

```python
from azure.storage.blob import generate_blob_sas, BlobSasPermissions
from datetime import datetime, timedelta, timezone

sas_token = generate_blob_sas(
    account_name="<account>",
    container_name="<container>",
    blob_name="report.pdf",
    account_key="<account_key>",          # or user_delegation_key=...
    permission=BlobSasPermissions(read=True),
    expiry=datetime.now(timezone.utc) + timedelta(hours=1),
)

# Build the full URL
sas_url = f"https://<account>.blob.core.windows.net/<container>/report.pdf?{sas_token}"
```

For **container-level SAS**:
```python
from azure.storage.blob import generate_container_sas, ContainerSasPermissions

sas_token = generate_container_sas(
    account_name="<account>",
    container_name="<container>",
    account_key="<account_key>",
    permission=ContainerSasPermissions(read=True, list=True),
    expiry=datetime.now(timezone.utc) + timedelta(hours=2),
)
```

---

## Access tiers

```python
from azure.storage.blob import StandardBlobTier

# Set tier on upload
blob_client.upload_blob(data, standard_blob_tier=StandardBlobTier.COOL)

# Change tier on existing blob
blob_client.set_standard_blob_tier(StandardBlobTier.ARCHIVE)
blob_client.set_standard_blob_tier(StandardBlobTier.HOT)
```

Tiers: `HOT` (frequent access), `COOL` (infrequent, ≥30 days), `COLD` (≥90 days),
`ARCHIVE` (offline, hours to rehydrate).

---

## Error handling

```python
from azure.core.exceptions import ResourceExistsError, ResourceNotFoundError, HttpResponseError

try:
    blob_client.upload_blob(data)          # overwrite=False by default
except ResourceExistsError:
    # Blob already exists
    ...

try:
    blob_client.download_blob().readall()
except ResourceNotFoundError:
    # Container or blob does not exist
    ...

try:
    container_client.create_container()
except HttpResponseError as e:
    print(e.status_code, e.error_code, e.message)
```

---

## Async client

All async classes live in `azure.storage.blob.aio`. Same methods, all awaitable.

```python
from azure.storage.blob.aio import BlobServiceClient
from azure.identity.aio import DefaultAzureCredential

async def main():
    async with BlobServiceClient(
        account_url="https://<account>.blob.core.windows.net",
        credential=DefaultAzureCredential()
    ) as service_client:
        container_client = service_client.get_container_client("my-container")

        # Upload
        blob_client = container_client.get_blob_client("file.txt")
        await blob_client.upload_blob(b"hello", overwrite=True)

        # Download
        data = await (await blob_client.download_blob()).readall()

        # List (async iteration)
        async for blob in container_client.list_blobs():
            print(blob.name)
```

---

## Common mistakes to avoid

| Wrong | Correct |
|-------|---------|
| `upload_blob()` returns `BlobProperties` | Returns `Dict[str, Any]` |
| `download_blob(stream=file)` | `download_blob().readinto(file)` |
| `blob_client.open_blob_stream()` | Doesn't exist — use `.download_blob().chunks()` |
| `metadata=["key:value"]` list | `metadata={"key": "value"}` dict only |
| Omitting `expiry` in SAS | `expiry` is required |
| `overwrite=True` is the default | Default is `False` — must pass `overwrite=True` explicitly |
| `upload_blob(generator)` without `length` | Must pass `length=` for generators/iterables |
| `list_blobs(filter=...)` for complex queries | Only `name_starts_with` is supported server-side |
