---
name: azure-bicep
description: >
  Write Infrastructure as Code using Azure Bicep (ARM Template abstraction layer).
  Use this skill whenever the user needs to: define Azure resources declaratively (param, var, resource, output),
  organize code with modules, use conditionals (if) and loops (for), work with existing resources,
  reference secrets from Key Vault, manage deployment scopes (subscription vs resource group),
  use symbolic references and the reference() function, apply decorators (@secure, @description),
  target deployment scopes with targetScope, build and deploy Bicep files, or use the bicep module registry.
  Also apply when users mention: "Bicep template", "ARM template" (prefer Bicep), "IaC for Azure",
  "Bicep parameter file", "bicep build", "bicep deploy", "Bicep module", "bicep linting", ".bicep file",
  or any request to generate Azure infrastructure code.
---

# Azure Bicep — Infrastructure as Code

**Bicep** is a domain-specific language (DSL) that compiles to ARM Templates (JSON). It provides cleaner syntax,
better tooling, and modularity compared to writing ARM JSON directly.

## Installation & Setup

```bash
# Install Bicep CLI (Windows, macOS, Linux)
az bicep install

# Update to latest
az bicep upgrade

# Verify installation
az bicep version
```

**VS Code Extensions** (highly recommended):
- **Bicep** (Microsoft): IntelliSense, validation, snippets
- **ARM Tools**: Template validation, visualization

---

## Core Concepts

### File Structure & Scopes

Every `.bicep` file declares its **target scope** (where it deploys):

```bicep
targetScope = 'resourceGroup'  // default; most resources go here
// OR
targetScope = 'subscription'   // for subscription-level resources (policies, RGs)
// OR
targetScope = 'managementGroup'  // for management group policies
// OR
targetScope = 'tenant'         // for tenant-level (AAD) resources
```

---

## Core Syntax

### 1. Parameters (Inputs)

```bicep
// Simple parameter
param location string

// With default
param environment string = 'dev'

// With metadata (appears in portal)
@description('The environment name (dev, staging, prod)')
param environment string

// With allowed values
@allowed([
  'dev'
  'staging'
  'prod'
])
param environment string

// Secure parameter (password, API key) — values NOT logged/shown
@secure()
param sqlAdminPassword string

// With constraint (min/max length)
@minLength(5)
@maxLength(24)
param storageAccountName string

// Array parameter
param tags array = [
  'tier: web'
  'owner: platform-team'
]

// Object parameter (for complex configs)
param vmConfig object = {
  size: 'Standard_D2s_v3'
  imageId: '/subscriptions/.../Microsoft.Compute/images/myImage'
  osDisk: {
    diskSizeGB: 128
  }
}
```

### 2. Variables (Computed Values)

```bicep
// Simple variable
var uniqueSuffix = substring(uniqueString(resourceGroup().id), 0, 4)

// String interpolation
var storageAccountName = 'st${environment}${uniqueSuffix}'

// Conditional variable (ternary)
var vmSize = (environment == 'prod') ? 'Standard_D4s_v3' : 'Standard_D2s_v3'

// Array variable
var subnets = [
  {
    name: 'web'
    addressPrefix: '10.0.1.0/24'
  }
  {
    name: 'db'
    addressPrefix: '10.0.2.0/24'
  }
]

// Computed from parameters
var resourceNamePrefix = '${environment}-${location}-${uniqueSuffix}'
```

### 3. Resources

```bicep
// Basic resource declaration
resource storageAccount 'Microsoft.Storage/storageAccounts@2023-01-01' = {
  name: storageAccountName
  location: location
  kind: 'StorageV2'
  sku: {
    name: 'Standard_LRS'
  }
  properties: {
    accessTier: 'Hot'
    minimumTlsVersion: 'TLS1_2'
  }
  tags: {
    Environment: environment
  }
}

// Reference another resource (symbolic reference — preferred)
resource vnet 'Microsoft.Network/virtualNetworks@2023-04-01' = {
  name: 'vnet-app-${location}'
  location: location
  properties: {
    addressSpace: {
      addressPrefixes: [
        '10.0.0.0/16'
      ]
    }
    subnets: [
      {
        name: 'default'
        properties: {
          addressPrefix: '10.0.1.0/24'
          networkSecurityGroup: {
            id: nsg.id  // ← symbolic reference to another resource
          }
        }
      }
    ]
  }
}

// Reference existing resource (not managed by this template)
resource existingKeyVault 'Microsoft.KeyVault/vaults@2023-02-01' = {
  name: keyVaultName
  location: location  // Still needs location for metadata
}

// Conditional resource — only created if condition is true
resource vmProd 'Microsoft.Compute/virtualMachines@2023-03-01' = if (environment == 'prod') {
  name: 'vm-${environment}'
  location: location
  properties: {
    hardwareProfile: {
      vmSize: 'Standard_D4s_v3'
    }
    // ... rest of config
  }
}

// Loop (create multiple copies)
resource subnets 'Microsoft.Network/virtualNetworks/subnets@2023-04-01' = [for subnet in subnetConfig: {
  parent: vnet
  name: subnet.name
  properties: {
    addressPrefix: subnet.addressPrefix
  }
}]

// Hybrid: conditional loop
resource storageContainers 'Microsoft.Storage/storageAccounts/blobServices/containers@2023-01-01' = [for (container, i) in containers: if (environment == 'prod') {
  parent: storageAccountBlobService
  name: container.name
  properties: {
    publicAccess: container.isPublic ? 'Blob' : 'None'
  }
}]
```

### 4. Outputs

```bicep
// Basic output
output storageAccountId string = storageAccount.id

// Computed output
output storageAccountConnectionString string = 'DefaultEndpointProtocol=https;AccountName=${storageAccount.name};AccountKey=${listKeys(storageAccount.id, storageAccount.apiVersion).keys[0].value};EndpointSuffix=core.windows.net'

// Object output
output deploymentInfo object = {
  storageAccountId: storageAccount.id
  storageAccountName: storageAccount.name
  location: location
}

// Array output
output subnetIds array = [for (i, subnet) in subnets: subnet.id]
```

---

## Advanced Features

### Decorators

Decorators provide metadata and validation:

```bicep
// @description — documentation
@description('The name of the storage account')
param storageAccountName string

// @minLength / @maxLength — validate string length
@minLength(3)
@maxLength(24)
param storageName string

// @minValue / @maxValue — validate numeric range
@minValue(1)
@maxValue(4)
param instanceCount int

// @allowed — restrict to specific values
@allowed([
  'dev'
  'staging'
  'prod'
])
param environment string

// @secure() — mark sensitive input (passwords, API keys)
@secure()
param sqlPassword string

// @export — export for module reuse
@export()
param commonTags object

// Custom metadata (portal display)
@metadata({
  description: 'The location for all resources'
  example: 'eastus'
})
param location string = 'eastus'
```

### Reference Function vs Symbolic References

**Symbolic Reference** (preferred — simpler, strongly typed):
```bicep
// Get ID of a resource defined in same template
var storageId = storageAccount.id
var storageUrl = storageAccount.properties.primaryEndpoints.blob

// This works because Bicep knows about storageAccount's structure
```

**reference() Function** (for metadata, runtime properties, or existing resources):
```bicep
// Get runtime properties of an existing resource
var existingVmProps = reference(vmId, '2023-03-01')

// Get connection string (requires list* functions)
var connStr = 'DefaultEndpointProtocol=https;AccountName=${storageAccount.name};AccountKey=${listKeys(storageAccount.id, '2023-01-01').keys[0].value};EndpointSuffix=core.windows.net'
```

**When to use reference()**:
- Fetching data from an existing resource (not defined in template)
- Getting list* outputs (keys, secrets, connection strings)
- Runtime-evaluated properties

---

### Key Vault Integration

**Pattern 1: Get Secret at Deployment Time** (preferred for sensitive values):
```bicep
param keyVaultResourceGroup string
param keyVaultName string

resource kv 'Microsoft.KeyVault/vaults@2023-02-01' = {
  scope: resourceGroup(keyVaultResourceGroup)  // ← reference resource in different RG
  name: keyVaultName
}

var sqlPassword = kv.listSecrets().value[0].value  // DANGEROUS — exposes in output
```

**Pattern 2: Use keyVaultReference (Better)** — reference in ARM template itself:
```bicep
// In parameter file (parameters.json or bicepparam)
{
  "$schema": "https://schema.management.azure.com/schemas/2019-04-01/deploymentParameters.json#",
  "contentVersion": "1.0.0.0",
  "parameters": {
    "sqlPassword": {
      "reference": {
        "keyVault": {
          "id": "/subscriptions/<sub>/resourceGroups/<rg>/providers/Microsoft.KeyVault/vaults/<vaultName>"
        },
        "secretName": "sqlPassword"
      }
    }
  }
}
```

Then in Bicep:
```bicep
param sqlPassword string
// Password is injected securely from Key Vault at deployment time
```

**Pattern 3: Managed Identity + Access Policy** (cleanest):
```bicep
// 1. Create managed identity
resource appIdentity 'Microsoft.ManagedIdentity/userAssignedIdentities@2023-01-31' = {
  name: 'mi-app-${environment}'
  location: location
}

// 2. Grant identity access to Key Vault
resource kvAccessPolicy 'Microsoft.KeyVault/vaults/accessPolicies@2023-02-01' = {
  parent: kv
  name: 'add'
  properties: {
    accessPolicies: [
      {
        tenantId: subscription().tenantId
        objectId: appIdentity.properties.principalId
        permissions: {
          secrets: ['get', 'list']
        }
      }
    ]
  }
}

// 3. App uses managed identity to fetch secrets at runtime
```

---

### Modules

**Module Definition** (`storage.bicep`):
```bicep
param location string
param environment string
param storageName string

@minLength(0)
@maxLength(100)
param containers array = []

param tags object = {}

resource storageAccount 'Microsoft.Storage/storageAccounts@2023-01-01' = {
  name: storageName
  location: location
  kind: 'StorageV2'
  sku: {
    name: 'Standard_LRS'
  }
  properties: {
    minimumTlsVersion: 'TLS1_2'
  }
  tags: tags
}

// Create containers
resource blobService 'Microsoft.Storage/storageAccounts/blobServices@2023-01-01' = {
  parent: storageAccount
  name: 'default'
}

resource storageContainers 'Microsoft.Storage/storageAccounts/blobServices/containers@2023-01-01' = [for container in containers: {
  parent: blobService
  name: container
  properties: {
    publicAccess: 'None'
  }
}]

// Export outputs
output id string = storageAccount.id
output name string = storageAccount.name
output primaryEndpoint string = storageAccount.properties.primaryEndpoints.blob
```

**Module Usage** (`main.bicep`):
```bicep
targetScope = 'resourceGroup'

param location string = 'eastus'
param environment string

// Call module
module storageModule './modules/storage.bicep' = {
  name: 'storageDeployment'
  params: {
    location: location
    environment: environment
    storageName: 'st${environment}${uniqueString(resourceGroup().id)}'
    containers: [
      'data'
      'logs'
      'exports'
    ]
    tags: {
      Environment: environment
      ManagedBy: 'Bicep'
    }
  }
}

// Use module output
output storageId string = storageModule.outputs.id
output storageName string = storageModule.outputs.name
```

**Bicep Module Registry** (public, from Microsoft):
```bicep
module appServiceModule 'br/public:avm/res/web/site:0.5.0' = {
  name: 'appServiceDeployment'
  params: {
    name: 'app-${environment}-${location}'
    location: location
    serverFarmResourceId: appServicePlan.id
    appSettings: [
      {
        name: 'WEBSITE_RUN_FROM_PACKAGE'
        value: '1'
      }
    ]
  }
}
```

**Module Scoping** (call module at different scope):
```bicep
// Main template at resource group scope
targetScope = 'resourceGroup'

// But create a resource group via module (subscription scope)
module rgModule './modules/resourcegroup.bicep' = {
  scope: subscription()  // ← override scope for this module
  name: 'rg-deployment'
  params: {
    name: 'rg-app-${environment}'
    location: location
  }
}
```

---

### Conditional & Loop Patterns

**Conditional Resource**:
```bicep
param deployDatabase bool = false

resource sqlDatabase 'Microsoft.Sql/servers/databases@2021-11-01' = if (deployDatabase) {
  parent: sqlServer
  name: 'appdb'
  location: location
  sku: {
    name: 'Standard'
    tier: 'Standard'
  }
}

// Conditional output
output databaseId string = deployDatabase ? sqlDatabase.id : ''
```

**Loop with Index**:
```bicep
param subnetCount int = 3

resource subnets 'Microsoft.Network/virtualNetworks/subnets@2023-04-01' = [for i in range(0, subnetCount): {
  parent: vnet
  name: 'subnet-${i}'
  properties: {
    addressPrefix: '10.0.${i}.0/24'
  }
}]
```

**Loop Over Array**:
```bicep
param subnetConfigs array = [
  { name: 'web', cidr: '10.0.1.0/24' }
  { name: 'db', cidr: '10.0.2.0/24' }
  { name: 'cache', cidr: '10.0.3.0/24' }
]

resource subnets 'Microsoft.Network/virtualNetworks/subnets@2023-04-01' = [for subnet in subnetConfigs: {
  parent: vnet
  name: 'snet-${subnet.name}'
  properties: {
    addressPrefix: subnet.cidr
  }
}]
```

**Conditional + Loop**:
```bicep
resource vmScaleSet 'Microsoft.Compute/virtualMachineScaleSets@2023-03-01' = if (environment == 'prod') {
  name: 'vmss-app'
  // ...
}

resource vmInstances 'Microsoft.Compute/virtualMachines@2023-03-01' = [for i in range(0, deployDatabase ? 2 : 0): {
  name: 'vm-db-${i}'
  // ... only create DB VMs if deployDatabase is true
}]
```

---

## Deployment

### CLI Commands

```bash
# Validate syntax
az bicep build --file main.bicep

# Validate against Azure (check API versions, permissions)
az deployment group validate \
  --resource-group rg-app-prod \
  --template-file main.bicep \
  --parameters @parameters.prod.json

# Deploy to resource group
az deployment group create \
  --resource-group rg-app-prod \
  --template-file main.bicep \
  --parameters @parameters.prod.json \
  --no-wait  # async deployment

# Deploy to subscription (for resource groups, policies)
az deployment sub create \
  --location eastus \
  --template-file main.bicep \
  --parameters location=eastus

# Deployment status
az deployment group show \
  --resource-group rg-app-prod \
  --name mainDeployment
```

### Parameter Files

**Bicep Parameter File** (`.bicepparam` — modern approach):
```bicepparam
using './main.bicep'

param location = 'eastus'
param environment = 'prod'
param vmSize = 'Standard_D4s_v3'
param containers = [
  'data'
  'logs'
  'exports'
]
param tags = {
  Environment: 'prod'
  Owner: 'platform-team'
  CostCenter: '12345'
}
```

**JSON Parameter File** (`.parameters.json` — legacy):
```json
{
  "$schema": "https://schema.management.azure.com/schemas/2019-04-01/deploymentParameters.json#",
  "contentVersion": "1.0.0.0",
  "parameters": {
    "location": {
      "value": "eastus"
    },
    "environment": {
      "value": "prod"
    },
    "vmSize": {
      "value": "Standard_D4s_v3"
    },
    "sqlPassword": {
      "reference": {
        "keyVault": {
          "id": "/subscriptions/12345/resourceGroups/rg-shared/providers/Microsoft.KeyVault/vaults/kv-app-prod-eastus"
        },
        "secretName": "sqlPassword"
      }
    }
  }
}
```

Deployment:
```bash
az deployment group create \
  --resource-group rg-app-prod \
  --template-file main.bicep \
  --parameters main.bicepparam
```

---

## Common Resource Examples

### Storage Account (with HTTPS only, versioning, soft delete)

```bicep
param storageAccountName string
param location string

resource storageAccount 'Microsoft.Storage/storageAccounts@2023-01-01' = {
  name: storageAccountName
  location: location
  kind: 'StorageV2'
  sku: {
    name: 'Standard_LRS'
  }
  properties: {
    accessTier: 'Hot'
    minimumTlsVersion: 'TLS1_2'
    supportsHttpsTrafficOnly: true
  }
}

resource blobService 'Microsoft.Storage/storageAccounts/blobServices@2023-01-01' = {
  parent: storageAccount
  name: 'default'
  properties: {
    changeFeed: {
      enabled: true
    }
    deleteRetentionPolicy: {
      enabled: true
      days: 7
    }
    containerDeleteRetentionPolicy: {
      enabled: true
      days: 7
    }
  }
}

resource dataContainer 'Microsoft.Storage/storageAccounts/blobServices/containers@2023-01-01' = {
  parent: blobService
  name: 'data'
  properties: {
    publicAccess: 'None'
  }
}

output connectionString string = 'DefaultEndpointProtocol=https;AccountName=${storageAccount.name};AccountKey=${listKeys(storageAccount.id, '2023-01-01').keys[0].value};EndpointSuffix=core.windows.net'
```

### Key Vault (with access policies for managed identity)

```bicep
param keyVaultName string
param location string
param tenantId string = subscription().tenantId
param appManagedIdentityPrincipalId string

resource keyVault 'Microsoft.KeyVault/vaults@2023-02-01' = {
  name: keyVaultName
  location: location
  properties: {
    tenantId: tenantId
    sku: {
      family: 'A'
      name: 'standard'
    }
    enableSoftDelete: true
    softDeleteRetentionInDays: 90
    enableRbacAuthorization: true  // ← use RBAC instead of access policies
  }
}

resource kvRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  scope: keyVault
  name: guid(keyVault.id, appManagedIdentityPrincipalId, 'Key Vault Secrets User')
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '4633458b-17de-408a-b874-0445c86b69e6')  // Key Vault Secrets User
    principalId: appManagedIdentityPrincipalId
  }
}

output id string = keyVault.id
output name string = keyVault.name
output vaultUri string = keyVault.properties.vaultUri
```

### Cosmos DB Account (multi-region, PITR backup)

```bicep
param accountName string
param location string
param primaryRegion string = location
param secondaryRegions array = []

resource cosmosAccount 'Microsoft.DocumentDB/databaseAccounts@2023-04-15' = {
  name: accountName
  location: location
  kind: 'GlobalDocumentDB'
  properties: {
    databaseAccountOfferType: 'Standard'
    locations: [
      {
        locationName: primaryRegion
        failoverPriority: 0
        isZoneRedundant: true
      }
    ] + [for (region, i) in secondaryRegions: {
      locationName: region
      failoverPriority: i + 1
      isZoneRedundant: true
    }]
    consistencyPolicy: {
      defaultConsistencyLevel: 'Session'
      maxStalenessPrefix: 100
      maxIntervalInSeconds: 5
    }
    enableAutomaticFailover: true
    enableMultipleWriteLocations: false  // set to true for multi-write
    backupPolicy: {
      type: 'Continuous'
      continuousModeProperties: {
        retentionInMinutes: 1440  // 24 hours
      }
    }
  }
}

output id string = cosmosAccount.id
output connectionString string = cosmosAccount.listConnectionStrings().connectionStrings[0].connectionString
```

### AKS Cluster (with RBAC, monitoring, system-assigned identity)

```bicep
param clusterName string
param location string
param nodeCount int = 3
param vmSize string = 'Standard_D2s_v3'
param kubernetesVersion string = '1.27.3'
param logAnalyticsWorkspaceId string

resource aksCluster 'Microsoft.ContainerService/managedClusters@2023-06-01' = {
  name: clusterName
  location: location
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    kubernetesVersion: kubernetesVersion
    enableRBAC: true
    dnsPrefix: clusterName
    agentPoolProfiles: [
      {
        name: 'system'
        count: nodeCount
        vmSize: vmSize
        osType: 'Linux'
        mode: 'System'
        type: 'VirtualMachineScaleSets'
        enableAutoScaling: true
        minCount: 1
        maxCount: 5
        availabilityZones: [
          '1'
          '2'
          '3'
        ]
      }
    ]
    networkProfile: {
      networkPlugin: 'azure'
      networkPolicy: 'azure'
      loadBalancerSku: 'standard'
      serviceCidr: '10.0.0.0/16'
      dnsServiceIP: '10.0.0.10'
      dockerBridgeCidr: '172.17.0.1/16'
    }
    addonProfiles: {
      omsagent: {
        enabled: true
        config: {
          logAnalyticsWorkspaceResourceID: logAnalyticsWorkspaceId
        }
      }
      azureKeyvaultSecretsProvider: {
        enabled: true
        config: {
          enableSecretRotation: 'true'
          rotationPollInterval: '2m'
        }
      }
    }
    apiServerAccessProfile: {
      enablePrivateCluster: false  // set to true for private cluster
      authorizedIPRanges: [
        '1.2.3.4/32'  // restrict to your IP
      ]
    }
  }
}

output kubeconfig string = aksCluster.listClusterAdminCredential().kubeconfigs[0].value  // Base64 encoded
output id string = aksCluster.id
```

---

## Common Pitfalls & How to Fix Them

| Mistake | Why It's Bad | Fix |
|---------|-------------|-----|
| Hardcoded secrets in Bicep | Secret exposed in version control + template history | Use `@secure()` params + Key Vault reference in param file |
| Wrong API version | Resource fails to deploy; missing new properties | Check [Azure Resource Manager documentation](https://learn.microsoft.com/en-us/azure/templates/); use latest stable |
| Circular dependencies | Deployment hangs or fails | Use `dependsOn` explicitly if symbolic reference doesn't work |
| Storing sensitive outputs | Secret appears in deployment history | Don't output secrets; use Key Vault for storage |
| Modifying managed resources outside template | Drift = template fails next deploy | Enable deleteLock on critical resources; enforce policy |
| Loop size not deterministic | Deployment unpredictable (different runs = different results) | Use fixed-size arrays; avoid reference() in loop count |
| Not using RBAC for Key Vault | Access policies are complex, hard to audit | Use `enableRbacAuthorization: true` + roleAssignments |
| Missing depends_on for custom ordering | Parallel deployment tries impossible order | Explicitly add `dependsOn: [resourceA.id]` |
| Using reference() when symbolic ref works | Unnecessary complexity | Use `resourceName.id` or `resourceName.property` instead |
| No validation before deploy | Errors discovered post-deploy, wasted time | Always run `az deployment group validate` first |

---

## Bicep Build & IDE Tips

```bash
# Decompile ARM template to Bicep (if you have JSON template)
az bicep decompile --file azuredeploy.json

# Check syntax without deploying
az bicep build --file main.bicep

# Lint (code style, best practices)
az bicep lint --file main.bicep
```

**VS Code Snippets** for faster typing:
- Type `res` + Tab → scaffold a resource block
- Type `param` + Tab → scaffold a parameter
- Type `var` + Tab → scaffold a variable
- Type `mod` + Tab → scaffold a module call
- Type `loop` + Tab → scaffold a for loop

