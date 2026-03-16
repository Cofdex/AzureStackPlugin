---
name: find-azure-skills
description: >
  Find and recommend the right Azure skill(s) from the AzureStackPlugin skills library
  based on what the user is trying to build or do. Use this skill whenever the user asks
  which skill to use, what skills are available, "which skill covers X", "do you have a
  skill for Y", "what should I use for Z on Azure", or any similar question about
  navigating or discovering skills in this plugin. Also trigger when the user describes
  an Azure task and you're not sure which skill applies — consult this skill first to
  find the best match before proceeding with implementation.
---

# Find Azure Skills

Help users discover the right skill(s) from the AzureStackPlugin library for their task.

## How to use this skill

1. Read `references/skills-catalog.md` — it contains every skill with its name, category, package, and one-line purpose.
2. Understand what the user is trying to accomplish (what Azure service, what action, what language/tool).
3. Match their need to the most relevant skill(s).
4. Present results clearly.

## Matching strategy

Think about what the user actually needs, not just keyword overlap:

- **Service name** — the most direct signal. "Cosmos DB" → `azure-cosmos` or `azure-cosmos-mongodb`.
- **Action/capability** — what they want to *do*: stream events → `azure-event-hubs`; send push notifications → `azure-notification-hubs`; cache data → `azure-redis`.
- **Category** — if they ask about IaC, Terraform, Bicep, architecture → look in the `design` category first.
- **Multiple skills** — some tasks genuinely need more than one skill (e.g., building an AI app with storage + OpenAI + Key Vault). List all relevant skills.
- **No exact match** — if nothing fits well, say so clearly and suggest the closest alternatives.

## Output format

Present results in this structure:

```
## Recommended skill(s) for: [summary of user's task]

### 1. `<skill-name>` (category: design | python)
**Package**: `<uv add ...>`
**Use for**: <one sentence on why this matches>

### 2. `<skill-name>` (if multiple apply)
...

---
**How to activate**: Mention the skill by name or describe your task — Claude will load
the relevant skill context automatically.
```

If the user asks for a full list or catalog, render the skills-catalog.md table directly.

## Quick category guide

| If the user wants to... | Look here |
|---|---|
| Design architecture, draw diagrams, plan infrastructure | `design/` |
| Write Bicep or ARM templates | `azure-bicep` |
| Write Terraform for Azure | `azure-terraform` |
| Authenticate Python code to Azure | `azure-identity` (always recommend alongside other skills) |
| Store secrets, keys, certs | `azure-keyvault` |
| Use OpenAI / GPT on Azure | `azure-openai` |
| Build AI agents | `agent-framework-azure-ai` or `container-agents-azure-ai` |
| Store blobs/files | `azure-blob-storage`, `azure-file-shares`, or `azure-datalake` |
| Run serverless code | `azure-functions` |
| Deploy containers | `azure-container-apps` or `azure-aks` |
| Stream events | `azure-event-hubs` |
| Queue messages | `azure-service-bus` or `azure-queue-storage` |
| Translate or analyze text (NLP) | `azure-ai-textanalytics`, `azure-ai-translation-text` |
| Transcribe speech | `azure-ai-transcription` or `azure-speech-stt-rest` |
| Search documents | `azure-ai-search` |
| Store structured data (NoSQL) | `azure-cosmos`, `azure-cosmos-mongodb`, or `azure-data-tables` |
| Store structured data (SQL) | `azure-sql` or `azure-postgres-flexible` |
| Monitor/observe applications | `azure-application-insights` or `azure-monitor-query` |
| Work with CI/CD or work items | `azure-devops-sdk` |
| Build REST APIs with Python | `fastapi-crud` + `pydantic-models` |
| Add cross-session memory to agents | `continual-learning` |

See `references/skills-catalog.md` for the full catalog with packages and detailed descriptions.
