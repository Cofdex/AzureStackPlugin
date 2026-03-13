# AzureStackPlugin Skills Catalog

Complete list of all available skills. 53 skills across 3 categories.

## Design Skills (Infrastructure & Architecture)

| Skill | Install / Tool | What it does |
|---|---|---|
| `azure-architecture-patterns` | *(no package)* | Design Azure solutions using Well-Architected Framework 5 pillars, hub-spoke, landing zones, microservices, CQRS, API Gateway patterns, and Mermaid diagrams |
| `azure-bicep` | `az bicep` / Bicep CLI | Write Azure Bicep IaC: params, vars, resources, outputs, modules, Key Vault integration, loops, conditionals |
| `azure-terraform` | `terraform` + AzureRM provider | Write Terraform IaC for Azure: provider config, auth, remote state, modules, multi-env tfvars |

---

## Python Skills

### AI & Machine Learning

| Skill | `pip install` | What it does |
|---|---|---|
| `azure-openai` | `openai azure-identity` | Chat completions, embeddings, DALL-E, streaming, function calling via Azure OpenAI (GPT-4, GPT-3.5) |
| `azure-ai-projects` | `azure-ai-projects>=2.0.0` | High-level Microsoft Foundry SDK: AIProjectClient, versioned AI assets, connections, deployments |
| `agent-framework-azure-ai` | `azure-ai-projects azure-ai-agents azure-identity` | Build Azure AI Foundry agents with tools, thread management, streaming responses |
| `container-agents-azure-ai` | `azure-ai-agentserver-core` | Deploy container-based Foundry Agents (ImageBasedHostedAgentDefinition) |
| `azure-ai-ml` | `azure-ai-ml azure-identity` | Azure ML SDK v2: MLClient, training jobs, pipelines, model registration, compute clusters |
| `azure-foundry-evaluations` | `azure-ai-evaluation` | Evaluate LLM outputs: quality, safety, NLP evaluators, batch evaluation against datasets |

### AI Cognitive Services

| Skill | `pip install` | What it does |
|---|---|---|
| `azure-ai-search` | `azure-search-documents azure-identity` | Full-text, vector, hybrid, semantic search; index management; document ingestion |
| `azure-ai-textanalytics` | `azure-ai-textanalytics azure-identity` | NLP: sentiment analysis, NER, key phrases, language detection, PII extraction |
| `azure-ai-document-intelligence` | `azure-ai-documentintelligence azure-identity` | Extract text, tables, key-value pairs from PDFs and images (prebuilt + custom models) |
| `azure-ai-vision-imageanalysis` | `azure-ai-vision-imageanalysis` | Image captioning, object detection, OCR, content tags, people detection |
| `azure-ai-face` | `azure-ai-vision-face azure-identity` | Face detection, 1:N identification, 1:1 verification, liveness detection |
| `azure-ai-transcription` | `azure-ai-transcription azure-identity` | Batch speech-to-text with TranscriptionClient (async, files/URLs) |
| `azure-speech-stt-rest` | `requests` | Simple synchronous speech-to-text via REST API (no SDK, audio ≤60s) |
| `azure-ai-voicelive` | `azure-ai-voicelive[aiohttp]` | Real-time bidirectional voice AI over WebSocket (VoiceLiveConnection, async-only) |
| `azure-ai-translation-text` | `azure-ai-translation-text` | Real-time text translation, transliteration, language detection |
| `azure-ai-translation-document` | `azure-ai-translation-document azure-identity` | Batch document translation (DocumentTranslationClient, whole containers) |
| `azure-ai-contentsafety` | `azure-ai-contentsafety` | Detect harmful content in text/images (ContentSafetyClient, BlocklistClient) |
| `azure-ai-contentunderstanding` | `azure-ai-contentunderstanding` | Multimodal content extraction (ContentUnderstandingClient) |
| `azure-ai-video-indexer` | `requests azure-identity` | Upload videos, extract transcripts/keywords/faces/emotions via REST API |

### Storage & Data

| Skill | `pip install` | What it does |
|---|---|---|
| `azure-blob-storage` | `azure-storage-blob azure-identity` | Upload, download, list, manage blobs and containers (BlobServiceClient, BlobClient) |
| `azure-datalake` | `azure-storage-file-datalake azure-identity` | Data Lake Gen2: hierarchical namespace, large file uploads (append+flush), ACLs |
| `azure-file-shares` | `azure-storage-file-share azure-identity` | Create shares, upload/download files, list directories (ShareServiceClient) |
| `azure-queue-storage` | `azure-storage-queue azure-identity` | Send, receive, delete messages from Azure Storage queues (QueueClient) |
| `azure-data-tables` | `azure-data-tables azure-identity` | NoSQL key-value storage: Azure Storage Tables + Cosmos DB Tables API |
| `azure-cosmos` | `azure-cosmos azure-identity` | Cosmos DB NoSQL API: document CRUD, SQL queries, containers (CosmosClient) |
| `azure-cosmos-mongodb` | `pymongo` | Cosmos DB MongoDB API using pymongo driver (MongoDB-compatible) |
| `azure-sql` | `pyodbc sqlalchemy azure-identity` | Azure SQL Database: queries, parameterized statements, AAD token auth, connection pooling |
| `azure-postgres-flexible` | `psycopg2-binary asyncpg azure-identity` | Azure PostgreSQL Flexible Server: sync (psycopg2) and async (asyncpg) connections |
| `azure-redis` | `redis` | Azure Cache for Redis: caching, sessions, pub/sub, rate limiting (redis-py / aioredis) |

### Messaging & Events

| Skill | `pip install` | What it does |
|---|---|---|
| `azure-service-bus` | `azure-servicebus azure-identity` | Reliable message queuing, pub/sub (topics/subscriptions), dead-letter handling |
| `azure-event-hubs` | `azure-eventhub azure-eventhub-checkpointstoreblob azure-identity` | High-throughput event streaming, IoT telemetry, Kafka-compatible pipelines |
| `azure-event-grid` | `azure-eventgrid azure-identity` | Publish events to Event Grid topics, webhook delivery, event-driven integrations |
| `azure-notification-hubs` | `azure-mgmt-notificationhubs` | Push notifications to iOS (APNS), Android (FCM), Windows (WNS) |

### Compute & Containers

| Skill | `pip install` | What it does |
|---|---|---|
| `azure-functions` | `azure-functions` | Serverless functions (v2 model): HTTP, timer, queue, blob, Service Bus, Event Hub triggers |
| `azure-container-apps` | `azure-mgmt-appcontainers azure-identity` | Deploy/manage container apps, environments, ingress, scaling, Dapr |
| `azure-aks` | `azure-mgmt-containerservice azure-identity` | Create AKS clusters, manage node pools, get kubeconfig, scale |
| `azure-containerregistry` | `azure-containerregistry azure-identity` | Manage ACR: push/pull images, OCI artifacts, list repositories/tags |

### Security & Configuration

| Skill | `pip install` | What it does |
|---|---|---|
| `azure-identity` | `azure-identity` | All Azure auth patterns: DefaultAzureCredential, ClientSecretCredential, managed identity, token providers |
| `azure-keyvault` | `azure-keyvault-secrets azure-identity` | Store/retrieve secrets, manage encryption keys, certificates (SecretClient, KeyClient, CertificateClient) |
| `azure-appconfiguration` | `azure-appconfiguration` | Centralized config: key-value settings, feature flags, dynamic refresh |

### Networking & Integration

| Skill | `pip install` | What it does |
|---|---|---|
| `azure-apim` | `azure-mgmt-apimanagement azure-identity` | Manage APIs, products, subscriptions, policies, backends in APIM |
| `azure-communication-services` | `azure-communication-email` + others | Send email (EmailClient), SMS (SmsClient), manage identities |
| `azure-digital-twins` | `azure-digitaltwins-core azure-identity` | Create/query digital twin instances, DTDL models, relationships, twin graph |

### Observability & DevOps

| Skill | `pip install` | What it does |
|---|---|---|
| `azure-application-insights` | `azure-monitor-opentelemetry opentelemetry-api` | Distributed tracing, custom metrics, structured logging via OpenTelemetry |
| `azure-monitor-query` | `azure-monitor-query azure-identity` | Run KQL queries against Log Analytics workspaces; query Azure Monitor metrics |
| `azure-monitor-ingestion` | `azure-monitor-ingestion azure-identity` | Send custom logs/telemetry to Log Analytics via Logs Ingestion API (DCR/DCE) |
| `azure-devops-sdk` | `azure-devops msrest` | Automate ADO: work items, repositories, builds, pipelines |

### General Python Patterns

| Skill | `pip install` | What it does |
|---|---|---|
| `fastapi-crud` | *(FastAPI project)* | Build FastAPI REST API routers with CRUD operations, auth dependencies, Pydantic response models |
| `pydantic-models` | *(Pydantic v2)* | Create Pydantic v2 models: Base/Create/Update/Response/InDB multi-model pattern |

---

## Plugin Infrastructure Skills

| Skill | Install | What it does |
|---|---|---|
| `continual-learning` | `cp -r hooks/continual-learning .github/hooks/` | Hooks + memory patterns for AI coding agents: sessionStart/postToolUse/sessionEnd lifecycle, two-tier SQLite memory (global + local), reflection patterns |

---

## Common Combinations

| Use case | Skills to combine |
|---|---|
| Secure Python app accessing Azure | `azure-identity` + any service skill |
| AI chatbot on Azure | `azure-openai` + `azure-ai-search` + `azure-keyvault` |
| AI agent with tools | `agent-framework-azure-ai` + `azure-blob-storage` |
| FastAPI microservice | `fastapi-crud` + `pydantic-models` + `azure-identity` |
| MLOps pipeline | `azure-ai-ml` + `azure-blob-storage` + `azure-application-insights` |
| Event-driven architecture | `azure-event-hubs` + `azure-functions` + `azure-service-bus` |
| Document processing | `azure-ai-document-intelligence` + `azure-blob-storage` + `azure-cosmos` |
