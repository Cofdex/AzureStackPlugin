---
name: azure-aks
description: >
  Azure Kubernetes Service management SDK for Python (azure-mgmt-containerservice).
  Use for creating AKS clusters, managing node pools, getting kubeconfig credentials,
  and scaling. Triggers on: "AKS", "ContainerServiceClient", "ManagedCluster",
  "node pool", "kubernetes cluster", "get kubeconfig", "begin_create_or_update AKS",
  "azure-mgmt-containerservice". CRITICAL: All create/update/delete ops are LRO —
  must call .result(). Kubeconfig requires separate credential call.
---

# Azure Kubernetes Service (AKS) Management SDK for Python

## Package
```bash
pip install azure-mgmt-containerservice azure-identity
```

## Client setup

```python
from azure.mgmt.containerservice import ContainerServiceClient
from azure.identity import DefaultAzureCredential
import os

client = ContainerServiceClient(
    credential=DefaultAzureCredential(),
    subscription_id=os.environ["AZURE_SUBSCRIPTION_ID"],
)
```

## Create AKS cluster

```python
from azure.mgmt.containerservice.models import (
    ManagedCluster,
    ManagedClusterAgentPoolProfile,
    ManagedClusterServicePrincipalProfile,
    ContainerServiceNetworkProfile,
)

cluster = ManagedCluster(
    location="eastus",
    dns_prefix="mycluster",
    agent_pool_profiles=[
        ManagedClusterAgentPoolProfile(
            name="nodepool1",               # max 12 chars, lowercase alphanumeric
            count=3,
            vm_size="Standard_DS2_v2",
            os_type="Linux",
            mode="System",                  # "System" or "User"
        )
    ],
    identity={
        "type": "SystemAssigned",           # use managed identity, not service principal
    },
    network_profile=ContainerServiceNetworkProfile(
        network_plugin="azure",             # "azure" or "kubenet"
        load_balancer_sku="standard",
    ),
    kubernetes_version="1.29.0",            # explicit version recommended
)

op = client.managed_clusters.begin_create_or_update(
    resource_group_name="myRG",
    resource_name="my-cluster",
    parameters=cluster,
)
result = op.result(timeout=900)   # AKS creation takes 5-15 min
print(result.fqdn)
```

## Get kubeconfig (admin credentials)

```python
# Admin credentials (for CI/CD or initial setup)
creds = client.managed_clusters.list_cluster_admin_credentials(
    resource_group_name="myRG",
    resource_name="my-cluster",
)
kubeconfig = creds.kubeconfigs[0].value   # bytes — write to file or decode

import os
kubeconfig_path = os.path.expanduser("~/.kube/config")
with open(kubeconfig_path, "wb") as f:
    f.write(kubeconfig)

# User credentials (RBAC-scoped)
user_creds = client.managed_clusters.list_cluster_user_credentials(
    resource_group_name="myRG",
    resource_name="my-cluster",
)
```

## List and Get

```python
# List in subscription
for cluster in client.managed_clusters.list():
    print(cluster.name, cluster.kubernetes_version, cluster.provisioning_state)

# List in resource group
for cluster in client.managed_clusters.list_by_resource_group("myRG"):
    print(cluster.name)

# Get specific cluster
cluster = client.managed_clusters.get("myRG", "my-cluster")
print(cluster.agent_pool_profiles[0].count)
```

## Scale node pool

```python
from azure.mgmt.containerservice.models import AgentPool

op = client.agent_pools.begin_create_or_update(
    resource_group_name="myRG",
    resource_name="my-cluster",
    agent_pool_name="nodepool1",
    parameters=AgentPool(count=5),         # scale to 5 nodes
)
op.result()
```

## Add node pool

```python
from azure.mgmt.containerservice.models import AgentPool

op = client.agent_pools.begin_create_or_update(
    resource_group_name="myRG",
    resource_name="my-cluster",
    agent_pool_name="gpupool",
    parameters=AgentPool(
        count=2,
        vm_size="Standard_NC6s_v3",
        node_labels={"workload": "gpu"},
        mode="User",
    ),
)
op.result()
```

## Delete cluster

```python
op = client.managed_clusters.begin_delete("myRG", "my-cluster")
op.result()
```

## Common mistakes

| ❌ Wrong | ✅ Correct |
|---|---|
| `AKSClient(...)` | `ContainerServiceClient(credential=..., subscription_id=...)` |
| `client.create(...)` | `client.managed_clusters.begin_create_or_update(...)` |
| Forgetting `.result()` on LRO | Always call `.result(timeout=900)` for cluster creation |
| `agent_pool_profiles[0].name = "NodePool1"` | Node pool name must be lowercase alphanumeric, max 12 chars |
| `creds.kubeconfig` | `creds.kubeconfigs[0].value` — it's a list |
| Kubeconfig value used directly as string | It's `bytes` — decode or write to file |
| `identity.type = "UserAssigned"` without specifying identity | SystemAssigned is simpler; UserAssigned needs identity resource ID |
