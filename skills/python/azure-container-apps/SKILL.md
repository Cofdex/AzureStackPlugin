---
name: azure-container-apps
description: >
  Azure Container Apps management SDK for Python (azure-mgmt-appcontainers). Use for
  creating managed environments, deploying container apps, configuring ingress, scaling
  rules, Dapr components, and secrets. Triggers on: "container apps", "ContainerAppsAPIClient",
  "ManagedEnvironment", "begin_create_or_update", "container app ingress", "scale rules",
  "dapr", "ACA", "azure-mgmt-appcontainers". CRITICAL: All mutating ops return LRO
  pollers — must call .result(). cpu/memory are strings not numbers. env vars are
  List[EnvironmentVar] not dicts.
---

# Azure Container Apps Management SDK for Python

## Package
```bash
pip install azure-mgmt-appcontainers azure-identity
```

## Client setup

```python
from azure.mgmt.appcontainers import ContainerAppsAPIClient
from azure.identity import DefaultAzureCredential
import os

client = ContainerAppsAPIClient(
    credential=DefaultAzureCredential(),
    subscription_id=os.environ["AZURE_SUBSCRIPTION_ID"],
)
```

## Create Managed Environment

```python
from azure.mgmt.appcontainers.models import ManagedEnvironment

op = client.managed_environments.begin_create_or_update(   # begin_ prefix = LRO
    resource_group_name="myRG",
    environment_name="my-env",
    environment=ManagedEnvironment(location="eastus"),
)
env = op.result(timeout=300)   # blocks until provisioned
env_id = env.id                # full resource ID needed for container apps
```

## Create Container App

```python
from azure.mgmt.appcontainers.models import (
    ContainerApp, Configuration, Template,
    Container, ContainerResources, Scale,
    Ingress, EnvironmentVar, Secret,
)

app = ContainerApp(
    location="eastus",
    managed_environment_id=env.id,    # full ARM resource ID
    configuration=Configuration(
        ingress=Ingress(
            external=True,
            target_port=8080,          # target_port, NOT port
        ),
        secrets=[
            Secret(name="db-password", value="secret123"),
        ],
    ),
    template=Template(
        containers=[
            Container(
                name="myapp",
                image="mcr.microsoft.com/azuredocs/containerapps-helloworld:latest",
                resources=ContainerResources(
                    cpu="0.5",         # string, NOT float 0.5
                    memory="1.0Gi",    # exact format "1.0Gi", NOT "1G" or "1024Mi"
                ),
                env=[
                    EnvironmentVar(name="ENV", value="production"),        # plain value
                    EnvironmentVar(name="DB_PASS", secret_ref="db-password"),  # from secret
                ],
            )
        ],
        scale=Scale(min_replicas=1, max_replicas=10),
    ),
)

op = client.container_apps.begin_create_or_update(
    resource_group_name="myRG",
    container_app_name="my-app",
    container_app=app,
)
result = op.result(timeout=300)
print(result.configuration.ingress.fqdn)   # public URL
```

## List and Get

```python
# List in resource group
for ca in client.container_apps.list_by_resource_group("myRG"):
    print(ca.name, ca.provisioning_state)

# Get specific app
app = client.container_apps.get("myRG", "my-app")
```

## Update

```python
from azure.mgmt.appcontainers.models import ContainerAppUpdate

op = client.container_apps.begin_update(
    resource_group_name="myRG",
    container_app_name="my-app",
    container_app_update=ContainerAppUpdate(
        template=Template(
            containers=[Container(name="myapp", image="myregistry.azurecr.io/myapp:v2")]
        )
    ),
)
op.result()
```

## Delete

```python
op = client.container_apps.begin_delete("myRG", "my-app")
op.result()
```

## Dapr Component

```python
from azure.mgmt.appcontainers.models import DaprComponent, DaprMetadata

op = client.dapr_components.create_or_update(
    resource_group_name="myRG",
    environment_name="my-env",
    component_name="statestore",
    dapr_component=DaprComponent(
        component_type="state.azure.blobstorage",
        version="v1",
        metadata=[
            DaprMetadata(name="accountName", value="myaccount"),
            DaprMetadata(name="accountKey",  secret_ref="storage-key"),
        ],
    ),
)
```

## Common mistakes

| ❌ Wrong | ✅ Correct |
|---|---|
| `ContainerAppsClient(...)` | `ContainerAppsAPIClient(credential=..., subscription_id=...)` |
| `client.create_or_update(...)` | `client.container_apps.begin_create_or_update(...)` |
| Forgetting `.result()` on LRO | Always call `.result(timeout=300)` |
| `ingress.port = 8000` | `ingress.target_port = 8000` |
| `container.env = {"KEY": "val"}` (dict) | `[EnvironmentVar(name="KEY", value="val")]` |
| `cpu = 0.5` (float) | `cpu = "0.5"` (string) |
| `memory = "1G"` | `memory = "1.0Gi"` |
| `environment_id = "my-env"` | Full ARM resource ID `/subscriptions/.../managedEnvironments/my-env` |
| Referencing secret without defining it | Add to `configuration.secrets` first, then use `secret_ref` |
