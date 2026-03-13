---
name: azure-terraform
description: >
  Write Infrastructure as Code using Terraform for Azure (AzureRM provider).
  Use this skill whenever the user needs to: authenticate to Azure (service principal, managed identity, Azure CLI),
  configure the AzureRM provider with version pinning, declare resources (azurerm_resource_group, storage_account,
  key_vault, cosmosdb_account, kubernetes_cluster, etc), use data sources, local values, output values, remote state
  in Azure Storage, modules, tfvars patterns, apply naming conventions, or manage multi-environment deployments.
  Also use for: "Terraform Azure", "terraform plan/apply", "AzureRM provider", "Terraform modules", "Terraform state",
  ".tf files", "main.tf", "variables.tf", "terraform.tfvars", "azurerm_", or any request to generate or explain
  Terraform IaC for Azure infrastructure.
---

# Terraform for Azure (AzureRM Provider)

**Terraform** is a multi-cloud IaC tool. The **AzureRM** provider manages Azure resources. Terraform uses
**HCL** (HashiCorp Configuration Language) with declarative syntax: define desired state, Terraform ensures
current state matches.

## Installation & Setup

```bash
# Install Terraform (macOS with Homebrew)
brew install terraform

# Or download from https://www.terraform.io/downloads.html
# Verify installation
terraform version

# Initialize working directory (downloads provider plugins)
terraform init
```

**VS Code Extension**: Hashicorp Terraform (for syntax highlighting, validation, snippets)

---

## Project Structure

```
my-azure-infra/
├── main.tf                 # Provider config, main resources
├── variables.tf            # Input variables (param declarations)
├── outputs.tf              # Output values
├── locals.tf               # Local values (computed variables)
├── terraform.tfvars        # Variable values (env-specific)
├── terraform.prod.tfvars   # Prod variable values
├── terraform.dev.tfvars    # Dev variable values
├── modules/
│   ├── storage/
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   └── outputs.tf
│   ├── network/
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   └── outputs.tf
│   └── aks/
│       ├── main.tf
│       ├── variables.tf
│       └── outputs.tf
├── .terraform/             # Provider cache (gitignore)
├── .gitignore              # Exclude state files, .tfvars with secrets
└── README.md               # Documentation
```

---

## Core Concepts

### Provider Configuration

```hcl
terraform {
  required_version = ">= 1.5.0"
  
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.80.0"  # Semantic versioning: ~> allows patch updates (3.80.x)
    }
  }

  # Remote state in Azure Storage (optional, but recommended for teams)
  backend "azurerm" {
    resource_group_name  = "rg-terraform-state"
    storage_account_name = "stterraformstate"
    container_name       = "tfstate"
    key                  = "prod.tfstate"
  }
}

provider "azurerm" {
  features {
    key_vault {
      purge_soft_delete_on_destroy = true  # ← careful with this
    }
    virtual_machine {
      delete_os_disk_on_delete            = true
      graceful_shutdown                   = false
    }
  }

  # Authentication method 1: Environment variables (service principal)
  # Set: ARM_CLIENT_ID, ARM_CLIENT_SECRET, ARM_SUBSCRIPTION_ID, ARM_TENANT_ID
  
  # Authentication method 2: Managed identity (Azure Container Instances, VMs)
  # Automatically uses the VM's system-assigned managed identity
  
  # Authentication method 3: Azure CLI (if az login is set)
  skip_provider_registration = false
}
```

### Authentication Methods (Priority Order)

**Option 1: Managed Identity** (preferred in Azure — no secrets to manage):
```bash
# When running from Azure VM, App Service, Container Instance, etc.
# Terraform automatically uses the resource's managed identity
# No additional config needed beyond `provider "azurerm" {}`
```

**Option 2: Service Principal via Environment Variables** (for CI/CD):
```bash
export ARM_CLIENT_ID="<app-id>"
export ARM_CLIENT_SECRET="<password>"
export ARM_SUBSCRIPTION_ID="<subscription-id>"
export ARM_TENANT_ID="<directory-id>"

# Terraform will automatically pick these up
```

**Option 3: Azure CLI** (easiest for local development):
```bash
az login
# Terraform uses the authenticated CLI session automatically
```

**Service Principal Creation** (for CI/CD pipelines):
```bash
# Create service principal
az ad sp create-for-rbac \
  --name "terraform-sp" \
  --role "Contributor" \
  --scopes "/subscriptions/<subscription-id>"

# Output:
# {
#   "appId": "...",
#   "password": "...",
#   "tenant": "..."
# }

# Add to CI/CD secrets as ARM_CLIENT_ID, ARM_CLIENT_SECRET, ARM_SUBSCRIPTION_ID, ARM_TENANT_ID
```

---

## Core Syntax

### 1. Variables (Inputs)

```hcl
# Simple variable
variable "location" {
  type = string
}

# With default
variable "environment" {
  type    = string
  default = "dev"
}

# With description and type validation
variable "vm_size" {
  description = "The size of the virtual machine (e.g., Standard_D2s_v3)"
  type        = string
  default     = "Standard_D2s_v3"

  validation {
    condition     = can(regex("^Standard_", var.vm_size))
    error_message = "VM size must start with 'Standard_'."
  }
}

# Complex types
variable "tags" {
  description = "Common tags for all resources"
  type = object({
    environment  = string
    owner        = string
    cost_center  = string
    created_date = string
  })

  default = {
    environment  = "dev"
    owner        = "platform-team"
    cost_center  = "12345"
    created_date = "2024-01-15"
  }
}

# List of objects
variable "subnets" {
  description = "Subnet configurations"
  type = list(object({
    name          = string
    address_space = string
  }))

  default = [
    { name = "web", address_space = "10.0.1.0/24" }
    { name = "db", address_space = "10.0.2.0/24" }
  ]
}

# Sensitive variable (value hidden from logs/plan output)
variable "sql_admin_password" {
  description = "SQL Server admin password"
  type        = string
  sensitive   = true
  # Don't provide a default for secrets!
}
```

### 2. Local Values (Computed Variables)

```hcl
locals {
  # Simple computation
  unique_suffix = substr(md5(azurerm_resource_group.main.id), 0, 4)

  # String interpolation
  storage_account_name = "st${var.environment}${local.unique_suffix}"
  
  # Conditional
  vm_size = var.environment == "prod" ? "Standard_D4s_v3" : "Standard_D2s_v3"

  # Common naming prefix
  resource_prefix = "${var.environment}-${var.location}-${local.unique_suffix}"

  # Commonly used tags (merged with user-provided tags)
  common_tags = merge(var.tags, {
    ManagedBy = "Terraform"
    CreatedAt = timestamp()  # Current time
  })
}
```

### 3. Resources

```hcl
# Azure Resource Group
resource "azurerm_resource_group" "main" {
  name     = "rg-${var.environment}-${var.location}"
  location = var.location

  tags = local.common_tags
}

# Azure Storage Account
resource "azurerm_storage_account" "main" {
  name                     = local.storage_account_name
  resource_group_name      = azurerm_resource_group.main.name
  location                 = azurerm_resource_group.main.location
  account_tier             = "Standard"
  account_replication_type = "LRS"  # or GRS, GZRS for redundancy
  https_traffic_only_enabled = true
  min_tls_version          = "TLS1_2"

  tags = local.common_tags
}

# Data source: fetch existing resource (not managed by Terraform)
data "azurerm_key_vault" "existing" {
  name                = var.key_vault_name
  resource_group_name = var.key_vault_rg
}

# Reference to another resource (symbolic reference)
resource "azurerm_storage_account_blob_container" "data" {
  name                  = "data"
  storage_account_id    = azurerm_storage_account.main.id
  container_access_type = "private"
}

# Conditional resource (only create if condition is true)
resource "azurerm_windows_virtual_machine" "prod_only" {
  count = var.environment == "prod" ? 1 : 0

  name                = "vm-${var.environment}"
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  vm_size             = local.vm_size

  # ... rest of config
}

# Loop: create multiple instances
resource "azurerm_subnet" "main" {
  for_each = toset(var.subnet_names)

  name                 = "snet-${each.value}"
  resource_group_name  = azurerm_resource_group.main.name
  virtual_network_name = azurerm_virtual_network.main.name
  address_prefixes     = ["10.0.${index(var.subnet_names, each.value)}.0/24"]
}

# Hybrid: conditional loop
resource "azurerm_virtual_machine" "cluster" {
  for_each = var.environment == "prod" ? toset(var.node_names) : toset([])

  name                = "vm-${each.value}"
  resource_group_name = azurerm_resource_group.main.name
  # ...
}

# Depends-on explicit ordering
resource "azurerm_kubernetes_cluster" "main" {
  depends_on = [
    azurerm_role_assignment.aks_network_contributor
  ]
  # ...
}
```

### 4. Outputs

```hcl
# Simple output
output "resource_group_id" {
  value       = azurerm_resource_group.main.id
  description = "The ID of the created resource group"
}

# Sensitive output (hidden from logs, but still retrievable via terraform output)
output "storage_account_key" {
  value       = azurerm_storage_account.main.primary_access_key
  sensitive   = true
  description = "Primary storage account key"
}

# Computed output
output "storage_connection_string" {
  value = "DefaultEndpointProtocol=https;AccountName=${azurerm_storage_account.main.name};AccountKey=${azurerm_storage_account.main.primary_access_key};EndpointSuffix=core.windows.net"
  sensitive = true
}

# Map output (for iterating)
output "subnet_ids" {
  value = {
    for name, subnet in azurerm_subnet.main : name => subnet.id
  }
}

# List output
output "instance_private_ips" {
  value = [for vm in azurerm_windows_virtual_machine.cluster : vm.private_ip_address]
}
```

---

## Core Resources (AzureRM Provider)

### Resource Group

```hcl
resource "azurerm_resource_group" "main" {
  name     = "rg-${var.app_name}-${var.environment}-${var.location}"
  location = var.location

  tags = local.common_tags
}
```

### Storage Account

```hcl
resource "azurerm_storage_account" "main" {
  name                     = "st${var.environment}${local.unique_suffix}"
  resource_group_name      = azurerm_resource_group.main.name
  location                 = azurerm_resource_group.main.location
  account_tier             = "Standard"
  account_replication_type = "GRS"  # Geo-redundant

  https_traffic_only_enabled = true
  min_tls_version            = "TLS1_2"
  shared_access_key_enabled  = false  # Prefer managed identities

  network_rules {
    default_action             = "Deny"
    virtual_network_subnet_ids = var.allowed_subnet_ids
    bypass                     = ["AzureServices"]
  }

  tags = local.common_tags
}

# Blob container
resource "azurerm_storage_account_blob_container" "data" {
  name                  = "data"
  storage_account_id    = azurerm_storage_account.main.id
  container_access_type = "private"
}

# Blob container with data deletion
resource "azurerm_storage_account_blob_container" "logs" {
  name                  = "logs"
  storage_account_id    = azurerm_storage_account.main.id
  container_access_type = "private"
}

resource "azurerm_storage_management_policy" "retention" {
  storage_account_id = azurerm_storage_account.main.id

  rule {
    name    = "delete-old-logs"
    enabled = true

    filters {
      blob_index_match {
        name      = "tier"
        operation = "=="
        value     = "logs"
      }
    }

    actions {
      base_blob {
        delete_after_days_since_modification_greater_than = 90
      }
    }
  }
}
```

### Key Vault

```hcl
resource "azurerm_key_vault" "main" {
  name                = "kv-${var.environment}-${var.location}"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  tenant_id           = data.azurerm_client_config.current.tenant_id

  sku_name = "standard"

  purge_protection_enabled = var.environment == "prod" ? true : false
  soft_delete_retention_days = 90

  # Enable RBAC (preferred over access policies)
  enable_rbac_authorization = true

  # Network rules (restrict access)
  network_acls {
    default_action             = "Deny"
    virtual_network_subnet_ids = var.allowed_subnet_ids
    bypass                     = ["AzureServices"]
  }

  tags = local.common_tags
}

# RBAC role assignment (grant app access to secrets)
resource "azurerm_role_assignment" "app_kv_access" {
  scope              = azurerm_key_vault.main.id
  role_definition_name = "Key Vault Secrets User"  # or use role_definition_id
  principal_id       = azurerm_user_assigned_identity.app.principal_id
}

# Store a secret
resource "azurerm_key_vault_secret" "db_password" {
  name         = "db-password"
  value        = random_password.db_password.result
  key_vault_id = azurerm_key_vault.main.id

  tags = local.common_tags
}

# Generate random password
resource "random_password" "db_password" {
  length  = 32
  special = true
}
```

### Cosmos DB

```hcl
resource "azurerm_cosmosdb_account" "main" {
  name                = "cosmos-${var.environment}-${var.location}"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  offer_type          = "Standard"

  consistency_policy {
    consistency_level = var.environment == "prod" ? "Session" : "Eventual"
  }

  # Single region (dev), multi-region (prod)
  dynamic "geo_location" {
    for_each = var.environment == "prod" ? [
      "eastus",
      "westus"
    ] : ["eastus"]

    content {
      prefix            = "region-${geo_location.key}"
      location          = geo_location.value
      failover_priority = geo_location.key
    }
  }

  backup {
    type                = "Continuous"
    retention_in_hours  = 24
  }

  tags = local.common_tags
}

# Cosmos DB Database
resource "azurerm_cosmosdb_sql_database" "main" {
  name                = "appdb"
  resource_group_name = azurerm_resource_group.main.name
  account_name        = azurerm_cosmosdb_account.main.name
  throughput          = 400  # RU/s
}

# Cosmos DB Container
resource "azurerm_cosmosdb_sql_container" "users" {
  name                = "users"
  resource_group_name = azurerm_resource_group.main.name
  account_name        = azurerm_cosmosdb_account.main.name
  database_name       = azurerm_cosmosdb_sql_database.main.name
  partition_key_path  = "/id"
  throughput          = 400

  unique_key {
    paths = ["/email"]
  }

  indexing_policy {
    indexing_mode = "consistent"

    included_path {
      path = "/*"
    }
  }
}
```

### AKS (Azure Kubernetes Service)

```hcl
resource "azurerm_kubernetes_cluster" "main" {
  name                = "aks-${var.environment}-${var.location}"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  dns_prefix          = "aks${var.environment}${local.unique_suffix}"

  kubernetes_version = var.kubernetes_version

  default_node_pool {
    name           = "system"
    node_count     = var.environment == "prod" ? 3 : 1
    vm_size        = var.environment == "prod" ? "Standard_D4s_v3" : "Standard_D2s_v3"
    os_sku         = "Ubuntu"
    
    # Enable auto-scaling
    enable_auto_scaling = true
    min_count          = 1
    max_count          = 5
    
    # Availability zones for HA
    zones = var.environment == "prod" ? [1, 2, 3] : []
    
    vnet_subnet_id = azurerm_subnet.aks.id
  }

  # Enable managed identity (preferred)
  identity {
    type = "SystemAssigned"
  }

  # Enable RBAC (required)
  role_based_access_control_enabled = true

  # Network config
  network_profile {
    network_plugin      = "azure"
    network_policy      = "azure"  # Calico alternative
    service_cidr        = "10.0.0.0/16"
    dns_service_ip      = "10.0.0.10"
    load_balancer_sku   = "standard"
  }

  # Add-ons
  oms_agent {
    enabled                    = true
    log_analytics_workspace_id = azurerm_log_analytics_workspace.main.id
  }

  key_vault_secrets_provider {
    secret_rotation_enabled  = true
    secret_rotation_interval = "2m"
  }

  tags = local.common_tags

  depends_on = [
    azurerm_role_assignment.aks_network_contributor
  ]
}

# Kubernetes provider (for managing resources inside AKS)
provider "kubernetes" {
  host                   = azurerm_kubernetes_cluster.main.kube_config[0].host
  client_certificate     = base64decode(azurerm_kubernetes_cluster.main.kube_config[0].client_certificate)
  client_key             = base64decode(azurerm_kubernetes_cluster.main.kube_config[0].client_key)
  cluster_ca_certificate = base64decode(azurerm_kubernetes_cluster.main.kube_config[0].cluster_ca_certificate)
}

# Grant AKS managed identity access to virtual network
resource "azurerm_role_assignment" "aks_network_contributor" {
  scope              = azurerm_virtual_network.main.id
  role_definition_name = "Network Contributor"
  principal_id       = azurerm_kubernetes_cluster.main.identity[0].principal_id
}
```

### App Service

```hcl
resource "azurerm_app_service_plan" "main" {
  name                = "plan-${var.environment}-${var.location}"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name

  sku {
    tier = var.environment == "prod" ? "Premium" : "Basic"
    size = var.environment == "prod" ? "P1v2" : "B1"
  }

  tags = local.common_tags
}

resource "azurerm_app_service" "main" {
  name                = "app-${var.environment}-${var.location}"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  app_service_plan_id = azurerm_app_service_plan.main.id

  https_only = true

  site_config {
    min_tls_version = "1.2"
    http2_enabled   = true
  }

  # Use managed identity instead of connection strings
  identity {
    type = "SystemAssigned"
  }

  app_settings = {
    WEBSITE_RUN_FROM_PACKAGE = "1"
    KEYVAULT_URL             = azurerm_key_vault.main.vault_uri
  }

  tags = local.common_tags
}

# Grant App Service access to Key Vault
resource "azurerm_role_assignment" "app_kv_access" {
  scope              = azurerm_key_vault.main.id
  role_definition_name = "Key Vault Secrets User"
  principal_id       = azurerm_app_service.main.identity[0].principal_id
}
```

---

## Remote State in Azure Storage

State file contains sensitive info. Store it remotely with encryption and backup.

### Initialize Remote State Backend

```bash
# Create storage account for state (one-time setup)
az group create --name rg-terraform-state --location eastus

az storage account create \
  --resource-group rg-terraform-state \
  --name stterraformstate \
  --sku Standard_LRS \
  --encryption-services blob

az storage container create \
  --account-name stterraformstate \
  --name tfstate
```

### Configure Backend in Terraform

```hcl
# main.tf
terraform {
  backend "azurerm" {
    resource_group_name  = "rg-terraform-state"
    storage_account_name = "stterraformstate"
    container_name       = "tfstate"
    key                  = "prod.tfstate"
    # Optional:
    # access_key = "..."  # or use environment variable ARM_ACCESS_KEY
  }
}

# Initialize backend
terraform init
# → prompts for storage account access key (or reads from ARM_ACCESS_KEY env var)
```

State file is now stored in Azure Storage (encrypted, versioned, backed up).

---

## Variables & tfvars Patterns

### variables.tf (Declarations)

```hcl
variable "environment" {
  description = "Environment (dev, staging, prod)"
  type        = string
}

variable "location" {
  description = "Azure region"
  type        = string
  default     = "eastus"
}

variable "tags" {
  description = "Common tags"
  type        = map(string)
  default = {
    ManagedBy = "Terraform"
  }
}
```

### terraform.tfvars (Dev Values)

```hcl
environment = "dev"
location    = "eastus"

tags = {
  ManagedBy   = "Terraform"
  Environment = "dev"
  Owner       = "dev-team"
}
```

### terraform.prod.tfvars (Prod Values)

```hcl
environment = "prod"
location    = "eastus"

tags = {
  ManagedBy   = "Terraform"
  Environment = "prod"
  Owner       = "platform-team"
  CostCenter  = "12345"
}
```

### Deployment with Specific tfvars

```bash
# Dev deployment
terraform plan -var-file="terraform.tfvars"
terraform apply -var-file="terraform.tfvars"

# Prod deployment
terraform plan -var-file="terraform.prod.tfvars"
terraform apply -var-file="terraform.prod.tfvars"

# Override single variable
terraform apply -var="environment=staging"
```

---

## Modules

### Module Structure

**modules/storage/main.tf**:
```hcl
terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.80.0"
    }
  }
}

provider "azurerm" {
  features {}
}

variable "storage_account_name" {
  type = string
}

variable "resource_group_name" {
  type = string
}

variable "location" {
  type = string
}

resource "azurerm_storage_account" "main" {
  name                     = var.storage_account_name
  resource_group_name      = var.resource_group_name
  location                 = var.location
  account_tier             = "Standard"
  account_replication_type = "LRS"
  https_traffic_only_enabled = true
}

output "id" {
  value = azurerm_storage_account.main.id
}

output "primary_endpoint" {
  value = azurerm_storage_account.main.primary_blob_endpoint
}
```

**Main terraform files call modules**:
```hcl
module "storage" {
  source = "./modules/storage"

  storage_account_name = "st${var.environment}${local.unique_suffix}"
  resource_group_name  = azurerm_resource_group.main.name
  location             = var.location
}

output "storage_id" {
  value = module.storage.id
}
```

---

## Common Commands

```bash
# Initialize working directory (downloads providers)
terraform init

# Format HCL code
terraform fmt --recursive

# Validate syntax
terraform validate

# Preview changes (DRY RUN)
terraform plan -out=tfplan

# Apply changes
terraform apply tfplan

# Show current state
terraform show
terraform state list

# Refresh state (sync with actual Azure resources)
terraform refresh

# Destroy all resources
terraform destroy

# Target specific resource
terraform apply -target=azurerm_resource_group.main

# Get provider documentation
terraform providers
```

---

## Common Pitfalls & How to Fix Them

| Mistake | Why It's Bad | Fix |
|---------|-------------|-----|
| Hardcoded secrets in `.tf` files | Exposed in version control | Use `sensitive = true` variables + .gitignore tfvars |
| Not .gitignore terraform state | State contains secrets + credentials | Add `.terraform/`, `*.tfstate*`, `*.tfvars` to .gitignore |
| Wrong provider version | API incompatibilities, missing features | Pin provider version: `version = "~> 3.80.0"` |
| Using `for_each` with dynamic count | Count unpredictable, causes drift | Use `for_each` with fixed keys (strings, not indices) |
| No remote state backend | Risk of manual modifications, no locking | Store state in Azure Storage, enable locking |
| Not running terraform validate | Errors discovered at apply time | Run `terraform validate` + `terraform plan` first |
| Modifying resources manually in portal | Terraform doesn't know about changes = drift | Always modify via Terraform; use `terraform refresh` if needed |
| Referencing outputs of destroyed modules | Breaking changes | Use `depends_on` + order modules explicitly |
| No naming convention | Hard to identify resources | Use local values + CAF naming: `"${var.environment}-${var.location}-${local.unique_suffix}"` |
| Storing sensitive outputs without marker | Secrets appear in logs/CI/CD | Use `sensitive = true` on all secret outputs |

