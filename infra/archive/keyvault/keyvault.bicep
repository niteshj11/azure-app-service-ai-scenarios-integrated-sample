@description('Name of the Azure Key Vault')
param name string

@description('Location for all resources')
param location string = resourceGroup().location

@description('Tags to apply to all resources')
param tags object = {}

@description('Principal ID of the user or service principal to grant access')
param principalId string = ''

@description('Principal ID of the App Service Managed Identity (optional)')
param appServicePrincipalId string = ''

@description('Enable RBAC authorization instead of access policies')
param enableRbacAuthorization bool = true

@description('Enable soft delete for the Key Vault')
param enableSoftDelete bool = true

@description('Soft delete retention days')
param softDeleteRetentionInDays int = 90

@description('Enable purge protection')
param enablePurgeProtection bool = false

@description('Enable public network access')
param enablePublicNetworkAccess bool = true

@description('SKU of the Key Vault')
@allowed(['standard', 'premium'])
param sku string = 'standard'

resource keyVault 'Microsoft.KeyVault/vaults@2023-07-01' = {
  name: name
  location: location
  tags: tags
  properties: {
    sku: {
      family: 'A'
      name: sku
    }
    tenantId: tenant().tenantId
    enabledForDeployment: false
    enabledForDiskEncryption: false
    enabledForTemplateDeployment: true
    enableSoftDelete: enableSoftDelete
    softDeleteRetentionInDays: softDeleteRetentionInDays
    enablePurgeProtection: enablePurgeProtection ? true : null
    publicNetworkAccess: enablePublicNetworkAccess ? 'Enabled' : 'Disabled'
    enableRbacAuthorization: enableRbacAuthorization
    accessPolicies: enableRbacAuthorization ? [] : concat(!empty(principalId) ? [
      {
        tenantId: tenant().tenantId
        objectId: principalId
        permissions: {
          keys: []
          secrets: [
            'get'
            'list'
            'set'
            'delete'
            'recover'
          ]
          certificates: []
        }
      }
    ] : [], !empty(appServicePrincipalId) ? [
      {
        tenantId: tenant().tenantId
        objectId: appServicePrincipalId
        permissions: {
          keys: []
          secrets: [
            'get'
            'list'
          ]
          certificates: []
        }
      }
    ] : [])
  }
}

// Define the secrets that will be stored in Key Vault
@description('Azure AI endpoint URL')
param azureAIEndpoint string = ''

@description('Azure AI API key')
@secure()
param azureAIApiKey string = ''

// Store Azure AI endpoint in Key Vault (if provided)
resource endpointSecret 'Microsoft.KeyVault/vaults/secrets@2023-07-01' = if (!empty(azureAIEndpoint)) {
  parent: keyVault
  name: 'azure-ai-endpoint'
  properties: {
    value: azureAIEndpoint
    contentType: 'Azure AI Inference Endpoint URL'
  }
}

// Store Azure AI API key in Key Vault (if provided)
resource apiKeySecret 'Microsoft.KeyVault/vaults/secrets@2023-07-01' = if (!empty(azureAIApiKey)) {
  parent: keyVault
  name: 'azure-ai-api-key'
  properties: {
    value: azureAIApiKey
    contentType: 'Azure AI Inference API Key'
  }
}

// Debug Outputs
output DEBUG_KEYVAULT object = {
  enableRbacAuthorization: enableRbacAuthorization
  principalIdProvided: !empty(principalId)
  principalIdLength: length(principalId)
  azureAIEndpointProvided: !empty(azureAIEndpoint)
  tenantId: tenant().tenantId
}

// Outputs
output keyVaultId string = keyVault.id
output keyVaultName string = keyVault.name
output keyVaultUri string = keyVault.properties.vaultUri

// Key Vault reference format for App Service settings (always provide the format)
output endpointKeyVaultReference string = '@Microsoft.KeyVault(VaultName=${keyVault.name};SecretName=azure-ai-endpoint)'
output apiKeyKeyVaultReference string = '@Microsoft.KeyVault(VaultName=${keyVault.name};SecretName=azure-ai-api-key)'

// Flag to indicate if secrets were created
output hasEndpointSecret bool = !empty(azureAIEndpoint)
