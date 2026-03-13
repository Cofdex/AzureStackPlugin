---
name: azure-identity
description: >
  Azure Identity SDK for Python authentication. Use this skill whenever the user needs to authenticate
  Python code to Azure services, configure credentials, or set up auth patterns. Triggers on:
  "azure-identity", "DefaultAzureCredential", "authentication", "managed identity", "service principal",
  "credential", "ManagedIdentityCredential", "ClientSecretCredential", "ChainedTokenCredential",
  "WorkloadIdentityCredential", "token scope", "az login credential", "azure auth".
  Always invoke this skill when Azure authentication or credential setup is involved — even if the
  user just says "connect to Azure" or "authenticate my app".
---

# Azure Identity SDK for Python

## Installation & Imports

```bash
pip install azure-identity
```

```python
# Synchronous
from azure.identity import (
    DefaultAzureCredential,
    ManagedIdentityCredential,
    ClientSecretCredential,
    CertificateCredential,
    AzureCliCredential,
    AzureDeveloperCliCredential,
    InteractiveBrowserCredential,
    EnvironmentCredential,
    ChainedTokenCredential,
    WorkloadIdentityCredential,
    TokenCachePersistenceOptions,
    CredentialUnavailableError,
    AuthenticationRequiredError,
)
from azure.core.exceptions import ClientAuthenticationError

# Async — same names, different module
from azure.identity.aio import (
    DefaultAzureCredential,
    ManagedIdentityCredential,
    ClientSecretCredential,
    ChainedTokenCredential,
    AzureCliCredential,
    # ... same names as sync
)
```

---

## DefaultAzureCredential

The right default for most applications. It tries a chain of credential types in order, adapting automatically between development and production environments.

### Chain Order (first success wins)
1. `EnvironmentCredential` — reads `AZURE_TENANT_ID`, `AZURE_CLIENT_ID`, `AZURE_CLIENT_SECRET` (or cert)
2. `WorkloadIdentityCredential` — AKS workload identity (if env vars present)
3. `ManagedIdentityCredential` — Azure-hosted resources (VMs, App Service, Functions, AKS)
4. `SharedTokenCacheCredential` — Windows only, cached from VS/VSCode/CLI
5. `VisualStudioCodeCredential` — VS Code Azure extension
6. `AzureCliCredential` — `az login`
7. `AzurePowerShellCredential` — `Connect-AzAccount`
8. `AzureDeveloperCliCredential` — `azd auth login`
9. `BrokerCredential` — Windows/WSL WAM (requires `azure-identity-broker`)

> **Interactive browser is excluded by default.** This is intentional — it prevents CI/CD pipelines from blocking waiting for browser input.

### Basic usage
```python
from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient

# Azure SDK clients accept credentials directly — no need to call get_token() yourself
credential = DefaultAzureCredential()
client = BlobServiceClient("https://myaccount.blob.core.windows.net", credential=credential)
```

### Key constructor parameters
```python
credential = DefaultAzureCredential(
    # Exclude specific links in the chain
    exclude_environment_credential=False,
    exclude_managed_identity_credential=False,
    exclude_cli_credential=False,
    exclude_developer_cli_credential=False,
    exclude_interactive_browser_credential=True,  # True by default!

    # For user-assigned managed identity (pass-through to ManagedIdentityCredential)
    managed_identity_client_id="<client-id>",

    # For workload identity (pass-through to WorkloadIdentityCredential)
    workload_identity_client_id="<client-id>",
)
```

> **Common mistake**: `DefaultAzureCredential` does NOT accept `tenant_id=` directly. If you need to target a specific tenant, use `ClientSecretCredential` or another specific credential.

### Production vs development pattern
```python
import os
from azure.identity import DefaultAzureCredential

# In production (deployed to Azure): ManagedIdentityCredential kicks in automatically
# In development: AzureCliCredential or AzureDeveloperCliCredential is used after `az login`
credential = DefaultAzureCredential()

# To speed up development by skipping checks you know won't work:
credential = DefaultAzureCredential(
    exclude_environment_credential=True,       # Skip env var check locally
    exclude_workload_identity_credential=True,  # Skip k8s check locally
)
```

---

## ManagedIdentityCredential

For Azure-hosted resources (VMs, App Service, Functions, Container Apps, AKS pods). No secrets needed — the platform provides the identity.

```python
from azure.identity import ManagedIdentityCredential

# System-assigned managed identity — no arguments
credential = ManagedIdentityCredential()

# User-assigned managed identity — pass client_id
credential = ManagedIdentityCredential(client_id="<user-assigned-mi-client-id>")
```

> When you have multiple user-assigned identities on a resource, you MUST pass `client_id=` to disambiguate. Passing `client_id=` for a system-assigned identity will fail.

---

## Service Principal Credentials

For CI/CD pipelines, backend services, and non-interactive authentication with an app registration.

### ClientSecretCredential
```python
from azure.identity import ClientSecretCredential

credential = ClientSecretCredential(
    tenant_id="<directory-tenant-id>",
    client_id="<app-registration-client-id>",
    client_secret="<client-secret-value>",
)
```

### CertificateCredential
```python
from azure.identity import CertificateCredential

# From file
credential = CertificateCredential(
    tenant_id="<tenant-id>",
    client_id="<client-id>",
    certificate_path="/path/to/cert.pem",  # PEM or PKCS12
)

# From bytes (e.g., loaded from Key Vault)
credential = CertificateCredential(
    tenant_id="<tenant-id>",
    client_id="<client-id>",
    certificate_data=cert_bytes,
    password="<cert-password>",  # Optional, for encrypted certs
)
```

### EnvironmentCredential
Reads service principal credentials from environment variables automatically.

Required env vars (secret auth):
- `AZURE_TENANT_ID`
- `AZURE_CLIENT_ID`
- `AZURE_CLIENT_SECRET`

Required env vars (cert auth):
- `AZURE_TENANT_ID`, `AZURE_CLIENT_ID`, `AZURE_CLIENT_CERTIFICATE_PATH`
- Optional: `AZURE_CLIENT_CERTIFICATE_PASSWORD`

```python
from azure.identity import EnvironmentCredential
credential = EnvironmentCredential()  # Reads vars automatically
```

---

## Development Credentials

For local development and tooling contexts.

```python
from azure.identity import AzureCliCredential, AzureDeveloperCliCredential, InteractiveBrowserCredential

# Uses `az login` session
credential = AzureCliCredential()

# Uses `azd auth login` session
credential = AzureDeveloperCliCredential()

# Opens browser for interactive login (desktop/CLI apps)
credential = InteractiveBrowserCredential(
    client_id="<app-registration-id>",  # Optional; defaults to Azure dev app
    redirect_uri="http://localhost:8400",  # Required when using custom client_id
)
```

---

## ChainedTokenCredential

Build a custom credential chain. Tries each credential left-to-right, returning the first success.

```python
from azure.identity import (
    ChainedTokenCredential,
    ManagedIdentityCredential,
    AzureCliCredential,
    EnvironmentCredential,
)

# Production prefers managed identity; falls back to CLI for local dev
credential = ChainedTokenCredential(
    ManagedIdentityCredential(),
    EnvironmentCredential(),
    AzureCliCredential(),
)
```

Raises `ClientAuthenticationError` if all credentials in the chain fail.

---

## WorkloadIdentityCredential (AKS)

For Kubernetes workload identity (federated credentials). Reads configuration from environment variables set by the Azure Workload Identity webhook.

```python
from azure.identity import WorkloadIdentityCredential

# If env vars are set by the webhook (typical AKS setup):
credential = WorkloadIdentityCredential()

# Or explicit:
credential = WorkloadIdentityCredential(
    tenant_id="<tenant-id>",       # from AZURE_TENANT_ID
    client_id="<client-id>",       # from AZURE_CLIENT_ID
    token_file_path="/var/run/secrets/azure/tokens/token",  # from AZURE_FEDERATED_TOKEN_FILE
)
```

---

## Token Scopes

Azure SDK clients manage scopes automatically. You only need scopes when calling `get_token()` directly (e.g., for custom REST calls or non-Azure services).

**Scope format**: `"https://{resource}/.default"` — the `/.default` suffix is required.

| Service | Scope |
|---------|-------|
| Azure Resource Manager | `"https://management.azure.com/.default"` |
| Azure Storage | `"https://storage.azure.com/.default"` |
| Azure Key Vault | `"https://vault.azure.net/.default"` |
| Azure Cosmos DB | `"https://cosmos.azure.com/.default"` |
| Azure SQL | `"https://database.windows.net/.default"` |
| Microsoft Graph | `"https://graph.microsoft.com/.default"` |

> **Common mistake**: Omitting `/.default`. `"https://management.azure.com"` (no suffix) will fail with an AADSTS error.

### Calling get_token() directly
```python
credential = DefaultAzureCredential()
token = credential.get_token("https://management.azure.com/.default")

# AccessToken fields:
print(token.token)      # str — the Bearer token
print(token.expires_on) # int — Unix timestamp when it expires

# Use in a raw HTTP request
headers = {"Authorization": f"Bearer {token.token}"}
```

---

## Async Support

Import from `azure.identity.aio`. Always use `async with` (or call `await credential.close()`) to release connections.

```python
from azure.identity.aio import DefaultAzureCredential

async def main():
    async with DefaultAzureCredential() as credential:
        # Pass to async SDK clients
        from azure.keyvault.secrets.aio import SecretClient
        client = SecretClient("https://my-vault.vault.azure.net", credential)
        secret = await client.get_secret("my-secret")
        print(secret.value)
```

```python
# Async get_token() directly
async with DefaultAzureCredential() as credential:
    token = await credential.get_token("https://storage.azure.com/.default")
```

> **Common mistake**: Using async credentials without `async with`. The `close()` method must be awaited or the transport will leak HTTP connections.

---

## Token Cache Persistence (Optional)

Credentials cache tokens in-memory by default. Opt into persistent caching to survive process restarts.

```python
from azure.identity import ClientSecretCredential, TokenCachePersistenceOptions

cache_options = TokenCachePersistenceOptions(
    name="my-app-cache",              # Cache name prefix
    allow_unencrypted_storage=False,  # Set True only for environments without keyring
)

credential = ClientSecretCredential(
    tenant_id="<tenant-id>",
    client_id="<client-id>",
    client_secret="<secret>",
    cache_persistence_options=cache_options,
)
```

Persistent caching is platform-native: DPAPI on Windows, Keychain on macOS, libsecret on Linux.

Not supported on: `AzureCliCredential`, `ManagedIdentityCredential`, `AzureDeveloperCliCredential`.

---

## Error Handling

```python
from azure.identity import DefaultAzureCredential, CredentialUnavailableError
from azure.core.exceptions import ClientAuthenticationError

try:
    credential = DefaultAzureCredential()
    token = credential.get_token("https://management.azure.com/.default")
except CredentialUnavailableError:
    # No credential in the chain has enough config to even try
    # e.g., ManagedIdentityCredential outside Azure, AzureCliCredential when not logged in
    print("No credential available — check environment setup")
except ClientAuthenticationError as e:
    # A credential attempted auth but it failed (wrong secret, expired cert, etc.)
    print(f"Authentication failed: {e.message}")
```

`CredentialUnavailableError` = credential can't attempt auth (misconfigured/missing).
`ClientAuthenticationError` = credential attempted but was rejected.
