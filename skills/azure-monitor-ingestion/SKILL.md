---
name: azure-monitor-ingestion
description: >
  Azure Monitor Ingestion SDK for Python (`azure-monitor-ingestion`). Use this skill when
  sending custom logs or telemetry to Azure Log Analytics workspace via the Logs Ingestion API
  and Data Collection Rules (DCR). Triggers on: "LogsIngestionClient", "azure-monitor-ingestion",
  "custom logs", "DCR", "data collection rule", "data collection endpoint", "DCE",
  "Log Analytics ingestion", "upload logs", "custom table", "Monitoring Metrics Publisher",
  "logs ingestion API". Use whenever the task involves pushing log data into Azure Monitor,
  even if the user just says "send logs to Log Analytics" or "ingest custom events into Azure".
---

# Azure Monitor Ingestion SDK for Python

Send custom log data to Azure Log Analytics workspaces using the Logs Ingestion API and
Data Collection Rules (DCR). This SDK handles gzip compression, automatic batching, and
chunking — you just pass a list of dicts.

## Installation

```bash
pip install azure-monitor-ingestion azure-identity
```

## Key concepts before writing code

Three resources must exist in Azure before you can ingest logs:

| Resource | What it is | Where to find its value |
|----------|-----------|------------------------|
| **DCE** (Data Collection Endpoint) | HTTPS endpoint that receives your data | Azure Portal → Monitor → Data Collection Endpoints → select → copy **Logs Ingestion** URI |
| **DCR Immutable ID** | Identifier for the data collection rule | Azure Portal → Monitor → Data Collection Rules → select → Properties → copy **Immutable ID** |
| **Stream name** | The destination table/stream in the DCR | DCR → Data Sources tab, e.g. `Custom-MyTable_CL` |

The **DCE endpoint** format looks like:
```
https://my-dce-name.eastus-2.ingest.monitor.azure.com
```
**Not** the Log Analytics workspace URL — that's a different thing entirely.

The **DCR Immutable ID** format:
```
dcr-a1b2c3d4e5f6...   (starts with "dcr-", followed by hex)
```
**Not** the DCR display name, not the full ARM resource ID — only the immutable ID.

The **stream name** for custom tables always follows `Custom-<TableName>_CL`. Built-in streams like `Custom-CommonSecurityLog` skip the `_CL` suffix.

## Client Initialization

```python
from azure.monitor.ingestion import LogsIngestionClient
from azure.identity import DefaultAzureCredential

client = LogsIngestionClient(
    endpoint="https://my-dce.eastus-2.ingest.monitor.azure.com",
    credential=DefaultAzureCredential()
)
```

The credential must have the **"Monitoring Metrics Publisher"** RBAC role assigned on the DCR resource (not the workspace). Without it you get HTTP 403.

## Uploading logs

```python
logs = [
    {
        "TimeGenerated": "2024-01-15T10:30:00.000Z",  # UTC ISO 8601
        "Computer": "web-server-01",
        "Message": "Request processed",
        "StatusCode": 200,
        "DurationMs": 45
    },
    # ... more records
]

client.upload(
    rule_id="dcr-a1b2c3d4e5f6789abcdef01234567890",  # DCR Immutable ID
    stream_name="Custom-AppLogs_CL",                   # Stream name from DCR
    logs=logs
)
```

The SDK automatically:
- Chunks large batches (1 MB limit per request)
- gzip-compresses each chunk
- Sends multiple HTTP POSTs if needed

`upload()` returns `None` — it raises on error by default.

## Error handling with on_error

By default, the first failed chunk raises an exception and stops processing. If you want
to continue uploading other chunks even when one fails (e.g. for large batches), pass an
`on_error` callback:

```python
from azure.monitor.ingestion import LogsUploadError

failed_records = []

def handle_upload_error(error: LogsUploadError) -> None:
    print(f"Chunk failed: {error.error}")        # The underlying HttpResponseError
    failed_records.extend(error.failed_logs)      # The records in that chunk

client.upload(
    rule_id="dcr-...",
    stream_name="Custom-AppLogs_CL",
    logs=logs,
    on_error=handle_upload_error
)

# Optionally retry failed records
if failed_records:
    client.upload(rule_id="dcr-...", stream_name="Custom-AppLogs_CL", logs=failed_records)
```

`LogsUploadError` has two fields:
- `.error` — the `HttpResponseError` with `.status_code` and `.message`
- `.failed_logs` — the list of records in the failed chunk

## Async client

```python
from azure.monitor.ingestion.aio import LogsIngestionClient
from azure.identity.aio import DefaultAzureCredential

async def send_logs(logs: list[dict]) -> None:
    async with LogsIngestionClient(
        endpoint="https://my-dce.eastus-2.ingest.monitor.azure.com",
        credential=DefaultAzureCredential()
    ) as client:
        await client.upload(
            rule_id="dcr-...",
            stream_name="Custom-AppLogs_CL",
            logs=logs
        )
```

Use `async with` (or `await client.close()`) to avoid HTTP transport leaks. The async
`on_error` callback can be either sync or async.

## Handling large datasets

The SDK auto-chunks at 1 MB, but for very large datasets it's worth batching explicitly
to avoid memory pressure and get better error granularity:

```python
def chunked(lst: list, size: int):
    for i in range(0, len(lst), size):
        yield lst[i:i + size]

for batch in chunked(all_records, 500):
    client.upload(rule_id=DCR_ID, stream_name=STREAM, logs=batch,
                  on_error=handle_upload_error)
```

## Data format requirements

Logs must be a **list of dicts** with JSON-serializable values:

```python
# ✓ Correct
logs = [{"TimeGenerated": "2024-01-15T10:30:00Z", "Level": "INFO", "Count": 42}]

# ✗ Wrong — JSON string, not a list
logs = '[{"TimeGenerated": "...", "Level": "INFO"}]'

# ✗ Wrong — non-serializable types
logs = [{"Time": datetime.now(), "Data": b"bytes"}]  # Use .isoformat() and str()
```

`TimeGenerated` (UTC ISO 8601) is the standard timestamp field. If omitted, Azure sets it
to ingestion time. Other field names must match the custom table's column schema.

## Common mistakes

| Mistake | Effect | Fix |
|---------|--------|-----|
| Using workspace URL as endpoint | `HttpResponseError: 404` | Use DCE endpoint: `https://....ingest.monitor.azure.com` |
| Using DCR display name as rule_id | `HttpResponseError: 404` | Use Immutable ID: `dcr-abc123...` |
| Stream name missing `Custom-` prefix | `HttpResponseError: 404` | `Custom-MyTable_CL` not `MyTable_CL` |
| Stream name missing `_CL` suffix | `HttpResponseError: 404` | `Custom-MyTable_CL` not `Custom-MyTable` |
| Missing "Monitoring Metrics Publisher" role | `HttpResponseError: 403` | Assign role on DCR resource, not workspace |
| Passing a JSON string instead of list | `TypeError` | Pass `list[dict]`, not `json.dumps(...)` |
| Non-UTC or non-ISO timestamp | Silent data issues | Use `datetime.now(timezone.utc).isoformat()` |
| Using sync client in async code | Blocks event loop | Import from `azure.monitor.ingestion.aio` |

## Complete example

```python
import os
from datetime import datetime, timezone
from azure.identity import DefaultAzureCredential
from azure.monitor.ingestion import LogsIngestionClient, LogsUploadError

DCE_ENDPOINT = os.environ["AZURE_MONITOR_DCE_ENDPOINT"]  # DCE endpoint URL
DCR_RULE_ID  = os.environ["AZURE_MONITOR_DCR_RULE_ID"]   # dcr-xxx immutable ID
STREAM_NAME  = os.environ["AZURE_MONITOR_STREAM_NAME"]   # Custom-TableName_CL

def on_error(err: LogsUploadError) -> None:
    print(f"Upload error {err.error.status_code}: {len(err.failed_logs)} records lost")

client = LogsIngestionClient(endpoint=DCE_ENDPOINT, credential=DefaultAzureCredential())

logs = [
    {
        "TimeGenerated": datetime.now(timezone.utc).isoformat(),
        "Computer": "app-server-01",
        "Severity": "Warning",
        "Message": "High memory usage detected",
        "MemoryPercent": 87.5,
    }
]

client.upload(rule_id=DCR_RULE_ID, stream_name=STREAM_NAME, logs=logs, on_error=on_error)
print("Logs uploaded successfully")
```
