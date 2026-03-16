---
name: azure-apim
description: >
  Azure API Management SDK for Python (`azure-mgmt-apimanagement`). Use this skill when working
  with Azure APIM to manage APIs, products, subscriptions, policies, backends, or named values
  programmatically. Triggers on: "ApiManagementClient", "azure-mgmt-apimanagement", "APIM",
  "API Management", "API gateway", "API product", "API subscription", "API policy", "rate limit policy",
  "backend service", "named value", "developer portal". Use whenever the task involves provisioning
  or configuring an API gateway on Azure, even if the user just says "set up an API in APIM" or
  "add rate limiting to my Azure API".
---

# Azure API Management SDK for Python

Manage Azure API Management services, APIs, products, subscriptions, policies, and more using
`azure-mgmt-apimanagement`. This is a **management-plane** SDK — it configures the APIM service
itself (not calls through it).

## Installation

```bash
uv add azure-mgmt-apimanagement azure-identity
```

## Client Initialization

```python
from azure.mgmt.apimanagement import ApiManagementClient
from azure.identity import DefaultAzureCredential
import os

client = ApiManagementClient(
    credential=DefaultAzureCredential(),
    subscription_id=os.environ["AZURE_SUBSCRIPTION_ID"]
)
```

Every operation takes these three positional parameters first:
```
resource_group_name, service_name, <resource_id>
```

`service_name` must match pattern `^[a-zA-Z](?:[a-zA-Z0-9-]*[a-zA-Z0-9])?$` (max 50 chars).

---

## APIs (`client.api`)

### Create or Update

`begin_create_or_update` is an **LRO** — always call `.result()`.

```python
from azure.mgmt.apimanagement.models import ApiCreateOrUpdateParameter

api = client.api.begin_create_or_update(
    resource_group_name="myRG",
    service_name="myApim",
    api_id="my-api-v1",              # Unique, immutable once set
    parameters=ApiCreateOrUpdateParameter(
        display_name="My API",       # Required
        path="my-api",               # Required: URL path segment, unique per service
        protocols=["https"],         # Required: list — "http", "https", "ws", "wss"
        service_url="https://backend.example.com/v1",
        description="API description (HTML allowed)",
        api_type="http",             # http | soap | websocket | graphql | odata | grpc
        subscription_required=True,
    ),
    if_match=None,                   # Pass ETag from .get() when updating
).result()
```

**Gotcha — protocols must be a list of lowercase strings.** `protocols="https"` or `protocols=["HTTPS"]` both fail.

**Gotcha — `api_id` is immutable.** To rename an API's ID, delete and recreate.

### List, Get, Delete

```python
# List (returns ItemPaged — iterate or call list())
for api in client.api.list_by_service("myRG", "myApim"):
    print(api.display_name, api.path)

# With OData filter
apis = client.api.list_by_service("myRG", "myApim",
    filter="substringof('users', displayName) eq true")

# Get
api = client.api.get("myRG", "myApim", "my-api-v1")
print(api.service_url, api.etag)

# Delete (requires ETag)
client.api.delete("myRG", "myApim", "my-api-v1",
    if_match=api.etag, delete_revisions=True)
```

---

## API Operations (`client.api_operation`)

```python
from azure.mgmt.apimanagement.models import OperationContract, ParameterContract

client.api_operation.create_or_update(
    "myRG", "myApim", "my-api-v1", "get-user",
    parameters=OperationContract(
        display_name="Get User",   # Required
        method="GET",              # Required: standard HTTP methods
        url_template="/users/{userId}",  # Required: {param} placeholders
        description="Fetch user by ID",
        template_parameters=[
            ParameterContract(name="userId", type="string", required=True)
        ],
    ),
)

# List operations in an API
for op in client.api_operation.list_by_api("myRG", "myApim", "my-api-v1"):
    print(op.method, op.url_template)
```

---

## Products (`client.product`, `client.product_api`)

Products bundle APIs and control subscription access.

```python
from azure.mgmt.apimanagement.models import ProductContract

# Create product
client.product.create_or_update(
    "myRG", "myApim", "free-tier",
    parameters=ProductContract(
        display_name="Free Tier",     # Required
        subscription_required=True,
        approval_required=False,
        subscriptions_limit=5,        # Max subscriptions per user
        state="published",            # "published" or "notPublished"
        terms="Usage terms...",
    ),
)

# Add an API to the product
client.product_api.create_or_update("myRG", "myApim", "free-tier", "my-api-v1")

# List APIs in a product
for api in client.product_api.list_by_product("myRG", "myApim", "free-tier"):
    print(api.display_name)

# Remove API from product
client.product_api.delete("myRG", "myApim", "free-tier", "my-api-v1")
```

---

## Subscriptions (`client.subscription`)

Subscriptions issue API keys scoped to a product, API, or all APIs.

```python
from azure.mgmt.apimanagement.models import SubscriptionCreateParameters

sub = client.subscription.create_or_update(
    "myRG", "myApim",
    sid="app-subscription-001",       # Subscription ID (not Azure subscription)
    parameters=SubscriptionCreateParameters(
        scope="/products/free-tier",  # "/products/{id}" | "/apis/{id}" | "/apis"
        display_name="App Client",
        # primary_key / secondary_key auto-generated if omitted
        state="active",               # active | suspended | submitted | rejected | cancelled
        allow_tracing=False,
    ),
    notify=False,
)

# Access keys (may be masked by default)
print(sub.primary_key, sub.secondary_key)

# Regenerate keys
client.subscription.regenerate_primary_key("myRG", "myApim", "app-subscription-001")
client.subscription.regenerate_secondary_key("myRG", "myApim", "app-subscription-001")

# List subscriptions
for s in client.subscription.list_by_service("myRG", "myApim"):
    print(s.display_name, s.scope)
```

**Scope format matters:** `/products/free-tier` (not `free-tier`), `/apis/my-api-v1`, or `/apis` for all.

---

## Policies (`client.api_policy`, `client.product_policy`)

Policies are **XML documents** applied at different scopes (service → product → API → operation).

```python
from azure.mgmt.apimanagement.models import PolicyContract

# Rate limiting policy on an API
rate_limit_policy = """<policies>
  <inbound>
    <rate-limit calls="100" renewal-period="60" />
    <quota calls="10000" bandwidth="40960" renewal-period="3600" />
    <base />
  </inbound>
  <backend>
    <base />
  </backend>
  <outbound>
    <base />
  </outbound>
  <on-error>
    <base />
  </on-error>
</policies>"""

client.api_policy.create_or_update(
    "myRG", "myApim", "my-api-v1",
    policy_id="policy",              # Always "policy" — this is a fixed constant
    parameters=PolicyContract(
        value=rate_limit_policy,
        format="xml",                # "xml" | "xml-link" | "rawxml" | "rawxml-link"
    ),
)

# Product-level policy
client.product_policy.create_or_update(
    "myRG", "myApim", "free-tier", "policy",
    parameters=PolicyContract(value=rate_limit_policy, format="xml"),
)

# Get current policy
policy = client.api_policy.get("myRG", "myApim", "my-api-v1", "policy",
    format="xml")  # Returns PolicyContract with .value containing the XML
print(policy.value)

# Delete policy
client.api_policy.delete("myRG", "myApim", "my-api-v1", "policy",
    if_match=policy.etag)
```

**`policy_id` is always the string `"policy"** — it's a fixed identifier, not a user-chosen name.

Common inbound policies:
- `<rate-limit calls="N" renewal-period="seconds" />` — per-subscription rate limit
- `<rate-limit-by-key calls="N" renewal-period="seconds" counter-key="@(context.Subscription.Id)" />` — custom key
- `<ip-filter action="allow"><address-range from="10.0.0.0" to="10.255.255.255" /></ip-filter>`
- `<set-header name="X-Custom" exists-action="override"><value>val</value></set-header>`
- `<rewrite-uri template="/v2{url}" copy-unmatched-params="true" />`
- `<base />` — inherit from parent scope (include this in each section)

---

## Named Values (`client.named_value`)

Named values are reusable constants or secrets referenced in policies as `{{my-value}}`.

```python
from azure.mgmt.apimanagement.models import NamedValueCreateContract

# Create a named value (plain text)
client.named_value.begin_create_or_update(
    "myRG", "myApim", "backend-api-key",
    parameters=NamedValueCreateContract(
        display_name="backend-api-key",  # Name used in policies as {{backend-api-key}}
        value="secret-key-12345",
        secret=True,                     # Mark as secret (hidden in portal)
        tags=["backend", "auth"],
    ),
).result()  # LRO — call .result()

# Reference in policy: <set-header name="X-API-Key" exists-action="override">
#   <value>{{backend-api-key}}</value>
# </set-header>

for nv in client.named_value.list_by_service("myRG", "myApim"):
    print(nv.display_name, nv.secret)
```

---

## Backends (`client.backend`)

Backends define upstream service endpoints with credentials and circuit breaker settings.

```python
from azure.mgmt.apimanagement.models import (
    BackendContract, BackendCredentialsContract, BackendProxyContract
)

client.backend.create_or_update(
    "myRG", "myApim", "my-backend",
    parameters=BackendContract(
        url="https://api.internal.example.com",  # Required
        protocol="http",                          # Required: "http" or "soap"
        description="Internal backend service",
        credentials=BackendCredentialsContract(
            header={"X-API-Key": ["{{backend-api-key}}"]},  # Header values are lists
        ),
    ),
)

# Reference backend in policy:
# <set-backend-service backend-id="my-backend" />
```

---

## Users & Groups (`client.user`, `client.group`)

```python
from azure.mgmt.apimanagement.models import UserCreateParameters

# Create user
client.user.create_or_update(
    "myRG", "myApim", "user-001",
    parameters=UserCreateParameters(
        email="dev@example.com",   # Required, unique
        first_name="Jane",
        last_name="Dev",
        state="active",            # active | blocked | pending | deleted
        confirmation="signup",     # "signup" | "invite"
    ),
)

# Add user to group
client.group_user.create("myRG", "myApim", "developers", "user-001")

# List users / groups
for user in client.user.list_by_service("myRG", "myApim"):
    print(user.email, user.state)
```

---

## ETag / if_match Pattern

All update and delete operations require an ETag to prevent lost updates:

```python
# Always fetch first to get ETag
resource = client.api.get("myRG", "myApim", "my-api-v1")

# Pass ETag for update/delete
client.api.update("myRG", "myApim", "my-api-v1",
    parameters=..., if_match=resource.etag)

# Pass "*" to overwrite unconditionally (use with caution)
client.api.delete("myRG", "myApim", "my-api-v1", if_match="*")
```

Missing or wrong ETag → `HttpResponseError: 412 Precondition Failed`.

---

## Common Mistakes

| Mistake | What Happens | Fix |
|---------|-------------|-----|
| `protocols="https"` (string) | `ValidationError` | Use list: `["https"]` |
| `protocols=["HTTPS"]` | API rejects uppercase | Lowercase: `["https"]` |
| Missing `.result()` on LRO | Gets `LROPoller` not the resource | Always chain `.result()` |
| `policy_id="my-policy"` | `ResourceNotFound` | Always `policy_id="policy"` |
| `/apis` scope vs `/apis/id` scope | Subscription scoped incorrectly | Use `/products/{id}` for product, `/apis/{id}` for single API |
| Reusing `api_id` after delete | May fail if soft-delete still active | Wait or use different ID |
| Omitting `if_match` on delete | `HttpResponseError: 412` | Pass ETag or `"*"` |
| Named value in policy uses wrong syntax | Policy rejected | Use `{{display_name}}` (double curly braces) |

---

## LRO Methods (require `.result()`)

These return an `LROPoller` — always call `.result()` to wait for completion:
- `client.api.begin_create_or_update()`
- `client.named_value.begin_create_or_update()`
- `client.api_management_service.begin_create_or_update()`
- `client.api_management_service.begin_update()`

Non-LRO methods (`product.create_or_update`, `subscription.create_or_update`, etc.) return the resource directly.
