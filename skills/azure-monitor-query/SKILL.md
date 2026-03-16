---
name: azure-monitor-query
description: >
  Azure Monitor Query SDK for Python (azure-monitor-query). Use for running KQL queries
  against Log Analytics workspaces and querying Azure Monitor metrics. Triggers on:
  "azure-monitor-query", "LogsQueryClient", "MetricsQueryClient", "KQL query",
  "Log Analytics", "query_workspace", "query_resource", "metrics query", "logs query",
  "workspace_id", "Monitor logs". Use when querying Azure Monitor data programmatically.
---

# Azure Monitor Query SDK for Python

## Package
```bash
uv add azure-monitor-query azure-identity
```

## Two clients

| Client | Purpose |
|---|---|
| `LogsQueryClient` | Run KQL queries against Log Analytics workspaces |
| `MetricsQueryClient` | Query metric time-series from any Azure resource |

## Auth

```python
from azure.monitor.query import LogsQueryClient, MetricsQueryClient
from azure.identity import DefaultAzureCredential

credential = DefaultAzureCredential()
logs_client = LogsQueryClient(credential)
metrics_client = MetricsQueryClient(credential)
```

## Query logs (KQL)

```python
from azure.monitor.query import LogsQueryClient, LogsQueryStatus
from datetime import timedelta

# workspace_id = UUID from Azure Portal > Log Analytics > Properties
workspace_id = "00000000-0000-0000-0000-000000000000"

response = logs_client.query_workspace(
    workspace_id=workspace_id,
    query="AzureActivity | where TimeGenerated > ago(1d) | summarize count() by OperationName",
    timespan=timedelta(days=1),   # timedelta, ISO 8601 string, or QueryTimeRange
)

if response.status == LogsQueryStatus.SUCCESS:
    for table in response.tables:
        # Rows are LISTS, not dicts — use index or zip with column names
        col_names = [col.name for col in table.columns]
        for row in table.rows:
            record = dict(zip(col_names, row))
            print(record)
elif response.status == LogsQueryStatus.PARTIAL:
    print(f"Partial result. Error: {response.error}")
```

### Timespan formats
```python
timedelta(days=1)                         # Python timedelta
"PT1H"                                    # ISO 8601 duration
"2024-01-01T00:00:00Z/2024-01-02T00:00:00Z"  # ISO 8601 interval
```

### Batch queries
```python
from azure.monitor.query import LogsBatchQuery

queries = [
    LogsBatchQuery(workspace_id=workspace_id, query="Heartbeat | count", timespan=timedelta(hours=1)),
    LogsBatchQuery(workspace_id=workspace_id, query="AzureActivity | count", timespan=timedelta(hours=1)),
]
responses = logs_client.query_batch(queries)
for resp in responses:
    if resp.status == LogsQueryStatus.SUCCESS:
        print(resp.tables[0].rows[0])
```

## Query metrics

```python
from azure.monitor.query import MetricsQueryClient, MetricAggregationType

resource_id = "/subscriptions/{sub}/resourceGroups/{rg}/providers/Microsoft.Compute/virtualMachines/{vm}"

response = metrics_client.query_resource(
    resource_uri=resource_id,
    metric_names=["Percentage CPU"],
    timespan=timedelta(hours=1),
    granularity=timedelta(minutes=5),
    aggregations=[MetricAggregationType.AVERAGE, MetricAggregationType.MAXIMUM],
)

for metric in response.metrics:
    print(f"Metric: {metric.name}")
    for ts in metric.timeseries:
        for point in ts.data:
            print(f"  {point.time_stamp}: avg={point.average}, max={point.maximum}")
```

## LogsQueryResult structure
```python
response.status          # LogsQueryStatus.SUCCESS / PARTIAL / FAILURE
response.tables          # List[LogsTable]
response.tables[0].name     # table name
response.tables[0].columns  # List[LogsTableColumn]  — schema
response.tables[0].rows     # List[List]  — data (NOT dicts, use index)
response.error           # set when status != SUCCESS
```

## MetricsQueryResult structure
```python
response.metrics[0].name          # metric name
response.metrics[0].unit          # "Percent", "Bytes", etc.
response.metrics[0].timeseries    # List[TimeSeriesElement]
response.metrics[0].timeseries[0].data   # List[MetricValue]
# MetricValue: .time_stamp, .average, .total, .count, .minimum, .maximum
```

## Common mistakes

| ❌ Wrong | ✅ Correct |
|---|---|
| `workspace_id = "my-workspace"` (name) | Must be UUID from portal Properties |
| `row["OperationName"]` | `row[col_index]` — rows are lists, not dicts |
| `timespan=1` | Use `timedelta(days=1)` or ISO 8601 string |
| `metrics_client.query()` | Method is `query_resource()` |
| `metric_name="CPUPercentage"` | Use exact Azure name: `"Percentage CPU"` (spaces matter) |
| `LogsQueryStatus.SUCCESS == "success"` | It's an enum, compare with `LogsQueryStatus.SUCCESS` |
| Batch queries are atomic | Each query in a batch fails independently — check each `status` |
