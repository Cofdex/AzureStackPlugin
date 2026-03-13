---
name: azure-datalake
description: >
  Azure Data Lake Storage Gen2 SDK for Python (azure-storage-file-datalake). Use for
  hierarchical namespace storage, large file uploads with append+flush pattern,
  directory management, and ACL/POSIX permissions. Triggers on: "data lake", "ADLS",
  "DataLakeServiceClient", "DataLakeFileClient", "append_data", "flush_data",
  "HierarchicalNamespace", "azure-storage-file-datalake", "ADLS Gen2".
  CRITICAL: Endpoint is dfs.core.windows.net NOT blob. Large files need
  append_data() + flush_data() pattern. Account must have HNS enabled.
---

# Azure Data Lake Storage Gen2 SDK for Python

## Package
```bash
pip install azure-storage-file-datalake azure-identity
```

## Client setup

```python
from azure.storage.filedatalake import (
    DataLakeServiceClient,
    DataLakeFileSystemClient,
    DataLakeDirectoryClient,
    DataLakeFileClient,
)
from azure.identity import DefaultAzureCredential

# CRITICAL: Use dfs.core.windows.net, NOT blob.core.windows.net
service = DataLakeServiceClient(
    account_url="https://myaccount.dfs.core.windows.net",   # dfs endpoint!
    credential=DefaultAzureCredential(),
)
# Account must have Hierarchical Namespace (HNS) enabled
```

## File system (container) management

```python
# Create filesystem
fs = service.create_file_system("my-container")

# Get existing filesystem
fs = service.get_file_system_client("my-container")

# List filesystems
for f in service.list_file_systems():
    print(f.name)

# Delete filesystem
fs.delete_file_system()
```

## Directory operations

```python
# Create directory
dir_client = fs.create_directory("raw/2024/01")

# Get existing directory
dir_client = fs.get_directory_client("raw/2024/01")

# List contents
paths = fs.get_paths("raw/2024")
for path in paths:
    print(path.name, "dir" if path.is_directory else "file", path.content_length)

# Delete directory (and all contents)
dir_client.delete_directory()
```

## Upload small file (< 100 MB)

```python
file_client = fs.get_file_client("raw/2024/01/data.json")

# Simple upload for small files
with open("data.json", "rb") as f:
    content = f.read()

file_client.upload_data(content, overwrite=True)
```

## Upload large file — append + flush pattern

```python
CHUNK_SIZE = 4 * 1024 * 1024   # 4 MB chunks

file_client = fs.get_file_client("raw/2024/01/bigfile.parquet")
file_client.create_file()

offset = 0
with open("bigfile.parquet", "rb") as f:
    while True:
        chunk = f.read(CHUNK_SIZE)
        if not chunk:
            break
        file_client.append_data(chunk, offset=offset, length=len(chunk))
        offset += len(chunk)

# MUST call flush_data after all appends
file_client.flush_data(offset)
```

## Download

```python
file_client = fs.get_file_client("processed/output.parquet")

# Download to bytes
download = file_client.download_file()
content = download.readall()

# Stream to local file
with open("local_output.parquet", "wb") as f:
    file_client.download_file().readinto(f)
```

## ACL and permissions (POSIX-style)

```python
from azure.storage.filedatalake import AccessControlChangeOptions

# Set ACL on directory
dir_client.set_access_control(
    acl="user::rwx,group::r-x,other::---,user:object-id:rwx",
)

# Get ACL
acl = dir_client.get_access_control()
print(acl["acl"], acl["permissions"])

# Set permissions (octal style)
dir_client.set_access_control(permissions="0755")

# Recursive ACL update
dir_client.update_access_control_recursive(
    acl="user:object-id:r-x",
    options=AccessControlChangeOptions(batch_size=100),
)
```

## Move and rename

```python
# Rename/move (atomic operation)
dir_client = fs.get_directory_client("staging")
dir_client.rename_directory("processed")   # atomic move

file_client = fs.get_file_client("staging/data.csv")
file_client.rename_file("processed/data.csv")
```

## Common mistakes

| ❌ Wrong | ✅ Correct |
|---|---|
| `account_url="https://myaccount.blob.core.windows.net"` | `account_url="https://myaccount.dfs.core.windows.net"` |
| `file_client.upload_file(large_data)` for large files | `append_data()` chunks + `flush_data(final_offset)` |
| Forgetting `flush_data()` after appends | Always call `flush_data(total_bytes)` to commit |
| `fs.list_files("dir")` | `fs.get_paths("dir")` |
| Using BlobServiceClient for HNS storage | Use DataLakeServiceClient for ADLS Gen2 |
| HNS disabled storage account | Enable Hierarchical Namespace during account creation |
