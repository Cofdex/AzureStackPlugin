---
name: azure-containerregistry
description: >
  Manage Azure Container Registry (ACR) resources using the azure-containerregistry Python SDK.
  Use this skill whenever the user needs to work with container images, OCI artifacts, Docker
  registries, or ACR repositories in Python — including listing repositories, managing tags,
  deleting old images, pushing/pulling OCI artifacts, setting permissions, or purging untagged
  manifests. Triggers on: "azure-containerregistry", "ContainerRegistryClient",
  "ContainerRegistryContentClient", "container images", "docker registry", "ACR", "OCI artifact",
  "container tags", "image digest", "registry cleanup".
---

# Azure Container Registry SDK for Python

## Installation & Imports

```python
pip install azure-containerregistry azure-identity
```

```python
# Sync clients
from azure.containerregistry import (
    ContainerRegistryClient,
    ContainerRegistryContentClient,
    ArtifactTagOrder,
    ArtifactManifestOrder,
    ArtifactTagProperties,
    ArtifactManifestProperties,
)
from azure.identity import DefaultAzureCredential
from azure.core.exceptions import ResourceNotFoundError

# Async clients
from azure.containerregistry.aio import ContainerRegistryClient as AsyncContainerRegistryClient
from azure.containerregistry.aio import ContainerRegistryContentClient as AsyncContainerRegistryContentClient
```

## Authentication

```python
# Production: managed identity / service principal
credential = DefaultAzureCredential()
client = ContainerRegistryClient("https://myregistry.azurecr.io", credential)

# Anonymous access (public registries)
client = ContainerRegistryClient("https://mcr.microsoft.com", credential=None, audience="https://management.azure.com")

# Sovereign clouds (supply audience explicitly)
client = ContainerRegistryClient(
    "https://myregistry.azurecr.cn",
    DefaultAzureCredential(),
    audience="https://management.chinacloudapi.cn"
)
```

## ContainerRegistryClient — Repository & Tag Operations

### List repositories
```python
with ContainerRegistryClient("https://myregistry.azurecr.io", DefaultAzureCredential()) as client:
    for repo_name in client.list_repository_names():
        print(repo_name)
```

### Get repository properties
```python
props = client.get_repository_properties("myapp")
print(props.name, props.manifest_count, props.tag_count)
```

### Delete a repository
```python
client.delete_repository("myapp")  # does not raise on 404
```

### List tags (with ordering)
```python
# Most recently updated first
for tag in client.list_tag_properties("myapp", order=ArtifactTagOrder.LAST_UPDATED_ON_DESCENDING):
    print(tag.name, tag.digest, tag.last_updated_on)

# Oldest first
for tag in client.list_tag_properties("myapp", order=ArtifactTagOrder.LAST_UPDATED_ON_ASCENDING):
    print(tag.name)
```

### Get a specific tag
```python
tag_props = client.get_tag_properties("myapp", "v1.0.0")
print(tag_props.name)          # "v1.0.0"
print(tag_props.digest)        # "sha256:abc..."
print(tag_props.created_on)    # datetime
print(tag_props.last_updated_on)
# Writeable properties
print(tag_props.can_read, tag_props.can_write, tag_props.can_delete, tag_props.can_list)
```

### Update tag permissions
```python
# Make a tag read-only (prevent deletion)
client.update_tag_properties("myapp", "stable", can_write=False, can_delete=False)

# Restore full permissions
client.update_tag_properties("myapp", "stable", can_write=True, can_delete=True)
```

### Delete a tag
```python
client.delete_tag("myapp", "old-tag")  # does not raise on 404
```

## Manifest Operations

A manifest represents a specific image/artifact version identified by a digest (`sha256:...`). You can reference manifests by tag or digest.

### List manifests
```python
for manifest in client.list_manifest_properties("myapp", order=ArtifactManifestOrder.LAST_UPDATED_ON_DESCENDING):
    print(manifest.digest)          # "sha256:abc..."
    print(manifest.tags)            # list of tag names, or [] if untagged
    print(manifest.size_in_bytes)
    print(manifest.created_on)
    print(manifest.last_updated_on)
    print(manifest.architecture)    # e.g. "amd64"
    print(manifest.operating_system) # e.g. "linux"
```

### Get manifest properties
```python
# By tag
props = client.get_manifest_properties("myapp", "v1.0.0")

# By digest
props = client.get_manifest_properties("myapp", "sha256:abc123...")
```

### Update manifest permissions
```python
client.update_manifest_properties("myapp", "sha256:abc...", can_write=False, can_delete=False)
```

### Delete a manifest (and all its tags)
```python
client.delete_manifest("myapp", "sha256:abc...")  # deletes image + all tags pointing to it
client.delete_manifest("myapp", "v1.0.0")          # also accepts tag name
```

## Common Patterns

### Purge untagged manifests (cleanup)
```python
with ContainerRegistryClient("https://myregistry.azurecr.io", DefaultAzureCredential()) as client:
    for manifest in client.list_manifest_properties("myapp"):
        if not manifest.tags:  # untagged
            print(f"Deleting untagged manifest: {manifest.digest}")
            client.delete_manifest("myapp", manifest.digest)
```

### Keep only latest N tags
```python
def keep_latest_n(client, repo: str, keep: int):
    tags = list(client.list_tag_properties(repo, order=ArtifactTagOrder.LAST_UPDATED_ON_DESCENDING))
    for tag in tags[keep:]:
        print(f"Deleting {tag.name}")
        client.delete_tag(repo, tag.name)
    # Then purge untagged manifests
    for manifest in client.list_manifest_properties(repo):
        if not manifest.tags:
            client.delete_manifest(repo, manifest.digest)
```

### Find all images older than N days
```python
from datetime import datetime, timezone, timedelta

cutoff = datetime.now(timezone.utc) - timedelta(days=30)
with ContainerRegistryClient("https://myregistry.azurecr.io", DefaultAzureCredential()) as client:
    for manifest in client.list_manifest_properties("myapp"):
        if manifest.last_updated_on < cutoff and not manifest.tags:
            client.delete_manifest("myapp", manifest.digest)
```

### Lock a production image (prevent deletion)
```python
client.update_manifest_properties("myapp", "sha256:prod-digest...", can_delete=False, can_write=False)
```

## ContainerRegistryContentClient — Push/Pull OCI Artifacts

Use `ContainerRegistryContentClient` (not `ContainerRegistryClient`) for pushing and pulling OCI artifacts and raw manifests/blobs.

```python
from azure.containerregistry import ContainerRegistryContentClient
from azure.containerregistry import OciImageManifest, OciManifestConfig
import json

content_client = ContainerRegistryContentClient(
    "https://myregistry.azurecr.io",
    "myapp",          # repository name
    DefaultAzureCredential()
)
```

### Upload a blob
```python
data = b"my artifact data"
digest, size = content_client.upload_blob(data)
print(f"Blob uploaded: {digest}, {size} bytes")
```

### Upload an OCI manifest
```python
# Build a simple OCI manifest
config_data = json.dumps({"mediaType": "application/vnd.oci.image.config.v1+json"}).encode()
config_digest, config_size = content_client.upload_blob(config_data)

layer_data = b"artifact content"
layer_digest, layer_size = content_client.upload_blob(layer_data)

manifest = OciImageManifest(
    config=OciManifestConfig(media_type="application/vnd.oci.image.config.v1+json", digest=config_digest, size=config_size),
    layers=[{"mediaType": "application/octet-stream", "digest": layer_digest, "size": layer_size}]
)
digest = content_client.set_manifest(manifest, tag="v1.0")
print(f"Manifest digest: {digest}")
```

### Download a blob
```python
stream = content_client.download_blob("sha256:abc...")
data = b"".join(stream)
```

### Pull a manifest
```python
result = content_client.get_manifest("v1.0")
print(result.digest)      # "sha256:..."
print(result.media_type)  # "application/vnd.oci.image.manifest.v1+json"
print(result.manifest)    # dict with full manifest JSON
```

### Delete a blob
```python
content_client.delete_blob("sha256:abc...")
```

## Async Usage

```python
import asyncio
from azure.containerregistry.aio import ContainerRegistryClient
from azure.identity.aio import DefaultAzureCredential

async def list_repos():
    async with ContainerRegistryClient("https://myregistry.azurecr.io", DefaultAzureCredential()) as client:
        async for repo in client.list_repository_names():
            print(repo)
        
        async for tag in client.list_tag_properties("myapp", order=ArtifactTagOrder.LAST_UPDATED_ON_DESCENDING):
            print(tag.name, tag.digest)

asyncio.run(list_repos())
```

## Error Handling

```python
from azure.core.exceptions import ResourceNotFoundError, ClientAuthenticationError
from azure.containerregistry import DigestValidationError

try:
    props = client.get_tag_properties("myapp", "nonexistent")
except ResourceNotFoundError:
    print("Tag not found")

try:
    props = client.get_manifest_properties("myapp", "sha256:invalid...")
except DigestValidationError:
    print("Digest validation failed — data may be corrupted")

# Note: delete_* methods (delete_tag, delete_manifest, delete_repository) do NOT raise on 404
```

## Enums Reference

```python
from azure.containerregistry import ArtifactTagOrder, ArtifactManifestOrder

# Tag ordering
ArtifactTagOrder.LAST_UPDATED_ON_DESCENDING  # newest first (most common)
ArtifactTagOrder.LAST_UPDATED_ON_ASCENDING   # oldest first
ArtifactTagOrder.NONE                         # no ordering

# Manifest ordering  
ArtifactManifestOrder.LAST_UPDATED_ON_DESCENDING
ArtifactManifestOrder.LAST_UPDATED_ON_ASCENDING
ArtifactManifestOrder.NONE
```

## ArtifactTagProperties Fields

| Field | Type | Description |
|-------|------|-------------|
| `name` | str | Tag name (e.g. "v1.0.0") |
| `digest` | str | Manifest digest this tag points to |
| `created_on` | datetime | When tag was created |
| `last_updated_on` | datetime | When tag was last updated |
| `can_read` | bool | Permission to read |
| `can_write` | bool | Permission to write |
| `can_delete` | bool | Permission to delete |
| `can_list` | bool | Permission to list |

## ArtifactManifestProperties Fields

| Field | Type | Description |
|-------|------|-------------|
| `digest` | str | Content-addressable SHA256 digest |
| `tags` | List[str] | Tag names pointing to this manifest |
| `size_in_bytes` | int | Manifest size |
| `created_on` | datetime | Creation timestamp |
| `last_updated_on` | datetime | Last update timestamp |
| `architecture` | str | e.g. "amd64", "arm64" |
| `operating_system` | str | e.g. "linux", "windows" |
| `can_read/write/delete/list` | bool | Permissions |
