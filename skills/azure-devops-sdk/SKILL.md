---
name: azure-devops-sdk
description: >
  Azure DevOps Python SDK (azure-devops). Use for automating Azure DevOps operations:
  creating work items, querying repositories, triggering builds, and managing pipelines.
  Triggers on: "azure-devops", "azure devops sdk", "work items", "build pipeline",
  "git repositories", "WIQL", "JsonPatchOperation", "WorkItemTrackingClient",
  "GitClient", "BuildClient", "PAT token", "dev.azure.com". Use when automating
  DevOps workflows or integrating Azure DevOps into Python applications.
---

# Azure DevOps Python SDK

## Package
```bash
uv add azure-devops msrest
```

## Auth and connection

```python
from azure.devops.connection import Connection
from msrest.authentication import BasicAuthentication

# Organization URL format: https://dev.azure.com/{org-name}
organization_url = "https://dev.azure.com/myorg"
pat_token = "your-personal-access-token"   # from Azure DevOps > User Settings > PAT

credentials = BasicAuthentication("", pat_token)   # username is empty string
connection = Connection(base_url=organization_url, creds=credentials)
```

## Get clients

```python
# Work items
wit_client = connection.clients.get_work_item_tracking_client()

# Git repos
git_client = connection.clients.get_git_client()

# Builds
build_client = connection.clients.get_build_client()

# Pipelines (YAML-based)
pipelines_client = connection.clients.get_pipelines_client()
```

## Work items

### Create a work item
```python
from azure.devops.v7_1.work_item_tracking.models import JsonPatchOperation

patch_document = [
    JsonPatchOperation(op="add", path="/fields/System.Title", value="Bug: login fails"),
    JsonPatchOperation(op="add", path="/fields/System.Description", value="Users cannot log in"),
    JsonPatchOperation(op="add", path="/fields/System.AssignedTo", value="user@company.com"),
    JsonPatchOperation(op="add", path="/fields/Microsoft.VSTS.Common.Priority", value=1),
]

work_item = wit_client.create_work_item(
    document=patch_document,
    project="MyProject",
    type="Bug"   # "Bug", "Task", "User Story", "Feature", "Epic"
)
print(f"Created work item: #{work_item.id}")
```

### Get / query work items
```python
# Single work item
wi = wit_client.get_work_item(id=123, project="MyProject")
print(wi.fields["System.Title"])
print(wi.fields["System.State"])

# WIQL query
from azure.devops.v7_1.work_item_tracking.models import Wiql
wiql = Wiql(query="SELECT [System.Id], [System.Title] FROM WorkItems WHERE [System.TeamProject] = 'MyProject' AND [System.State] = 'Active'")
results = wit_client.query_by_wiql(wiql, project="MyProject")
ids = [r.id for r in results.work_items]
items = wit_client.get_work_items(ids=ids[:200])   # max 200 per call
```

## Git repositories

```python
# List repos
repos = git_client.get_repositories(project="MyProject")
for repo in repos:
    print(f"{repo.name}: {repo.remote_url}")

# Get specific repo
repo = git_client.get_repository(
    repository_id="MyRepo",   # name or GUID
    project="MyProject"
)

# Get commits
from azure.devops.v7_1.git.models import GitQueryCommitsCriteria
criteria = GitQueryCommitsCriteria(item_version={"version": "main", "versionType": "branch"})
commits = git_client.get_commits(
    repository_id=repo.id,
    search_criteria=criteria,
    project="MyProject",
    top=10
)
```

## Build pipelines

```python
# List build definitions
definitions = build_client.get_definitions(project="MyProject")

# Queue a build
from azure.devops.v7_1.build.models import Build
build_def = build_client.get_definition(definition_id=42, project="MyProject")
queued = build_client.queue_build(
    build=Build(definition=build_def),
    project="MyProject"
)
print(f"Queued build: #{queued.id}")

# Get build status
build = build_client.get_build(build_id=queued.id, project="MyProject")
print(f"Status: {build.status}, Result: {build.result}")
```

## Common mistakes

| ❌ Wrong | ✅ Correct |
|---|---|
| `BasicAuthentication(pat, "")` | `BasicAuthentication("", pat)` — username is empty, PAT is password |
| `connection.get_client('...')` long path | `connection.clients.get_work_item_tracking_client()` |
| `row["System.Title"]` from WIQL | WIQL returns work item references with `id` only — call `get_work_items(ids)` separately |
| `get_work_items([1,2,3])` all at once | Max 200 IDs per call — batch in chunks |
| Organization URL as `https://myorg.visualstudio.com` | Use `https://dev.azure.com/myorg` (new format) |
| `wit_client.update_work_item(patch, id)` | `wit_client.update_work_item(document=patch, id=id, project=project)` |
