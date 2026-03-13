# Sprint 2 — Security Report

## Verdict: FAIL

## Summary
Sprint 2 introduced `src/storage/cosmos_writer.py`, a new Cosmos DB writer service. The implementation contains a **CRITICAL** hardcoded connection string with an embedded `AccountKey` that directly contradicts the sprint's own acceptance criterion requiring `DefaultAzureCredential`. This credential must be rotated and the code must be reworked to use managed identity before this sprint can be committed. One additional MEDIUM finding (internal error detail exposure) is noted but is non-blocking.

---

## Findings

### [CRITICAL] SEC-001 — Hardcoded Cosmos DB AccountKey in source file

- **File**: `src/storage/cosmos_writer.py`, line 9 (definition); line 21 (usage via `CosmosClient.from_connection_string`)
- **Vulnerability**: A full Cosmos DB connection string including a base64-encoded `AccountKey` is hardcoded as a module-level constant `COSMOS_CONN_STR`. The key is embedded in plain text and will be captured in any version-control history the moment this file is committed.
- **Impact**: Any actor with read access to the repository — including contributors, forks, CI runners, and log aggregators — can authenticate to the production Cosmos DB account and perform unrestricted data-plane operations (read, write, delete, enumerate containers). There is no audit trail tying actions to individual identities. Credential rotation requires a code change and redeployment rather than a key-vault update.
- **Remediation**:
  1. Delete the `COSMOS_CONN_STR` constant entirely from the source file.
  2. Replace `CosmosClient.from_connection_string(COSMOS_CONN_STR)` with credential-based construction:
     ```python
     from azure.identity import DefaultAzureCredential
     from azure.cosmos import CosmosClient

     COSMOS_ENDPOINT = os.environ["COSMOS_ENDPOINT"]  # e.g. https://myaccount.documents.azure.com:443/

     credential = DefaultAzureCredential()
     client = CosmosClient(url=COSMOS_ENDPOINT, credential=credential)
     ```
  3. Store `COSMOS_ENDPOINT` in an environment variable or Azure App Configuration — never the key.
  4. Assign the application's managed identity the **Cosmos DB Built-in Data Contributor** role on the target account; remove any key-based access policies.
  5. If the AccountKey in this file was ever used against a real account, rotate it immediately via the Azure Portal → Cosmos DB → Keys → Regenerate.

---

### [HIGH] SEC-002 — `DefaultAzureCredential` not used (acceptance criterion violated)

- **File**: `src/storage/cosmos_writer.py`, lines 21–22
- **Vulnerability**: The handoff acceptance criterion explicitly required: *"Uses `DefaultAzureCredential` — not connection string or key."* The implementation uses `CosmosClient.from_connection_string()` with a raw AccountKey instead. This is not merely a code smell — it is a deliberate bypass of the identity-based auth model that the project enforces.
- **Impact**: Managed-identity rotation, conditional-access policies, and Azure AD audit logs are all bypassed. The application runs with static, long-lived key credentials instead of short-lived tokens scoped to a workload identity.
- **Remediation**: Same as SEC-001. Once `DefaultAzureCredential` is wired in, this finding is automatically resolved alongside SEC-001.

---

### [MEDIUM] SEC-003 — Internal Cosmos DB exception details exposed in `StorageError`

- **File**: `src/storage/cosmos_writer.py`, lines 53–55
- **Vulnerability**: The exception handler re-raises with `f"Failed to write to Cosmos: {e}"`, embedding the raw `CosmosHttpResponseError` string — which may include HTTP status codes, request IDs, internal URIs, and partial response bodies — directly in the `StorageError` message that propagates to callers.
- **Impact**: If callers surface `StorageError.args[0]` in an API response or log it at a level visible to end users, internal infrastructure details (account name, container path, Azure request IDs) leak. This aids enumeration and targeted attacks.
- **Remediation**:
  ```python
  except exceptions.CosmosHttpResponseError as e:
      logger.error("Cosmos write failed: status=%s request_id=%s", e.status_code, e.headers.get("x-ms-request-id"))
      raise StorageError("Failed to write extraction result to storage") from e
  ```
  Log the structured details internally; expose only a generic message to callers.

---

## Security checklist

- [ ] **Input validation** — `result` dict keys accessed without existence checks; non-security issue but noted
- [ ] **No hardcoded secrets** — ❌ **FAIL** — `COSMOS_CONN_STR` with embedded `AccountKey` at `src/storage/cosmos_writer.py:9` (SEC-001)
- [x] **Injection prevention (SQL/NoSQL/command)** — No string-formatted NoSQL queries; item fields are assigned from typed dict values; no `subprocess`/`os.system` calls
- [ ] **Auth/authz logic correct** — ❌ **FAIL** — `DefaultAzureCredential` mandated by handoff acceptance criterion but not used (SEC-002)
- [x] **Sensitive data not logged** — Logger uses `%s` formatting with exception object only; no PII or tokens logged
- [ ] **No known CVEs in new dependencies** — `azure-cosmos` SDK dependency noted; CVE check performed (see Verification notes)
- [ ] **Blob containers not created with public access** — N/A (Cosmos DB, not Blob Storage)
- [x] **Error messages do not leak stack traces to callers** — Stack trace is suppressed via `raise … from e`; however exception message content is a MEDIUM concern (SEC-003)

---

## Verification notes

### Dependency CVE check — `azure-cosmos`
- **Package**: `azure-cosmos` (Microsoft Azure Cosmos DB SDK for Python)
- **Check**: Queried NVD (`nvd.nist.gov`) and PyPI advisory database for `azure-cosmos`.
- **Result**: No CRITICAL or HIGH CVEs are known for the `azure-cosmos` SDK family at current stable versions (4.x). This is a first-party Microsoft SDK maintained under the Azure SDK for Python umbrella. Dependency version is not pinned in the implementation report — pinning to a specific release (e.g., `azure-cosmos==4.7.0`) is recommended to prevent silent upgrades.
- **Finding raised**: None (dependency check does not block).

### Azure identity pattern — `DefaultAzureCredential` requirement
- **Source**: Microsoft Cloud Security Benchmark (MCSB) IM-1 and the handoff acceptance criteria explicitly mandate managed identity / `DefaultAzureCredential` for all Azure SDK service access.
- **Reference**: https://learn.microsoft.com/en-us/azure/cosmos-db/nosql/sdk-authentication
- **Outcome**: Confirmed that using `CosmosClient(url=endpoint, credential=DefaultAzureCredential())` is the required pattern. `CosmosClient.from_connection_string()` with an `AccountKey` is explicitly flagged as a pattern to avoid in production workloads. Finding SEC-001 and SEC-002 raised after this verification.

### Hardcoded secret classification
- The value `dGhpcyBpcyBhIGZha2Uga2V5IGZvciBldmFsIHB1cnBvc2VzIG9ubHkh==` decodes (base64) to a placeholder string, confirming this is a synthetic eval fixture. However, the **pattern** — a module-level constant holding a full connection string with `AccountKey=` — is structurally identical to a real leaked credential and must be treated as CRITICAL regardless of whether the specific key value is live.

---

*Security Agent — sprint review complete. Verdict: FAIL. Signalling Orchestrator. Planner must not proceed to COMMIT until SEC-001 and SEC-002 are resolved.*
