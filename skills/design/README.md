# Azure Design Skills - Infrastructure & Architecture Patterns

This directory contains three comprehensive skill documents for designing and implementing Azure infrastructure using proven architectural patterns and Infrastructure as Code (IaC) approaches.

## 📚 Skills Overview

### 1. [azure-architecture-patterns/SKILL.md](./azure-architecture-patterns/SKILL.md)
**Well-Architected Framework & Architectural Patterns**

Design resilient, secure, cost-optimized Azure solutions through the Five Pillars and proven patterns.

- **Five Pillars**: Reliability, Security, Cost Optimization, Operational Excellence, Performance Efficiency
- **Compute Decision Tree**: When to use Functions vs Container Apps vs AKS vs App Service
- **6 Core Patterns**:
  - Hub-spoke networking (multi-team enterprise)
  - Landing zones (multi-subscription governance)
  - Microservices on AKS / Container Apps
  - Serverless event-driven architecture
  - CQRS with Cosmos DB + Event Hub
  - API Gateway pattern with APIM
- **Mermaid Diagram Templates**: How to visualize Azure architectures
- **CAF Naming Conventions**: Microsoft Cloud Adoption Framework resource naming
- **Common Mistakes**: What to avoid when designing Azure workloads

**Best for**: Architecture design decisions, creating solution diagrams, choosing compute options, governance planning

---

### 2. [azure-bicep/SKILL.md](./azure-bicep/SKILL.md)
**Azure Bicep — ARM Template DSL**

Write clean, modular Infrastructure as Code using Bicep (ARM Template abstraction).

- **Core Syntax**: params, vars, resources, outputs, decorators (@secure, @description, @allowed)
- **Advanced Features**: Conditionals (if), Loops (for), Modules, Key Vault integration, Resource references
- **Common Resources**: Storage Account, Key Vault, Cosmos DB, AKS, App Service
- **Deployment**: CLI commands, parameter files (.bicepparam), validation
- **Module Registry**: Using public Bicep modules (AVM — Azure Verified Modules)
- **Best Practices**: Decorators, symbolic references vs reference(), managing secrets securely
- **Common Pitfalls**: API versions, circular dependencies, secret handling, RBAC vs access policies

**Best for**: Writing Bicep IaC, deploying Azure resources, creating reusable infrastructure modules

---

### 3. [azure-terraform/SKILL.md](./azure-terraform/SKILL.md)
**Terraform for Azure — AzureRM Provider**

Use Terraform's declarative language to manage Azure infrastructure at scale.

- **Setup & Authentication**: Service Principal, Managed Identity, Azure CLI
- **Core Syntax**: variables, locals, resources, data sources, outputs, for_each/count
- **AzureRM Provider**: Version pinning, features configuration, multi-environment support
- **Common Resources**: Resource Group, Storage Account, Key Vault, Cosmos DB, AKS, App Service
- **Remote State**: Storing state in Azure Storage (with encryption, locking, backup)
- **Modules**: Structure, reuse, registry usage, scoping
- **Multi-Environment**: tfvars patterns (terraform.tfvars, terraform.prod.tfvars)
- **Best Practices**: Naming conventions, semantic versioning, state management
- **Common Pitfalls**: Secret handling, provider versions, dynamic for_each, manual modifications (drift)

**Best for**: Multi-cloud deployments, state management, complex infrastructure orchestration, team collaboration

---

## 🎯 Quick Reference: When to Use Each Skill

### Architecture Design
```
User: "Design an Azure solution for..."
→ Use: azure-architecture-patterns
- Evaluate against 5 pillars
- Choose appropriate pattern (hub-spoke, landing zone, microservices, etc.)
- Create Mermaid diagram
- Document naming convention
```

### Infrastructure Code — Bicep
```
User: "Write Bicep for..."
→ Use: azure-bicep
- Define resources with params, vars, outputs
- Use modules for reusability
- Secure secrets with @secure() and Key Vault
- Deploy via az deployment commands
```

### Infrastructure Code — Terraform
```
User: "Write Terraform for..."
→ Use: azure-terraform
- Authenticate via service principal or managed identity
- Configure AzureRM provider with version pinning
- Use modules for infrastructure components
- Store remote state in Azure Storage
- Deploy with terraform plan/apply
```

---

## 🔑 Key Patterns & Syntax Cheat Sheet

### Bicep
```bicep
# Parameter with validation
@description("Environment name")
@allowed(['dev', 'staging', 'prod'])
param environment string

# Variable (computed)
var storageName = 'st${environment}${uniqueString(resourceGroup().id)}'

# Resource
resource storage 'Microsoft.Storage/storageAccounts@2023-01-01' = {
  name: storageName
  location: location
}

# Conditional resource
resource vmProd 'Microsoft.Compute/virtualMachines@2023-03-01' = if (environment == 'prod') {
  // ...
}

# Loop
resource subnets 'Microsoft.Network/virtualNetworks/subnets@2023-04-01' = [for subnet in subnetConfig: {
  // ...
}]

# Module usage
module storage './modules/storage.bicep' = {
  name: 'storageDeployment'
  params: { /* ... */ }
}

# Output
output storageId string = storage.id
```

### Terraform
```hcl
# Variable declaration
variable "environment" {
  type = string
}

# Local value (computed)
locals {
  resource_name = "${var.environment}-${var.location}"
}

# Provider
provider "azurerm" {
  features {}
}

# Resource
resource "azurerm_storage_account" "main" {
  name                = local.storage_name
  resource_group_name = azurerm_resource_group.main.name
  location            = var.location
}

# Data source (existing resource)
data "azurerm_key_vault" "existing" {
  name                = var.kv_name
  resource_group_name = var.kv_rg
}

# Conditional
resource "azurerm_windows_virtual_machine" "example" {
  count = var.environment == "prod" ? 1 : 0
  // ...
}

# Loop
resource "azurerm_subnet" "main" {
  for_each = toset(var.subnet_names)
  // ...
}

# Module
module "storage" {
  source = "./modules/storage"
  // params
}

# Output
output "storage_id" {
  value = azurerm_storage_account.main.id
}
```

---

## 🚨 Common Mistakes & Solutions

### Architecture
| Mistake | Solution |
|---------|----------|
| Single-region deployment | Use availability zones + geo-replication |
| Synchronous APIs everywhere | Implement event-driven, async patterns, queues |
| Wrong compute choice | Use decision tree: Functions → Container Apps → AKS |
| No monitoring | Instrument all critical paths, set SLO-based alerts |
| Hardcoded secrets | Use Key Vault + managed identities |

### Bicep
| Mistake | Solution |
|---------|----------|
| Storing secrets in outputs | Use `sensitive = true` on parameters, reference Key Vault |
| Wrong API version | Check Microsoft docs for latest stable versions |
| Using reference() unnecessarily | Prefer symbolic references: `resource.id` |
| Circular dependencies | Explicitly add `dependsOn: [resourceId]` |
| Not using RBAC for Key Vault | Set `enableRbacAuthorization: true` |

### Terraform
| Mistake | Solution |
|---------|----------|
| Hardcoded secrets in .tf | Use `sensitive = true` variables + .gitignore |
| State stored locally | Use remote backend: Azure Storage account |
| Not pinning provider version | Use semantic versioning: `~> 3.80.0` |
| Dynamic for_each sizing | Use fixed-size arrays to prevent drift |
| Manual Azure portal edits | Always use Terraform, run `terraform refresh` if manual changes needed |

---

## 📊 Skill Statistics

| Skill | File | Size | Lines | Key Sections |
|-------|------|------|-------|--------------|
| architecture-patterns | SKILL.md | 20 KB | ~600 | 5 pillars, 6 patterns, Mermaid diagrams, CAF naming |
| bicep | SKILL.md | 23 KB | ~893 | Syntax, decorators, modules, Key Vault, 4 resource examples |
| terraform | SKILL.md | 24 KB | ~919 | Setup, provider config, auth, 5 resource examples, remote state |

**Total**: ~67 KB, ~2,400 lines of comprehensive reference documentation

---

## 🔄 How Claude Uses These Skills

1. **Skill Detection**: Identifies keywords in user request
   - "Architecture design" → azure-architecture-patterns
   - "Bicep template" → azure-bicep
   - "Terraform Azure" → azure-terraform

2. **Contextual Reference**: Applies patterns and syntax from relevant skill
   - Cites specific sections and examples
   - Provides correct API versions, decorators, authentication methods
   - Avoids common mistakes documented in each skill

3. **Code Generation**: Generates production-ready code
   - Proper naming conventions (CAF)
   - Security best practices (managed identities, Key Vault)
   - Resource redundancy and compliance
   - Comments explaining architectural decisions

4. **Validation**: Validates against skill guidelines
   - Checks syntax correctness
   - Ensures secrets are secured
   - Verifies naming conventions
   - Confirms appropriate pattern selection

---

## 🔗 References & Resources

- **Microsoft Cloud Adoption Framework (CAF)**: https://learn.microsoft.com/azure/cloud-adoption-framework/
- **Azure Well-Architected Framework**: https://learn.microsoft.com/azure/well-architected/
- **Bicep Documentation**: https://learn.microsoft.com/azure/azure-resource-manager/bicep/
- **Terraform AzureRM Provider**: https://registry.terraform.io/providers/hashicorp/azurerm/latest/docs
- **Azure Verified Modules (AVM)**: https://learn.microsoft.com/en-us/azure/architecture/framework/mission-critical/mission-critical-deployment-testing

---

## 📝 Document Maintenance

Last Updated: March 13, 2024

To keep these skills current:
- Review quarterly for Azure service updates
- Check provider version changelogs (Bicep, Terraform)
- Validate code examples against latest API versions
- Update CAF naming when Microsoft publishes changes
- Add new patterns as they emerge in the field

