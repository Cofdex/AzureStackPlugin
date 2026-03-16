---
name: azure-ai-ml
description: >
  Build Azure Machine Learning solutions using the Azure ML Python SDK v2 (azure-ai-ml).
  Use this skill whenever working with MLClient, submitting training jobs, building ML pipelines,
  registering models, managing datasets, configuring compute clusters, creating environments,
  or deploying to online/batch endpoints. Also use for sweep jobs (hyperparameter tuning),
  components, datastores, and AutoML. Triggers: "azure-ai-ml", "MLClient", "AzureML", "ML workspace",
  "training job", "command job", "pipeline job", "model registry", "AmlCompute", "ComputeInstance",
  "dataset", "datastore", "online endpoint", "batch endpoint", "sweep job", "ml component",
  "azure machine learning", "AzureML SDK v2".
---

# Azure Machine Learning SDK v2 for Python

The Azure ML Python SDK v2 (`azure-ai-ml`) is the main way to programmatically interact with
Azure Machine Learning workspaces — submitting training jobs, managing models, data, compute,
environments, and deploying endpoints.

## Install

```bash
uv add azure-ai-ml azure-identity
```

## Connect to a Workspace

Every operation goes through `MLClient`. You need subscription ID, resource group, and workspace name:

```python
from azure.ai.ml import MLClient
from azure.identity import DefaultAzureCredential

ml_client = MLClient(
    credential=DefaultAzureCredential(),
    subscription_id="<subscription-id>",
    resource_group_name="<resource-group>",
    workspace_name="<workspace-name>",
)
```

**Alternative — load from config file** (useful in notebooks/CI, requires `config.json` in workspace):
```python
ml_client = MLClient.from_config(credential=DefaultAzureCredential())
```

---

## Command Jobs

A `command` job runs a script on managed compute. It's the basic unit of training in AML.

```python
from azure.ai.ml import command, Input, Output
from azure.ai.ml.constants import AssetTypes

job = command(
    code="./src",                   # local directory uploaded automatically
    command="python train.py --data ${{inputs.training_data}} --output ${{outputs.model_dir}}",
    inputs={
        "training_data": Input(
            type=AssetTypes.URI_FILE,
            path="./data/train.csv",    # local path auto-uploaded, or azureml:// / https:// / abfss://
        )
    },
    outputs={
        "model_dir": Output(type=AssetTypes.URI_FOLDER)
    },
    environment="azureml://registries/azureml/environments/sklearn-1.5/labels/latest",
    compute="cpu-cluster",
    display_name="my-training-job",
    experiment_name="my-experiment",
)

returned_job = ml_client.jobs.create_or_update(job)
print(returned_job.studio_url)      # link to AML Studio
```

**Input/Output types** (`AssetTypes`):

| Type | Use for |
|---|---|
| `URI_FILE` | Single file (CSV, parquet, etc.) |
| `URI_FOLDER` | Directory of files |
| `MLTABLE` | Tabular data with schema |
| `MLFLOW_MODEL` | MLflow model artifact |
| `CUSTOM_MODEL` | Any other model format |
| `TRITON_MODEL` | Triton inference server model |

**Wait for job completion:**
```python
ml_client.jobs.stream(returned_job.name)   # streams logs until done
job = ml_client.jobs.get(returned_job.name)
print(job.status)  # "Completed", "Failed", "Running", etc.
```

**Download outputs:**
```python
ml_client.jobs.download(returned_job.name, output_name="model_dir", download_path="./local_output")
```

---

## Environments

Environments define the software stack for your job.

```python
from azure.ai.ml.entities import Environment

# From a conda YAML file
env = Environment(
    name="my-sklearn-env",
    description="scikit-learn training environment",
    conda_file="./conda.yml",
    image="mcr.microsoft.com/azureml/openmpi4.1.0-ubuntu20.04",
)
ml_client.environments.create_or_update(env)

# Reference a registered environment in a job
environment="azureml:my-sklearn-env:1"       # name:version
environment="azureml:my-sklearn-env@latest"  # latest label
# Or use a curated environment from the registry
environment="azureml://registries/azureml/environments/sklearn-1.5/labels/latest"
```

---

## Compute

```python
from azure.ai.ml.entities import AmlCompute, ComputeInstance

# Create a CPU cluster (scales to 0 when idle)
cluster = AmlCompute(
    name="cpu-cluster",
    type="amlcompute",
    size="Standard_DS3_v2",
    min_instances=0,
    max_instances=4,
    idle_time_before_scale_down=120,   # seconds
)
ml_client.compute.begin_create_or_update(cluster).result()

# Create a compute instance (single dev VM)
instance = ComputeInstance(
    name="my-instance",
    size="Standard_DS3_v2",
)
ml_client.compute.begin_create_or_update(instance).result()

# List existing compute
for c in ml_client.compute.list():
    print(c.name, c.type, c.provisioning_state)
```

---

## Data Assets

Register data so it can be versioned and shared across jobs:

```python
from azure.ai.ml.entities import Data
from azure.ai.ml.constants import AssetTypes

# Register a local file as a versioned data asset
data_asset = Data(
    name="titanic-dataset",
    version="1",
    description="Titanic passenger data",
    path="./data/titanic.csv",          # local path auto-uploaded to default datastore
    type=AssetTypes.URI_FILE,
)
ml_client.data.create_or_update(data_asset)

# Register a folder
folder_asset = Data(
    name="training-images",
    path="./data/images/",
    type=AssetTypes.URI_FOLDER,
)
ml_client.data.create_or_update(folder_asset)

# Use in a job: reference by name:version
Input(type=AssetTypes.URI_FILE, path="azureml:titanic-dataset:1")
Input(type=AssetTypes.URI_FILE, path="azureml:titanic-dataset@latest")
```

---

## Model Registry

Register and retrieve models from the workspace:

```python
from azure.ai.ml.entities import Model
from azure.ai.ml.constants import AssetTypes

# Register from local path
model = Model(
    path="./outputs/model",
    name="my-model",
    version="1",
    description="Trained sklearn classifier",
    type=AssetTypes.MLFLOW_MODEL,   # or CUSTOM_MODEL for non-MLflow artifacts
)
registered_model = ml_client.models.create_or_update(model)

# Register from a completed job's output
model_from_job = Model(
    path=f"azureml://jobs/{returned_job.name}/outputs/model_dir",
    name="job-trained-model",
    type=AssetTypes.CUSTOM_MODEL,
)
ml_client.models.create_or_update(model_from_job)

# Get a specific version
model = ml_client.models.get("my-model", version="1")
model = ml_client.models.get("my-model", label="latest")

# List all versions
for m in ml_client.models.list("my-model"):
    print(m.name, m.version, m.creation_context.created_at)
```

---

## Pipeline Jobs

Pipelines chain multiple steps. Use the `@pipeline` decorator with component calls:

```python
from azure.ai.ml.dsl import pipeline
from azure.ai.ml import Input, command, load_component

# Define steps as command components inline
prep_step = command(
    name="prep",
    command="python prep.py --raw ${{inputs.raw_data}} --out ${{outputs.prepared}}",
    code="./prep",
    inputs={"raw_data": Input(type=AssetTypes.URI_FILE)},
    outputs={"prepared": Output(type=AssetTypes.URI_FOLDER)},
    environment="azureml:my-env:1",
    compute="cpu-cluster",
)

train_step = command(
    name="train",
    command="python train.py --data ${{inputs.train_data}} --model ${{outputs.model}}",
    code="./train",
    inputs={"train_data": Input(type=AssetTypes.URI_FOLDER)},
    outputs={"model": Output(type=AssetTypes.URI_FOLDER)},
    environment="azureml:my-env:1",
    compute="cpu-cluster",
)

@pipeline(
    description="Prep → Train pipeline",
    default_compute="cpu-cluster",
)
def my_pipeline(raw_input):
    prep = prep_step(raw_data=raw_input)
    train = train_step(train_data=prep.outputs.prepared)
    return {"trained_model": train.outputs.model}

pipeline_job = my_pipeline(
    raw_input=Input(type=AssetTypes.URI_FILE, path="./data/raw.csv"),
)
returned = ml_client.jobs.create_or_update(pipeline_job)
```

**Load components from YAML files** (reusable across teams):
```python
from azure.ai.ml import load_component

prep_component = load_component(source="./components/prep.yml")
train_component = load_component(source="./components/train.yml")

# Register component to workspace
ml_client.components.create_or_update(prep_component)

# Use registered component by name:version
prep_component = ml_client.components.get("prep-data", version="1")
```

---

## Sweep Jobs (Hyperparameter Tuning)

```python
from azure.ai.ml.sweep import Choice, Uniform, BanditPolicy

# Start from a command job and add sweep config
sweep_job = job.sweep(
    sampling_algorithm="random",
    primary_metric="val_accuracy",
    goal="Maximize",
    compute="cpu-cluster",
)
sweep_job.set_limits(max_total_trials=20, max_concurrent_trials=4, timeout=3600)
sweep_job.early_termination = BanditPolicy(evaluation_interval=2, slack_factor=0.1)

# Specify hyperparameter search space in the command string
# e.g. command="python train.py --lr ${{search_space.lr}} --batch ${{search_space.batch_size}}"
sweep_job.search_space = {
    "lr": Uniform(min_value=0.001, max_value=0.1),
    "batch_size": Choice(values=[16, 32, 64]),
}

returned_sweep = ml_client.jobs.create_or_update(sweep_job)
```

---

## Online Endpoints (Real-time Inference)

Deploy a registered model to a managed online endpoint:

```python
from azure.ai.ml.entities import (
    ManagedOnlineEndpoint,
    ManagedOnlineDeployment,
    Model,
)
import datetime

endpoint_name = f"my-endpoint-{datetime.datetime.now().strftime('%m%d%H%M')}"

# Create endpoint
endpoint = ManagedOnlineEndpoint(
    name=endpoint_name,
    description="My inference endpoint",
    auth_mode="key",
)
ml_client.online_endpoints.begin_create_or_update(endpoint).result()

# Create deployment with a registered model
deployment = ManagedOnlineDeployment(
    name="blue",
    endpoint_name=endpoint_name,
    model="azureml:my-model:1",
    instance_type="Standard_DS3_v2",
    instance_count=1,
)
ml_client.online_deployments.begin_create_or_update(deployment).result()

# Route all traffic to the deployment
endpoint.traffic = {"blue": 100}
ml_client.online_endpoints.begin_create_or_update(endpoint).result()

# Invoke the endpoint
response = ml_client.online_endpoints.invoke(
    endpoint_name=endpoint_name,
    request_file="./sample_input.json",
    deployment_name="blue",
)
```

---

## Job Management

```python
# List jobs in an experiment
for job in ml_client.jobs.list(parent_job_name=None):
    print(job.name, job.status, job.display_name)

# Get a job by name
job = ml_client.jobs.get("<job-name>")

# Cancel a job
ml_client.jobs.begin_cancel("<job-name>").result()

# Archive a job
ml_client.jobs.archive("<job-name>")
```

---

## Error Handling

```python
from azure.core.exceptions import HttpResponseError, ResourceNotFoundError

try:
    ml_client.compute.get("nonexistent-cluster")
except ResourceNotFoundError:
    print("Compute not found — create it first")
except HttpResponseError as e:
    print(f"Service error {e.status_code}: {e.message}")
```

---

## Key Patterns

**Local path vs cloud path in Input/Output:**
- Local paths (`./data/file.csv`) are automatically uploaded to the default datastore on job submission.
- Cloud paths use URI schemes: `azureml://`, `https://`, `abfss://` (ADLS), `wasbs://`.
- Reference registered assets: `azureml:<name>:<version>` or `azureml:<name>@latest`.

**`ml_client.create_or_update` vs `ml_client.<resource>.create_or_update`:**
- `ml_client.create_or_update(job)` is a shorthand that works for jobs, models, data.
- `ml_client.jobs.create_or_update(job)` is explicit; both are equivalent.

**Polling operations:** Compute and endpoint operations return an LRO poller. Call `.result()` to block until complete, or `.done()` to check without blocking.
