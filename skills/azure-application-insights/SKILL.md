---
name: azure-application-insights
description: >
  Azure Application Insights via OpenTelemetry for Python (azure-monitor-opentelemetry).
  Use for distributed tracing, custom metrics, structured logging, and exception tracking
  in Python applications. Triggers on: "application insights", "app insights",
  "azure-monitor-opentelemetry", "configure_azure_monitor", "OpenTelemetry",
  "distributed tracing", "custom telemetry", "APPLICATIONINSIGHTS_CONNECTION_STRING",
  "telemetry", "spans", "metrics". Use the OpenTelemetry-based SDK — NOT opencensus.
---

# Azure Application Insights (OpenTelemetry)

## Package
```bash
uv add azure-monitor-opentelemetry opentelemetry-api
```

**Do NOT use** `opencensus-ext-azure` — it is end-of-life.

## Setup (call once at startup)

```python
from azure.monitor.opentelemetry import configure_azure_monitor

configure_azure_monitor(
    connection_string="InstrumentationKey=00000000-0000-0000-0000-000000000000;IngestionEndpoint=https://eastus.in.applicationinsights.azure.com/"
)
# Or use env var: APPLICATIONINSIGHTS_CONNECTION_STRING
```

Get connection string from: Azure Portal → Application Insights → Properties → Connection String.

## Distributed tracing

```python
from opentelemetry import trace

tracer = trace.get_tracer(__name__)

def process_order(order_id: str):
    with tracer.start_as_current_span("process_order") as span:
        span.set_attribute("order.id", order_id)
        span.set_attribute("order.source", "web")
        
        # Nested span
        with tracer.start_as_current_span("validate_order"):
            validate(order_id)
        
        return fulfill(order_id)
```

## Structured logging with custom dimensions

```python
import logging

logger = logging.getLogger(__name__)

# Custom dimensions appear in Application Insights as custom properties
logger.info(
    "Order processed",
    extra={
        "custom_dimensions": {
            "order_id": "12345",
            "customer_tier": "premium",
            "processing_time_ms": 143
        }
    }
)

# Exception with stack trace
try:
    risky_operation()
except Exception:
    logger.exception("Operation failed")   # captures full stack trace
```

## Custom metrics

```python
from opentelemetry import metrics

meter = metrics.get_meter(__name__)

# Counter (cumulative)
request_counter = meter.create_counter(
    name="requests.total",
    description="Total requests processed",
    unit="1"
)
request_counter.add(1, {"endpoint": "/api/orders", "status": "200"})

# Histogram (value distribution)
latency_histogram = meter.create_histogram(
    name="request.duration",
    description="Request duration",
    unit="ms"
)
latency_histogram.record(150, {"endpoint": "/api/orders"})
```

## Exception tracking via spans

```python
from opentelemetry.trace import Status, StatusCode

with tracer.start_as_current_span("risky_op") as span:
    try:
        risky_operation()
    except Exception as e:
        span.record_exception(e)
        span.set_status(Status(StatusCode.ERROR, str(e)))
        raise
```

## Environment variable config

```bash
APPLICATIONINSIGHTS_CONNECTION_STRING="InstrumentationKey=..."   # preferred
# Do NOT use APPINSIGHTS_INSTRUMENTATIONKEY (deprecated)
```

## Common mistakes

| ❌ Wrong | ✅ Correct |
|---|---|
| `from opencensus.ext.azure...` | `from azure.monitor.opentelemetry import configure_azure_monitor` |
| `configure_azure_monitor()` in every module | Call **once** at application startup only |
| `APPINSIGHTS_INSTRUMENTATIONKEY` env var | Use `APPLICATIONINSIGHTS_CONNECTION_STRING` |
| Expect telemetry to send immediately | Data is **batched** — sent every ~10 seconds or on `shutdown()` |
| `span.set_attribute("dimensions", {...})` for logging | Use `extra={"custom_dimensions": {...}}` in `logger.info()` |
| Instrumentation key alone works everywhere | Use full **connection string** — includes regional endpoint |
| `configure_azure_monitor(sampling_rate=0.5)` | Configure sampling via `OTEL_TRACES_SAMPLER` env var |
