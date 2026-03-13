---
name: azure-file-shares
description: >
  Azure File Shares SDK for Python (azure-storage-file-share). Use for creating shares,
  uploading/downloading files, listing directories, and managing file metadata.
  Triggers on: "file shares", "ShareServiceClient", "ShareClient", "ShareDirectoryClient",
  "ShareFileClient", "upload_file", "download_file", "list_directories_and_files",
  "azure-storage-file-share". CRITICAL: list_files() does NOT exist — use
  list_directories_and_files(). download_file() returns a stream — call readall().
---

# Azure File Shares SDK for Python

## Package
```bash
pip install azure-storage-file-share azure-identity
```

## Client hierarchy

```python
from azure.storage.fileshare import (
    ShareServiceClient,
    ShareClient,
    ShareDirectoryClient,
    ShareFileClient,
)
from azure.identity import DefaultAzureCredential

# Service → Share → Directory → File
service = ShareServiceClient(
    account_url="https://myaccount.file.core.windows.net",
    credential=DefaultAzureCredential(),
)

share = service.get_share_client("my-share")
directory = share.get_directory_client("subdir")
file_client = share.get_file_client("subdir/myfile.txt")
# or: directory.get_file_client("myfile.txt")
```

## Share management

```python
# Create share
share.create_share()
share.create_share(quota=5120)   # quota in GB

# List shares
for s in service.list_shares():
    print(s.name, s.properties.quota)

# Delete share
share.delete_share()
```

## Directory operations

```python
# Create directory (and parents if needed)
share.get_directory_client("dir/subdir").create_directory()

# List — use list_directories_and_files(), NOT list_files()
directory = share.get_directory_client("")   # root
for item in directory.list_directories_and_files():
    print(item.name, item.is_directory)

# List with prefix filter
for item in directory.list_directories_and_files(name_starts_with="report"):
    print(item.name)
```

## Upload file

```python
file_client = share.get_file_client("reports/report.csv")

# Upload from bytes/string
content = b"id,name\n1,Alice\n"
file_client.upload_file(content)

# Upload from file object
with open("local_report.csv", "rb") as f:
    file_client.upload_file(f)

# Upload large file (use upload_range for chunked)
with open("bigfile.bin", "rb") as f:
    file_client.upload_file(f)   # SDK handles chunking automatically
```

## Download file

```python
file_client = share.get_file_client("reports/report.csv")

# download_file() returns a stream — MUST call readall()
download = file_client.download_file()
content = download.readall()   # bytes

# Stream to local file
with open("local_copy.csv", "wb") as f:
    download = file_client.download_file()
    download.readinto(f)       # stream directly to file
```

## File properties and metadata

```python
# Get properties
props = file_client.get_file_properties()
print(props.size, props.last_modified)

# Set metadata
file_client.set_file_metadata({"author": "alice", "version": "2"})
```

## Copy and delete

```python
# Copy within same account
source_url = file_client.url
dest_client = share.get_file_client("archive/report.csv")
dest_client.start_copy_from_url(source_url)

# Delete file
file_client.delete_file()

# Delete directory (must be empty)
directory.delete_directory()
```

## Common mistakes

| ❌ Wrong | ✅ Correct |
|---|---|
| `directory.list_files()` | `directory.list_directories_and_files()` |
| `content = file_client.download_file()` | `content = file_client.download_file().readall()` |
| `ShareFileClient(account_url, share_name="...", file_path="...")` | Use `service.get_share_client().get_file_client()` |
| `share.get_file_client("file.txt")` (root) | `share.get_file_client("file.txt")` works for root files; use path for subdirs |
| `upload_file(content.encode())` | `upload_file(content)` — pass bytes directly |
