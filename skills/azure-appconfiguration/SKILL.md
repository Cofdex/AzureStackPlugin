---
name: azure-appconfiguration
description: >
  Azure App Configuration SDK for Python — centralized key-value configuration,
  feature flags, and dynamic settings for cloud applications. Use this skill
  whenever working with the `azure-appconfiguration` package and tasks involve:
  reading or writing key-value configuration settings with labels, managing feature
  flags (FeatureFlagConfigurationSetting) with percentage/targeting/time-window
  filters, storing Key Vault secret references (SecretReferenceConfigurationSetting),
  performing conditional optimistic-concurrency updates with ETags and MatchConditions,
  managing configuration snapshots, filtering settings by key/label/tags wildcards,
  polling for configuration changes, or making settings read-only. Always invoke this
  skill for "azure-appconfiguration", "AzureAppConfigurationClient", "feature flag",
  "feature flags", "configuration settings", "key-value settings", "config store",
  "appconfiguration", "app config", or any task that reads/writes settings from an
  Azure App Configuration store.
---

# Azure App Configuration SDK for Python

Package: `pip install azure-appconfiguration` (v1.8.1+)

Centralised store for application settings and feature flags. Supports labels (environments), tags, snapshots, conditional updates, and Key Vault secret references.

## Client creation

```python
from azure.appconfiguration import AzureAppConfigurationClient

# Development: connection string
client = AzureAppConfigurationClient.from_connection_string(
    os.environ["APPCONFIGURATION_CONNECTION_STRING"]
)

# Production: managed identity / service principal
from azure.identity import DefaultAzureCredential
client = AzureAppConfigurationClient(
    base_url="https://mystore.azconfig.io",
    credential=DefaultAzureCredential()
)
```

Async client: `from azure.appconfiguration.aio import AzureAppConfigurationClient` — identical API, all methods are `async`.

## Key imports

```python
from azure.appconfiguration import (
    AzureAppConfigurationClient,
    ConfigurationSetting,
    FeatureFlagConfigurationSetting,
    SecretReferenceConfigurationSetting,
    ConfigurationSnapshot,
    ConfigurationSettingsFilter,
    FILTER_PERCENTAGE,    # "Microsoft.Percentage"
    FILTER_TARGETING,     # "Microsoft.Targeting"
    FILTER_TIME_WINDOW,   # "Microsoft.TimeWindow"
)
from azure.core import MatchConditions
from azure.core.exceptions import ResourceModifiedError, ResourceExistsError, ResourceNotFoundError
```

## CRUD operations

### Add (fails if key+label already exists)
```python
setting = ConfigurationSetting(
    key="app:database:host",
    label="prod",           # label is the environment dimension; None = default
    value="db.example.com",
    content_type="text/plain",
    tags={"team": "platform"}
)
result = client.add_configuration_setting(setting)
```

### Set (upsert — create or overwrite)
```python
setting = ConfigurationSetting(key="app:timeout", label="prod", value="30")
result = client.set_configuration_setting(setting)
```

### Get
```python
setting = client.get_configuration_setting(key="app:database:host", label="prod")
print(setting.value, setting.etag, setting.last_modified)

# Historical value (point-in-time)
from datetime import datetime, timedelta, timezone
setting = client.get_configuration_setting(
    key="app:database:host",
    accept_datetime=datetime.now(timezone.utc) - timedelta(hours=1)
)
```

### List with filters
```python
# Wildcard key filter — list all keys under a prefix
for s in client.list_configuration_settings(key_filter="app:*"):
    print(s.key, s.label, s.value)

# Key + label + tags
for s in client.list_configuration_settings(
    key_filter="app:*",
    label_filter="prod",
    tags_filter=["env=prod", "team=platform"]
):
    print(s.key, s.value)

# List revision history
for rev in client.list_revisions(key_filter="app:database:*"):
    print(rev.key, rev.last_modified)
```

### Delete
```python
client.delete_configuration_setting(key="app:timeout", label="prod")
```

### Read-only lock / unlock
```python
setting = client.get_configuration_setting(key="app:timeout")
client.set_read_only(setting, read_only=True)   # lock
client.set_read_only(setting, read_only=False)  # unlock
```

## Feature flags

Feature flags are stored with key prefix `.appconfig.featureflag/` and a special content type — the SDK handles this automatically through `FeatureFlagConfigurationSetting`.

```python
from azure.appconfiguration import FeatureFlagConfigurationSetting, FILTER_PERCENTAGE

# Create a flag with gradual percentage rollout
flag = FeatureFlagConfigurationSetting(
    feature_id="new-checkout",    # key becomes ".appconfig.featureflag/new-checkout"
    enabled=True,
    display_name="New Checkout Flow",
    description="Redesigned checkout experience",
    label="prod",
    filters=[
        {"name": FILTER_PERCENTAGE, "parameters": {"value": 25}}  # 25% rollout
    ]
)
client.set_configuration_setting(flag)

# Read a feature flag
setting = client.get_configuration_setting(
    key=".appconfig.featureflag/new-checkout", label="prod"
)
if isinstance(setting, FeatureFlagConfigurationSetting):
    print(f"enabled={setting.enabled}, id={setting.feature_id}")
    print(f"filters={setting.filters}")

# List all feature flags
for s in client.list_configuration_settings(key_filter=".appconfig.featureflag/*"):
    if isinstance(s, FeatureFlagConfigurationSetting):
        print(s.feature_id, s.enabled)
```

### Filter types for feature flags
- **`FILTER_PERCENTAGE`**: `{"name": FILTER_PERCENTAGE, "parameters": {"value": 50}}` — roll out to N% of users
- **`FILTER_TARGETING`**: `{"name": FILTER_TARGETING, "parameters": {"Audience": {"Users": ["alice@example.com"], "Groups": [{"Name": "beta", "RolloutPercentage": 100}], "DefaultRolloutPercentage": 0}}}` — specific users/groups
- **`FILTER_TIME_WINDOW`**: `{"name": FILTER_TIME_WINDOW, "parameters": {"Start": "Wed, 01 Jan 2025 00:00:00 GMT", "End": "Wed, 01 Feb 2025 00:00:00 GMT"}}` — time-based activation

## Secret references

Point to Key Vault secrets without storing the secret value in App Configuration:

```python
from azure.appconfiguration import SecretReferenceConfigurationSetting

ref = SecretReferenceConfigurationSetting(
    key="db:password",
    label="prod",
    secret_id="https://myvault.vault.azure.net/secrets/db-password/abc123"
)
client.set_configuration_setting(ref)

# Reading back
setting = client.get_configuration_setting(key="db:password", label="prod")
if isinstance(setting, SecretReferenceConfigurationSetting):
    print(f"Resolve from Key Vault: {setting.secret_id}")
```

## Conditional updates (optimistic concurrency)

Use `etag` + `MatchConditions` to prevent overwriting someone else's changes — critical in multi-process scenarios:

```python
from azure.core import MatchConditions
from azure.core.exceptions import ResourceModifiedError

setting = client.get_configuration_setting(key="app:config")
setting.value = "updated"

try:
    client.set_configuration_setting(
        setting,
        match_condition=MatchConditions.IfNotModified  # only save if etag still matches
    )
except ResourceModifiedError:
    print("Conflict: setting was modified by another process — reload and retry")

# Conditional get: skip response if unchanged (efficient polling)
updated = client.get_configuration_setting(
    key="app:config",
    etag=setting.etag,
    match_condition=MatchConditions.IfModified  # returns None if not changed
)
if updated is None:
    print("No change since last read")
```

## Snapshots

Snapshots capture a point-in-time consistent set of configuration settings, useful for deployments:

```python
from azure.appconfiguration import ConfigurationSnapshot, ConfigurationSettingsFilter

# Create a snapshot of all prod settings
filters = [ConfigurationSettingsFilter(key="app:*", label="prod")]
poller = client.begin_create_snapshot(name="release-v2.1", filters=filters)
snapshot = poller.result()
print(f"Snapshot {snapshot.name}, status={snapshot.status}, count={snapshot.items_count}")

# Read from a snapshot
for s in client.list_configuration_settings(snapshot_name="release-v2.1"):
    print(s.key, s.value)

# Archive (soft-delete) and recover
client.archive_snapshot("release-v2.1")
client.recover_snapshot("release-v2.1")

# List snapshots
for snap in client.list_snapshots():
    print(snap.name, snap.status, snap.created_on)
```

## Async usage

```python
import asyncio
from azure.appconfiguration.aio import AzureAppConfigurationClient
from azure.identity.aio import DefaultAzureCredential

async def load_config():
    async with AzureAppConfigurationClient(
        base_url="https://mystore.azconfig.io",
        credential=DefaultAzureCredential()
    ) as client:
        setting = await client.get_configuration_setting(key="app:timeout", label="prod")
        
        # Async list iteration
        async for s in client.list_configuration_settings(key_filter="app:*"):
            print(s.key, s.value)
        
        return setting.value

asyncio.run(load_config())
```

## Configuration change polling

Poll for changes by tracking ETags — no push notification mechanism exists in the SDK itself:

```python
import time

etag_cache = {}

def poll_for_changes(client, key, label="prod", interval=30):
    while True:
        cached_etag = etag_cache.get((key, label))
        
        if cached_etag:
            setting = client.get_configuration_setting(
                key=key, label=label,
                etag=cached_etag,
                match_condition=MatchConditions.IfModified
            )
            if setting is None:
                print(f"{key}: no change")
                time.sleep(interval)
                continue
        else:
            setting = client.get_configuration_setting(key=key, label=label)
        
        etag_cache[(key, label)] = setting.etag
        print(f"{key}: changed → {setting.value}")
        time.sleep(interval)
```

## Key notes

- **Labels are the environment dimension**: use `label="prod"`, `label="dev"` to separate environments. `label=None` is the default/no-label setting.
- **Key hierarchy**: use `:` or `/` as separator (e.g., `app:database:host`). Wildcard `*` matches within a segment, `app:*` matches all keys starting with `app:`.
- **`add` vs `set`**: `add_configuration_setting` raises `ResourceExistsError` if the key+label already exists; `set_configuration_setting` always upserts.
- **Feature flag key prefix**: always `.appconfig.featureflag/` — use this when calling `get_configuration_setting` directly.
- **Snapshots are immutable**: once created, a snapshot's contents never change. Archive to hide, recover to restore.
- **Async list iteration**: use `async for` (not `async with`) when iterating async paged results.
