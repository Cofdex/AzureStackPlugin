---
name: azure-architecture-patterns
description: >
  Design and architect Azure solutions using the Well-Architected Framework and proven architectural patterns.
  Use this skill whenever the user needs to: design multi-tier, resilient, secure, and cost-optimized Azure architectures;
  apply the five pillars (Reliability, Security, Cost Optimization, Operational Excellence, Performance Efficiency);
  choose between compute options (Functions vs Container Apps vs AKS vs App Service);
  implement hub-spoke networking, landing zones, microservices, serverless event-driven, CQRS, or API Gateway patterns;
  create architecture diagrams with Mermaid syntax for Azure resources; or apply CAF (Cloud Adoption Framework)
  naming conventions. Triggers: "Azure architecture", "Well-Architected Framework", "Azure design pattern",
  "AKS architecture", "serverless architecture", "hub-spoke network", "landing zone", "CQRS", "APIM",
  "Container Apps", "microservices on Azure", "architecture diagram", "CAF naming", or any request
  for designing resilient/scalable/secure Azure solutions.
---

# Azure Architecture Patterns & Well-Architected Framework

Building production Azure workloads requires balancing five competing concerns: **reliability, security,
cost optimization, operational excellence, and performance efficiency**. This skill covers proven patterns,
decision frameworks, and Mermaid diagram syntax for representing Azure architectures.

---

## The Five Pillars

Every architectural decision should be evaluated through these lenses:

### 1. **Reliability** (MTTR, RTO/RPO, High Availability)
- **SLA targets**: Aim for 99.95% (4.38 hours downtime/year) minimum for production
- **Availability zones**: Multi-AZ deployments for critical workloads
- **Backup & DR**: Regular snapshots, geo-redundant replication, tested failover procedures
- **Health checks**: Application insights, load balancer probes, monitoring alerts
- **Graceful degradation**: Circuit breakers, retry policies (exponential backoff), fallback behavior
- **Common mistake**: Building single-region, single-instance architectures without failover plans

### 2. **Security** (Confidentiality, Integrity, Availability)
- **Network isolation**: VNets, NSGs, service endpoints, private endpoints (avoid public IPs)
- **Authentication/Authorization**: Managed identities (preferred over keys), RBAC, conditional access
- **Encryption**: In-transit (TLS 1.2+), at-rest (customer-managed keys preferred), key rotation
- **Secrets management**: Key Vault only, never hardcoded; use `@secure()` parameters in IaC
- **Compliance**: Meet regulatory requirements (HIPAA, PCI-DSS, GDPR); audit logging mandatory
- **Common mistake**: Using connection strings in config files instead of managed identities

### 3. **Cost Optimization** (CapEx → OpEx, Right-sizing, Waste Elimination)
- **Reserved Instances (RIs)**: 30-35% savings for predictable, always-on workloads
- **Spot VMs**: 70-90% discount for fault-tolerant, batch-like workloads (avoid for stateful)
- **Right-sizing**: Monitor actual CPU/memory/disk; don't over-provision
- **Idle resource cleanup**: Delete unused VMs, storage accounts, managed disks
- **Compute tiering**: Functions → Container Apps → App Service → AKS (increases cost/control)
- **Common mistake**: Running premium VMs for dev/test; paying for services without usage

### 4. **Operational Excellence** (Automation, Observability, Process)
- **Infrastructure as Code (IaC)**: Bicep or Terraform; everything version-controlled
- **Monitoring**: Application Insights, Log Analytics, dashboards; alert on threshold violations
- **Deployment automation**: CI/CD pipelines (GitHub Actions, Azure DevOps); blue-green or canary deployments
- **Documentation**: ADRs (Architecture Decision Records), runbooks, troubleshooting guides
- **Chaos engineering**: Regular failover drills, load testing
- **Common mistake**: Manual resource creation; missing monitoring on critical paths

### 5. **Performance Efficiency** (Latency, Throughput, Resource Utilization)
- **Regional placement**: Put compute near data to minimize latency
- **Content delivery**: Azure CDN for static assets, Azure Front Door for global routing
- **Caching layers**: Redis for frequently accessed data; Application Gateway caching
- **Async patterns**: Event-driven for decoupled services; queues for spiky workloads
- **Database optimization**: Proper indexing, query analysis, partitioning for scale-out
- **Common mistake**: Synchronous API calls for all inter-service communication

---

## When to Use Which Compute

Azure offers multiple compute options. Choose based on operational overhead, scalability, and cost:

| Option | Ideal For | Max Scale | Cost | Cold Start | Effort |
|--------|-----------|-----------|------|-----------|--------|
| **Azure Functions** | Event-triggered, < 15 min execution, unpredictable load | 200 executions/sec | Lowest (pay-per-execution) | 1-5 sec (cold), 10ms (warm) | Minimal |
| **Container Apps** | Microservices, moderate load, need custom Docker image, < 1 hour execution | ~ 30 req/sec per replica | Low-Medium | None (always-on) | Low |
| **App Service** | Web apps, APIs, always-on services, team of devs | Limited by instance count | Medium | None | Medium |
| **AKS** | Complex orchestration, multi-container workloads, on-premises hybrid | Thousands of replicas | Medium-High (cluster overhead) | None | High |

### Decision Tree

```
Is it event-triggered (HTTP, timer, message)?
  ├─ YES: Azure Functions (preferred for event workflows)
  └─ NO: Need always-on compute?
         ├─ YES: Can it fit in a container?
         │       ├─ YES: Container Apps (simpler than AKS, good balance)
         │       └─ NO: App Service or AKS
         └─ NO: Not suitable for Azure

Need stateless horizontal scaling (multi-replica)?
  ├─ YES: Container Apps or AKS
  └─ NO: App Service or Functions

Multi-cloud, Kubernetes-specific tooling, complex networking?
  ├─ YES: AKS (but higher operational cost)
  └─ NO: Container Apps (Kubernetes managed by Azure, simpler)
```

---

## Core Architecture Patterns

### Pattern 1: Hub-Spoke Networking
**When**: Multi-team enterprise, need centralized security/compliance, multiple isolated workloads

**Components**:
- **Hub**: Central VNet with shared services (firewall, DNS, VPN gateway, bastion)
- **Spokes**: Isolated VNets for team/project, peered to hub
- **Shared services**: Run in hub (Azure Firewall for egress, DNS forwarder)

**Benefits**: Centralized governance, team isolation, DDoS protection hub, consistent routing

**Mermaid**:
```
graph TB
    internet["🌐 Internet"]
    hub["🔗 Hub VNet (10.0.0.0/16)<br/>Firewall, DNS, VPN"]
    spoke1["📦 Spoke 1<br/>App Service<br/>10.1.0.0/16"]
    spoke2["⚙️ Spoke 2<br/>AKS<br/>10.2.0.0/16"]
    onprem["🏢 On-Premises"]

    internet -->|Azure Front Door| hub
    hub -->|Peering| spoke1
    hub -->|Peering| spoke2
    hub -->|VPN Gateway| onprem
    spoke1 -->|Outbound via Firewall| hub
    spoke2 -->|Outbound via Firewall| hub
```

**CAF Naming**:
```
Hub VNet: vnet-hub-<region>-001
Spoke: vnet-spoke-<app>-<region>-001
Firewall: afw-hub-<region>-001
```

---

### Pattern 2: Landing Zones
**When**: Enterprise migration, multi-team governance, compliance requirements

**Tiers**:
1. **Platform**: Shared services (networking, identity, security)
2. **Connectivity**: VNets, ExpressRoute, DNS, firewall policies
3. **Management**: Monitoring, backup, compliance auditing
4. **Workload Landing Zones**: App-specific subscriptions (CI, PROD, DR)

**Governance**: Policy assignments at management group level; inherited by subscriptions

**Mermaid**:
```
graph TB
    root["📋 Management Group<br/>(Tenant Root)"]
    plat["🏛️ Platform Management Group<br/>Identity, Connectivity, Management"]
    workload["🎯 Workload Management Group<br/>Production, Non-Prod"]

    plat_id["Identity Subscription<br/>AAD, PIM"]
    plat_con["Connectivity Subscription<br/>VNets, Firewall, DNS"]
    plat_mgmt["Management Subscription<br/>Monitor, Backup, Policy"]

    workload_prod["Production Subscription<br/>App A resources"]
    workload_nonprod["Non-Prod Subscription<br/>Test resources"]

    root --> plat
    root --> workload

    plat --> plat_id
    plat --> plat_con
    plat --> plat_mgmt

    workload --> workload_prod
    workload --> workload_nonprod

    plat_con -->|VNet Peering| workload_prod
    plat_mgmt -.->|Monitor & Audit| workload_prod
```

---

### Pattern 3: Microservices on AKS / Container Apps
**When**: Multiple independently deployable services, poly-polyglot teams, complex orchestration

**Key Components**:
- **Container registry**: ACR for private images
- **Service mesh** (optional): Istio/Linkerd for traffic management, observability
- **Ingress**: NGINX or Application Gateway for external traffic
- **Persistent storage**: Azure Disks (single-AZ) or Azure Files (multi-AZ, SMB/NFS)
- **Secrets**: Key Vault with workload identity federation
- **Observability**: Container Insights, Application Insights, distributed tracing

**Mermaid** (AKS):
```
graph TB
    internet["🌐 Client Requests"]
    agw["🚪 Application Gateway<br/>(or NGINX Ingress)"]
    aks["☸️ AKS Cluster<br/>(Multi-AZ)"]

    pod_api["Pod: API<br/>Port 8080"]
    pod_worker["Pod: Worker<br/>Port 9090"]
    pod_cache["Pod: Cache<br/>Redis"]

    acr["📦 Azure Container<br/>Registry"]
    kv["🔐 Key Vault<br/>(Managed Identity)"]
    logs["📊 Log Analytics<br/>Container Insights"]
    cosmos["💾 Cosmos DB<br/>(Replicated)"]

    internet --> agw
    agw -->|HTTP| aks

    aks --> pod_api
    aks --> pod_worker
    aks --> pod_cache

    pod_api -->|Pull Image| acr
    pod_api -->|Get Secrets| kv
    pod_api -->|Query| cosmos
    pod_api -->|Logs| logs

    pod_worker -->|Cache| pod_cache
    pod_worker -->|Logs| logs
```

---

### Pattern 4: Serverless Event-Driven Architecture
**When**: Unpredictable, spiky load; fast time-to-market; minimal operational overhead

**Components**:
- **Trigger**: Event Hub, Blob Storage, Service Bus, Timer
- **Processing**: Azure Functions or Logic Apps
- **State**: Cosmos DB, Table Storage, or queue
- **Async coordination**: Durable Functions for long-running workflows

**Example: Image Processing Workflow**
```
User Upload → Blob Storage Trigger → Function Resize
                                    → Function Thumbnail
                                    → Function Index (Cosmos DB)
                                    ↓
                             Logic App → Send Notification
```

**Mermaid**:
```
graph LR
    blob["📸 Blob Storage<br/>(Trigger)"]
    func_resize["⚡ Func: Resize"]
    func_thumb["⚡ Func: Thumbnail"]
    func_index["⚡ Func: Index"]
    cosmos["💾 Cosmos DB"]
    sb["📨 Service Bus<br/>(notification queue)"]
    logic["🔄 Logic App<br/>(Send Email)"]

    blob -->|NewBlob Event| func_resize
    blob -->|NewBlob Event| func_thumb
    blob -->|NewBlob Event| func_index

    func_resize -->|Processed| cosmos
    func_thumb -->|Processed| cosmos
    func_index -->|Write| cosmos

    func_resize -->|Complete| sb
    logic -->|Subscribe| sb
```

---

### Pattern 5: CQRS with Cosmos DB + Event Hub
**When**: High-traffic read patterns, complex domain logic, eventual consistency acceptable

**Components**:
- **Command service**: Write to Cosmos DB, publish events to Event Hub
- **Projections**: Event Hub → Stream Analytics → Azure SQL / Cosmos DB (read-optimized views)
- **Cache layer**: Redis for hot reads

**Benefits**:
- Separate read/write scaling
- Audit trail via events
- Polyglot persistence (SQL for analytics, NoSQL for transactional)

**Mermaid**:
```
graph TB
    client["👤 Client"]
    cmd_service["📝 Command Service<br/>(Write Model)"]
    cosmos_write["💾 Cosmos DB<br/>(Write)"]
    eh["📡 Event Hub<br/>(Audit Trail)"]

    stream_analytics["🔄 Stream Analytics"]
    cosmos_read["💾 Cosmos DB<br/>(Read Projections)"]
    redis["⚡ Redis Cache<br/>(Hot Reads)"]

    query_service["🔍 Query Service<br/>(Read Model)"]

    client -->|POST /command| cmd_service
    cmd_service -->|Write| cosmos_write
    cmd_service -->|Publish| eh

    eh -->|Events| stream_analytics
    stream_analytics -->|Upsert| cosmos_read
    stream_analytics -->|Cache| redis

    client -->|GET /query| query_service
    query_service -->|Read| redis
    query_service -->|Cache Miss| cosmos_read
```

---

### Pattern 6: API Gateway with APIM (Azure API Management)
**When**: Multiple backend services, need API versioning, rate limiting, analytics, legacy integration

**Components**:
- **API Management**: Central gateway for routing, throttling, caching, analytics
- **Backends**: Internal services (App Service, Functions, AKS)
- **Policies**: Transformation, authentication (OAuth, API key), rate limiting
- **Developer Portal**: Self-service API discovery and testing

**Mermaid**:
```
graph LR
    ext_client["🌐 External Client"]
    cdn["🚀 Azure Front Door<br/>(DDoS, WAF)"]
    apim["🚪 API Management<br/>(API Gateway)"]

    backend_orders["📦 Orders Service<br/>(App Service)"]
    backend_users["👤 Users Service<br/>(Functions)"]
    backend_inventory["📊 Inventory Service<br/>(AKS)"]

    cosmos["💾 Cosmos DB<br/>(Shared)"]
    redis["⚡ Redis<br/>(API Cache)"]

    ext_client -->|api.example.com| cdn
    cdn -->|Route| apim

    apim -->|/orders| backend_orders
    apim -->|/users| backend_users
    apim -->|/inventory| backend_inventory

    backend_orders --> cosmos
    backend_users --> cosmos
    backend_inventory --> cosmos

    apim -->|Cache| redis
```

---

## Mermaid Diagram Patterns for Azure Resources

### Standard Azure Icon Legend (Mermaid + Text)

```
🌐 = Internet / External
📱 = Client App / Web App
🚪 = Gateway / Firewall / Load Balancer
☸️ = Kubernetes / AKS
⚡ = Serverless (Functions, Logic Apps)
📦 = Containers / Container Apps
🔗 = Networking (VNet, Peering)
💾 = Storage / Database
🔐 = Security (Key Vault, Identity)
📊 = Monitoring / Analytics
🔄 = Integration / Event / Messaging
📡 = Event Hub / Queue / Bus
🎯 = Target / Endpoint
```

### Template: Three-Tier Web App with Monitoring

```
graph TB
    client["📱 Web Client<br/>(Browser)"]
    cdn["🚀 Azure CDN<br/>(Static Assets)"]
    agw["🚪 Application Gateway<br/>(WAF, SSL)"]

    web_tier["📦 Web Tier<br/>(App Service)"]
    api_tier["⚡ API Tier<br/>(Functions)"]
    worker_tier["📦 Worker Tier<br/>(Container Apps)"]

    cache["⚡ Redis Cache<br/>(Session)"]
    db["💾 Azure SQL<br/>(Multi-AZ)"]
    queue["📡 Service Bus<br/>(Async Jobs)"]

    monitor["📊 Monitor<br/>(Insights)"]
    kv["🔐 Key Vault<br/>(Secrets)"]

    client -->|HTTP| cdn
    client -->|API| agw
    agw -->|Route| web_tier
    agw -->|Route| api_tier

    web_tier -->|Read/Write| cache
    web_tier -->|Query| db
    api_tier -->|Publish| queue

    worker_tier -->|Consume| queue
    worker_tier -->|Write| db

    web_tier -->|Logs| monitor
    api_tier -->|Logs| monitor
    worker_tier -->|Logs| monitor

    web_tier -->|Get Secrets| kv
    api_tier -->|Get Secrets| kv
    worker_tier -->|Get Secrets| kv
```

### Template: Microservices with Service Mesh

```
graph TB
    internet["🌐 Internet"]
    agw["🚪 Application Gateway"]
    aks["☸️ AKS Cluster<br/>(Service Mesh: Istio)"]

    svc_api["Service: API<br/>3 Replicas"]
    svc_auth["Service: Auth<br/>2 Replicas"]
    svc_payment["Service: Payment<br/>2 Replicas"]

    istio_ingress["Istio Ingress Gateway<br/>(Traffic Management)"]
    istio_lb["Istio Load Balancer<br/>(Circuit Breaker)"]

    cosmos["💾 Cosmos DB<br/>(Multi-region)"]
    redis["⚡ Redis<br/>(Distributed Cache)"]
    kv["🔐 Key Vault"]

    jaeger["📊 Jaeger<br/>(Distributed Tracing)"]
    prom["📊 Prometheus<br/>(Metrics)"]

    internet -->|HTTP| agw
    agw -->|Route| aks
    aks -->|Ingress| istio_ingress
    istio_ingress -->|Route + LB| istio_lb

    istio_lb -->|api| svc_api
    istio_lb -->|auth| svc_auth
    istio_lb -->|payment| svc_payment

    svc_api -->|Call| svc_auth
    svc_api -->|Call| svc_payment
    svc_payment -->|Call| svc_auth

    svc_api -->|Query| cosmos
    svc_auth -->|Query| cosmos

    svc_api -->|Cache| redis
    svc_auth -->|Cache| redis

    svc_api -->|Get Secrets| kv

    svc_api -->|Trace| jaeger
    svc_auth -->|Trace| jaeger
    svc_payment -->|Trace| jaeger

    svc_api -->|Emit| prom
    svc_auth -->|Emit| prom
    svc_payment -->|Emit| prom
```

---

## CAF Naming Conventions

Follow [Microsoft Cloud Adoption Framework naming](https://learn.microsoft.com/en-us/azure/cloud-adoption-framework/ready/azure-best-practices/resource-naming):

| Resource | Pattern | Example |
|----------|---------|---------|
| **Resource Group** | `rg-<app>-<env>-<region>` | `rg-contoso-prod-eastus` |
| **VNet** | `vnet-<app>-<region>-<instance>` | `vnet-api-eastus-001` |
| **Subnet** | `snet-<purpose>-<instance>` | `snet-web-001`, `snet-db-001` |
| **Storage Account** | `st<app><env><hash>` (no dashes, 24 char max) | `stcontosoprda1b2c3` |
| **Key Vault** | `kv-<app>-<env>-<region>` | `kv-contoso-prod-eastus` |
| **App Service Plan** | `plan-<app>-<env>-<region>` | `plan-contoso-prod-eastus` |
| **App Service** | `app-<app>-<env>-<region>` | `app-contoso-prod-eastus` |
| **AKS Cluster** | `aks-<app>-<env>-<region>` | `aks-contoso-prod-eastus` |
| **ACR** | `acr<app><env>` (no dashes, 5-50 char) | `acrcontosoprod` |
| **Cosmos DB** | `cosmos-<app>-<env>-<region>` | `cosmos-contoso-prod-eastus` |
| **API Management** | `apim-<app>-<env>-<region>` | `apim-contoso-prod-eastus` |
| **Application Insights** | `appins-<app>-<env>` | `appins-contoso-prod` |
| **Log Analytics Workspace** | `law-<app>-<env>` | `law-contoso-prod` |

**Tags** (mandatory):
```json
{
  "Environment": "prod|staging|dev",
  "Application": "contoso-api",
  "Owner": "platform-team@contoso.com",
  "CostCenter": "12345",
  "CreatedDate": "2024-01-15",
  "ManagedBy": "Terraform" // or "Bicep"
}
```

---

## Common Architectural Mistakes & How to Avoid Them

| Mistake | Why It's Bad | Fix |
|---------|-------------|-----|
| Single-region deployment | Regional outages take down entire app | Use multi-AZ; geo-replicate data |
| Hardcoded secrets in config | Credentials exposed in version control | Use Key Vault + managed identities |
| No monitoring/alerting | Discover issues only when users complain | Instrument all critical paths; alert on SLO violations |
| Overly complex networking | Difficult to troubleshoot, security gaps | Start with simple hub-spoke; scale gradually |
| Choosing AKS for simple app | Kubernetes overhead not justified | Use Container Apps or App Service |
| Not testing failover | RTO/RPO targets are theoretical | Regularly execute DR drills; measure actual recovery time |
| Sync APIs everywhere | Cascading failures, poor scalability | Use event-driven, queues, eventual consistency |
| No IaC (manual resources) | No audit trail, can't reproduce environment | Everything in Bicep/Terraform; version control |
| Undersized compute | Poor performance, user complaints | Monitor resource utilization; right-size |
| Paying for idle resources | Waste budget | Clean up dev/test resources; use automation |

---

## Decision Matrix: Quick Reference

**Reliability**: Multi-region? → AZ-redundant resources → Health checks → Backup/DR plan
**Security**: Private endpoints? → Managed identities? → Encryption at rest/transit? → Key Vault for secrets?
**Cost**: Reserved Instances? → Auto-scaling? → Right-sized resources? → Cleanup old resources?
**Operations**: IaC? → Monitoring? → CI/CD? → Runbooks?
**Performance**: Caching? → CDN? → Regional placement? → Async where possible?

