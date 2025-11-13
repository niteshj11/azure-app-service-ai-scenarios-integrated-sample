@description('Name of the existing Key Vault')
param keyVaultName string

@description('Azure AI endpoint URL')
param azureAIEndpoint string = ''

@description('Azure AI API key')
@secure()
param azureAIApiKey string = ''

// Reference to existing Key Vault
resource keyVault 'Microsoft.KeyVault/vaults@2023-07-01' existing = {
  name: keyVaultName
}

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

output endpointSecretCreated bool = !empty(azureAIEndpoint)
// Note: Can't output secure parameter value, but can confirm creation
output secretsProcessed bool = true
