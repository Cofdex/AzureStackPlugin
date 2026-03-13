---
name: azure-keyvault
description: >
  Azure Key Vault SDK for Python — secrets, keys, and certificates management.
  Use this skill whenever the user needs to store secrets, manage encryption keys, or work
  with certificates in Azure Key Vault. Triggers on: "key vault", "SecretClient", "KeyClient",
  "CertificateClient", "secrets management", "encryption keys", "azure-keyvault-secrets",
  "azure-keyvault-keys", "azure-keyvault-certificates", "vault secrets", "store password",
  "rotate secret", "CryptographyClient", "encrypt decrypt key vault".
  Always invoke this skill when Azure Key Vault is involved — even if the user just says
  "store this secret in Azure" or "manage certificates with Azure".
---

# Azure Key Vault SDK for Python

Three separate packages, each with its own client class. Install what you need:

```bash
pip install azure-keyvault-secrets azure-identity     # secrets only
pip install azure-keyvault-keys azure-identity        # keys only
pip install azure-keyvault-certificates azure-identity  # certs only
# or all at once:
pip install azure-keyvault-secrets azure-keyvault-keys azure-keyvault-certificates azure-identity
```

**Vault URL format** (same for all clients):
```
https://{vault-name}.vault.azure.net
```

---

## SecretClient — Secrets Management

```python
from azure.keyvault.secrets import SecretClient
from azure.identity import DefaultAzureCredential
from azure.core.exceptions import ResourceNotFoundError

credential = DefaultAzureCredential()
client = SecretClient(vault_url="https://my-vault.vault.azure.net", credential=credential)
```

### Core operations

```python
# Store / update a secret
secret = client.set_secret("db-password", "s3cr3t!", content_type="password",
                           tags={"env": "prod"}, expires_on=datetime(2026, 1, 1))

# Retrieve latest version
secret = client.get_secret("db-password")
print(secret.value)                  # str — the actual value
print(secret.properties.version)     # UUID string
print(secret.properties.expires_on)  # datetime or None

# Retrieve a specific version
secret = client.get_secret("db-password", version="<version-uuid>")

# Update metadata only (not the value — call set_secret again for that)
client.update_secret_properties("db-password", enabled=False, tags={"archived": "true"})
```

### Listing — returns metadata ONLY, not values

```python
# ✅ List all secrets (names/metadata)
for props in client.list_properties_of_secrets():
    print(props.name, props.enabled, props.expires_on)
    # props.value does NOT exist — must call get_secret() to fetch the value

# ✅ All versions of one secret
for props in client.list_properties_of_secret_versions("db-password"):
    print(props.version, props.enabled)
```

> **Common mistake**: Accessing `.value` on items from `list_properties_of_secrets()` — it doesn't exist. Call `client.get_secret(props.name)` to get the value.

### Soft-delete lifecycle

Key Vault soft-delete is **on by default** — deleting a secret makes it recoverable for 7–90 days. The name stays reserved until purged or recovered.

```python
# Delete (soft-delete by default) — LRO: must call .result()
poller = client.begin_delete_secret("db-password")
deleted = poller.result()  # waits for completion
print(deleted.scheduled_purge_date)

# Recover (while still in soft-deleted state)
client.begin_recover_deleted_secret("db-password").result()

# Permanently destroy (cannot be undone)
client.purge_deleted_secret("db-password")

# Inspect what's in the soft-deleted state
deleted = client.get_deleted_secret("db-password")
```

> **Important**: After soft-deleting a secret, you CANNOT create a new secret with the same name until you either recover or purge the old one. Plan for this in rotation workflows.

> **LRO pattern**: All `begin_*` methods return a poller. Always call `.result()` to wait for completion (or `.wait()` if you don't need the return value).

### Backup and restore

```python
backup_bytes = client.backup_secret("db-password")      # bytes (encrypted)
client.restore_secret_backup(backup_bytes)              # restore to same vault
```

---

## KeyClient — Cryptographic Key Management

```python
from azure.keyvault.keys import KeyClient, KeyType, KeyCurveName, KeyOperation
from azure.identity import DefaultAzureCredential

credential = DefaultAzureCredential()
key_client = KeyClient(vault_url="https://my-vault.vault.azure.net", credential=credential)
```

### Creating keys

```python
# RSA key (signing, encryption)
rsa_key = key_client.create_rsa_key("my-rsa-key", size=2048)  # 2048, 3072, 4096
# OR equivalently:
rsa_key = key_client.create_key("my-rsa-key", KeyType.rsa, size=2048)

# EC key (signing, ECDH)
ec_key = key_client.create_ec_key("my-ec-key", curve="P-256")  # P-256, P-384, P-521
# OR:
ec_key = key_client.create_key("my-ec-key", KeyType.ec, curve=KeyCurveName.p256)

# Symmetric key (wrapping, AES encryption — Managed HSM only for software keys)
sym_key = key_client.create_oct_key("my-aes-key", size=256)
```

```python
# With optional parameters
key = key_client.create_rsa_key(
    "my-rsa-key",
    size=4096,
    key_operations=[KeyOperation.encrypt, KeyOperation.decrypt],
    tags={"app": "payments"},
    expires_on=datetime(2027, 1, 1),
)
```

### Retrieving and listing

```python
key = key_client.get_key("my-rsa-key")
print(key.name)
print(key.key_type)           # KeyType.rsa
print(key.properties.version)

# List keys — metadata only (no key material)
for props in key_client.list_properties_of_keys():
    print(props.name, props.key_type)

# All versions
for props in key_client.list_properties_of_key_versions("my-rsa-key"):
    print(props.version, props.enabled)
```

### Delete, recover, purge (same LRO pattern as secrets)

```python
key_client.begin_delete_key("my-rsa-key").result()
key_client.begin_recover_deleted_key("my-rsa-key").result()
key_client.purge_deleted_key("my-rsa-key")  # permanent
```

---

## CryptographyClient — Encrypt, Decrypt, Sign, Verify

The `CryptographyClient` performs crypto operations using a specific key. It requires its own `credential` parameter — it's separate from `KeyClient`.

```python
from azure.keyvault.keys.crypto import (
    CryptographyClient,
    EncryptionAlgorithm,
    SignatureAlgorithm,
    KeyWrapAlgorithm,
)

# Build from a key object
key = key_client.get_key("my-rsa-key")
crypto = CryptographyClient(key, credential=credential)

# OR build directly from a key ID (URI string)
crypto = CryptographyClient(
    "https://my-vault.vault.azure.net/keys/my-rsa-key",
    credential=credential,
)

# OR use the KeyClient helper (most convenient)
crypto = key_client.get_cryptography_client("my-rsa-key")
```

> **Common mistake**: `CryptographyClient(key)` raises `TypeError` — the `credential` parameter is required.

### Encrypt / Decrypt

```python
ciphertext = crypto.encrypt(EncryptionAlgorithm.rsa_oaep, b"plaintext").ciphertext
plaintext  = crypto.decrypt(EncryptionAlgorithm.rsa_oaep, ciphertext).plaintext
```

Common algorithms: `EncryptionAlgorithm.rsa_oaep`, `rsa_oaep_256`, `rsa1_5`

### Sign / Verify

```python
import hashlib

digest = hashlib.sha256(b"message to sign").digest()
signature = crypto.sign(SignatureAlgorithm.rs256, digest).signature
verified  = crypto.verify(SignatureAlgorithm.rs256, digest, signature).is_valid
```

Common algorithms: `SignatureAlgorithm.rs256`, `rs384`, `rs512`, `es256`, `es384`

### Wrap / Unwrap key

```python
wrapped   = crypto.wrap_key(KeyWrapAlgorithm.rsa_oaep, b"<symmetric-key-bytes>").encrypted_key
unwrapped = crypto.unwrap_key(KeyWrapAlgorithm.rsa_oaep, wrapped).key
```

---

## CertificateClient — Certificate Lifecycle

```python
from azure.keyvault.certificates import (
    CertificateClient,
    CertificatePolicy,
    CertificateContentType,
    WellKnownIssuerNames,
)
from azure.identity import DefaultAzureCredential

credential = DefaultAzureCredential()
cert_client = CertificateClient(
    vault_url="https://my-vault.vault.azure.net", credential=credential
)
```

### Create a self-signed certificate

```python
# Simplest: use default policy (self-signed, RSA 2048, 12 months)
policy = CertificatePolicy.get_default()
poller = cert_client.begin_create_certificate("my-cert", policy)
cert = poller.result()  # blocks until issued (can take 1–2 minutes)
print(cert.name, cert.properties.version)
```

### Custom policy

```python
policy = CertificatePolicy(
    issuer_name=WellKnownIssuerNames.self,    # "Self" = self-signed
    subject="CN=myapp.example.com",
    validity_in_months=24,
    exportable=True,
    key_type="RSA",
    key_size=2048,
    reuse_key=False,
    content_type=CertificateContentType.pkcs12,  # or pem
    san_dns_names=["myapp.example.com", "*.myapp.example.com"],
)
poller = cert_client.begin_create_certificate("myapp-tls", policy)
cert = poller.result()
```

### Get and list certificates

```python
cert = cert_client.get_certificate("my-cert")
print(cert.cer)           # bytes — DER-encoded certificate (public key only)
print(cert.properties.version)
print(cert.policy.subject)

# List all certificates (metadata only)
for props in cert_client.list_properties_of_certificates():
    print(props.name, props.expires_on)

# All versions of one cert
for props in cert_client.list_properties_of_certificate_versions("my-cert"):
    print(props.version)
```

### Import an existing certificate

```python
with open("existing-cert.pfx", "rb") as f:
    pfx_bytes = f.read()

cert = cert_client.import_certificate(
    "imported-cert",
    pfx_bytes,
    password=b"pfx-password",  # optional
    policy=CertificatePolicy(issuer_name=WellKnownIssuerNames.self, subject="CN=example"),
)
```

### Delete, recover, purge (same LRO pattern)

```python
cert_client.begin_delete_certificate("my-cert").result()
cert_client.begin_recover_deleted_certificate("my-cert").result()
cert_client.purge_deleted_certificate("my-cert")  # permanent
```

---

## Async Support

All three clients have async counterparts in `.aio` submodules. Use `async with` for proper cleanup.

```python
from azure.keyvault.secrets.aio import SecretClient
from azure.keyvault.keys.aio import KeyClient
from azure.keyvault.certificates.aio import CertificateClient
from azure.identity.aio import DefaultAzureCredential

async def main():
    async with DefaultAzureCredential() as credential:
        async with SecretClient("https://my-vault.vault.azure.net", credential) as client:
            secret = await client.get_secret("db-password")
            print(secret.value)

            # Async iteration
            async for props in client.list_properties_of_secrets():
                print(props.name)
```

LRO operations in async also return pollers — `await poller.result()`:
```python
poller = await client.begin_delete_secret("db-password")
deleted = await poller.result()
```

---

## Error Handling

```python
from azure.core.exceptions import ResourceNotFoundError, HttpResponseError

try:
    secret = client.get_secret("my-secret")
except ResourceNotFoundError:
    # 404 — secret doesn't exist (or was soft-deleted and not yet recovered)
    print("Secret not found")
except HttpResponseError as e:
    if e.status_code == 403:
        print("Access denied — check Key Vault access policy / RBAC role")
    elif e.status_code == 429:
        print("Throttled — back off and retry")
    else:
        raise
```

---

## Key Vault URL & Client Reuse

```python
# ✅ Correct vault URL formats
vault_url = "https://my-vault.vault.azure.net"    # standard
vault_url = "https://my-vault.vault.azure.net/"   # trailing slash also fine

# ❌ Wrong
vault_url = "https://my-vault.azure.com"          # wrong domain
vault_url = "https://my-vault"                    # missing domain

# Reuse a single client per vault — don't create a new one per request
# Creating many clients causes throttling (HTTP 429)
client = SecretClient(vault_url=VAULT_URL, credential=credential)
for name in secret_names:
    client.get_secret(name)  # ✅ reuse
```

---

## Common Mistakes Summary

| Mistake | Fix |
|---------|-----|
| `list_properties_of_secrets()` gives no `.value` | Call `client.get_secret(props.name)` separately |
| `begin_delete_secret()` without `.result()` | Always chain `.result()` to wait for completion |
| Re-creating a soft-deleted secret name | Recover or purge it first |
| `CryptographyClient(key)` with no credential | `CryptographyClient(key, credential=credential)` |
| Wrong vault URL (`.azure.com` etc.) | Use `https://{name}.vault.azure.net` |
| Creating a new client per request | Instantiate once and reuse |
