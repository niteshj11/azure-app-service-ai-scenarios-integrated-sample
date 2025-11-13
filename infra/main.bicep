@minLength(1)
@maxLength(64)  
@description('Name of the environment provided by azd')
param environmentName string = replace(resourceGroup().name, 'rg-', '')

@minLength(1)
@description('Primary location for all resources')
param location string = resourceGroup().location

@description('Id of the user or app to assign application roles')
param principalId string = ''

// User Configuration Options
@description('Enable Azure AI services and AI Foundry project')
param enableAIServices bool = false
@description('Enable Managed Identity for the App Service')
param enableManagedIdentity bool = true
@description('Enable Application Insights monitoring')
param enableApplicationInsights bool = false
@description('Enable Azure AI Search service')
param enableSearchService bool = false
@description('Enable Azure Key Vault for secure configuration storage')
param enableKeyVault bool = true

// Optional existing resources
@description('Use this parameter to use an existing AI project resource ID')
param azureExistingAIProjectResourceId string = ''


// Resource names (optional - will be generated if not provided)
@description('The Azure AI Foundry Hub resource name. If omitted will be generated')
param aiProjectName string = ''
@description('The application insights resource name. If omitted will be generated')
param applicationInsightsName string = ''
@description('The AI Services resource name. If omitted will be generated')
param aiServicesName string = ''
@description('The Azure Search resource name. If omitted will be generated')
param searchServiceName string = ''
@description('The search index name')
param aiSearchIndexName string = 'techmart-index'
@description('The Azure Storage Account resource name. If omitted will be generated')
param storageAccountName string = ''
@description('The log analytics workspace name. If omitted will be generated')
param logAnalyticsWorkspaceName string = ''
@description('The App Service plan name. If omitted will be generated')
param appServicePlanName string = ''
@description('The Key Vault name. If omitted will be generated as <projectname>-kv')
param keyVaultName string = ''

// External Azure AI credentials (for existing AI services)
// Note: These will be configured by users via the settings page after deployment
@description('External Azure AI endpoint URL (will be stored in Key Vault)')
param externalAzureAIEndpoint string = ''
@description('External Azure AI API key (will be stored in Key Vault)')
@secure()
param externalAzureAIApiKey string = ''

// Chat completion model
@description('Format of the chat model to deploy')
@allowed(['Microsoft', 'OpenAI'])
param chatModelFormat string = 'OpenAI'
@description('Name of the chat model to deploy')
param chatModelName string = 'gpt-4o-mini'
@description('Name of the model deployment')
param chatDeploymentName string = 'gpt-4o-mini'

@description('Version of the chat model to deploy')
// See version availability in this table:
// https://learn.microsoft.com/azure/ai-services/openai/concepts/models#global-standard-model-availability
param chatModelVersion string = '2024-07-18'

@description('Sku of the chat deployment')
param chatDeploymentSku string = 'GlobalStandard'

@description('Capacity of the chat deployment')
// You can increase this, but capacity is limited per model/region, so you will get errors if you go over
// https://learn.microsoft.com/en-us/azure/ai-services/openai/quotas-limits
param chatDeploymentCapacity int = 30

// Embedding model
@description('Format of the embedding model to deploy')
@allowed(['Microsoft', 'OpenAI'])
param embedModelFormat string = 'OpenAI'

@description('Name of the embedding model to deploy')
param embedModelName string = 'text-embedding-3-small'
@description('Name of the embedding model deployment')
param embeddingDeploymentName string = 'text-embedding-3-small'
@description('Embedding model dimensionality')
param embeddingDeploymentDimensions string = '100'

@description('Version of the embedding model to deploy')
// See version availability in this table:
// https://learn.microsoft.com/azure/ai-services/openai/concepts/models#embeddings-models
param embedModelVersion string = '1'

@description('Sku of the embeddings model deployment')
param embedDeploymentSku string = 'Standard'

@description('Capacity of the embedding deployment')
// You can increase this, but capacity is limited per model/region, so you will get errors if you go over
// https://learn.microsoft.com/azure/ai-services/openai/quotas-limits
param embedDeploymentCapacity int = 30

// Legacy compatibility parameters 
param useApplicationInsights bool = true
@description('Use the RAG search')
param useSearchService bool = false

@description('Do we want to use the Azure Monitor tracing')
param enableAzureMonitorTracing bool = false

@description('Do we want to use the Azure Monitor tracing for GenAI content recording')
param azureTracingGenAIContentRecordingEnabled bool = false

// Computed values based on user choices and legacy parameters
var shouldEnableAI = enableAIServices || !empty(azureExistingAIProjectResourceId)
var shouldEnableAppInsights = enableApplicationInsights || useApplicationInsights
var shouldEnableSearch = enableSearchService || useSearchService

param templateValidationMode bool = false

@description('Random seed to be used during generation of new resources suffixes.')
param seed string = newGuid()

var runnerPrincipalType = templateValidationMode? 'ServicePrincipal' : 'User'

var abbrs = loadJsonContent('./abbreviations.json')
var resourceToken = templateValidationMode? toLower(uniqueString(resourceGroup().id, environmentName, location, seed)) : toLower(uniqueString(resourceGroup().id, environmentName, location))
var tags = { 'azd-env-name': environmentName }

var aiChatModel = [
  {
    name: chatDeploymentName
    model: {
      format: chatModelFormat
      name: chatModelName
      version: chatModelVersion
    }
    sku: {
      name: chatDeploymentSku
      capacity: chatDeploymentCapacity
    }
  }
]
var aiEmbeddingModel = [ 
  {
    name: embeddingDeploymentName
    model: {
      format: embedModelFormat
      name: embedModelName
      version: embedModelVersion
    }
    sku: {
      name: embedDeploymentSku
      capacity: embedDeploymentCapacity
    }
  }
]

var aiDeployments = concat(
  aiChatModel,
  shouldEnableSearch ? aiEmbeddingModel : [])

// Resources will be deployed to the resource group managed by azd

var logAnalyticsWorkspaceResolvedName = !shouldEnableAppInsights
  ? ''
  : !empty(logAnalyticsWorkspaceName)
      ? logAnalyticsWorkspaceName
      : '${abbrs.operationalInsightsWorkspaces}${resourceToken}'

var resolvedSearchServiceName = !shouldEnableSearch
  ? ''
  : !empty(searchServiceName) ? searchServiceName : '${abbrs.searchSearchServices}${resourceToken}'

var resolvedKeyVaultName = !enableKeyVault
  ? ''
  : !empty(keyVaultName) ? keyVaultName : '${environmentName}-kv'

// STEP 1: AI and Search services (if enabled)
module ai 'core/host/ai-environment.bicep' = if (shouldEnableAI && empty(azureExistingAIProjectResourceId)) {
  name: 'ai'
  params: {
    location: location
    tags: tags
    aiProjectName: !empty(aiProjectName) ? aiProjectName : '${abbrs.machineLearningServicesWorkspaces}${resourceToken}'
    aiServicesName: !empty(aiServicesName) ? aiServicesName : '${abbrs.cognitiveServicesAccounts}${resourceToken}'
    storageAccountName: !empty(storageAccountName) ? storageAccountName : '${abbrs.storageStorageAccounts}${resourceToken}'
    logAnalyticsName: logAnalyticsWorkspaceResolvedName
    applicationInsightsName: !empty(applicationInsightsName) ? applicationInsightsName : '${abbrs.insightsComponents}${resourceToken}'
    searchServiceName: resolvedSearchServiceName
    aiServiceModelDeployments: aiDeployments
    appInsightConnectionName: 'appinsight-connection'
    runnerPrincipalId: principalId
    runnerPrincipalType: runnerPrincipalType
  }
}

module search 'core/search/search-services.bicep' = if (shouldEnableSearch && shouldEnableAI && empty(azureExistingAIProjectResourceId)) {
  name: 'search'
  params: {
    location: location
    tags: tags
    name: resolvedSearchServiceName
    authOptions: {
      aadOrApiKey: {
        aadAuthFailureMode: 'http401WithBearerChallenge'
      }
    }
  }
}

// App Service Plan for hosting the TechMart AI chatbot
module appServicePlan 'core/host/appserviceplan.bicep' = {
  name: 'appserviceplan'
  params: {
    name: !empty(appServicePlanName) ? appServicePlanName : '${environmentName}-asplan'
    location: location
    tags: tags
    sku: {
      name: 'B2'
      capacity: 1
    }
    kind: 'linux'
    reserved: true
  }
}

// STEP 2: TechMart AI App Service deployment (deployed after KeyVault)
module api 'api.bicep' = {
  name: 'api'
  params: {
    name: '${replace(environmentName, '-', '')}app'
    location: location
    tags: union(tags, { 'azd-service-name': 'api' })
    identityName: enableManagedIdentity ? '${environmentName}-mi' : ''
    appServicePlanId: appServicePlan.outputs.id
    enableAIServices: shouldEnableAI
    enableManagedIdentity: enableManagedIdentity
    azureExistingAIProjectResourceId: azureExistingAIProjectResourceId
    chatDeploymentName: chatDeploymentName
    aiSearchIndexName: aiSearchIndexName
    searchServiceEndpoint: ''
    embeddingDeploymentName: embeddingDeploymentName
    embeddingDeploymentDimensions: embeddingDeploymentDimensions
    enableAzureMonitorTracing: enableAzureMonitorTracing
    azureTracingGenAIContentRecordingEnabled: azureTracingGenAIContentRecordingEnabled
    projectEndpoint: ''
    applicationInsightsName: shouldEnableAppInsights ? (!empty(applicationInsightsName) ? applicationInsightsName : '${abbrs.insightsComponents}${resourceToken}') : ''
    // Infrastructure resources - App Service needs to know about these
    enableKeyVault: enableKeyVault
    keyVaultName: resolvedKeyVaultName
    // Note: Credentials are now managed by application via settings page
  }
}

// STEP 2b: Key Vault - Provision AFTER App Service (uses App Service Managed Identity)
module keyVault 'core/security/keyvault.bicep' = if (enableKeyVault) {
  name: 'keyvault'
  params: {
    name: resolvedKeyVaultName
    location: location
    tags: tags
    principalId: principalId  // Deployment user access
    appServicePrincipalId: enableManagedIdentity ? api.outputs.SERVICE_API_IDENTITY_PRINCIPAL_ID : ''  // App Service Managed Identity
    // Skip secrets for now - will be populated after KeyVault is provisioned
    azureAIEndpoint: ''
    azureAIApiKey: ''
  }
  // Depends on api implicitly through api.outputs.SERVICE_API_IDENTITY_PRINCIPAL_ID
}

// STEP 3: Populate KeyVault with secrets after App Service is deployed
module keyVaultSecrets 'core/security/keyvault-secrets.bicep' = if (enableKeyVault && !empty(externalAzureAIEndpoint)) {
  name: 'keyvault-secrets'
  params: {
    keyVaultName: resolvedKeyVaultName
    azureAIEndpoint: externalAzureAIEndpoint
    azureAIApiKey: externalAzureAIApiKey
  }
  dependsOn: [keyVault, api]
}

// User roles
module userRoleAzureAIDeveloper 'core/security/role.bicep' = if (shouldEnableAI) {
  name: 'user-role-azureai-developer'
  params: {
    principalType: runnerPrincipalType
    principalId: principalId
    roleDefinitionId: '64702f94-c441-49e6-a78b-ef80e0188fee'
  }
}

module userRoleSearchIndexDataReader 'core/security/role.bicep' = if (useSearchService) {
  name: 'user-role-search-index-data-reader'
  params: {
    principalType: runnerPrincipalType
    principalId: principalId
    roleDefinitionId: '1407120a-92aa-4202-b7e9-c0e197c71c8f'
  }
}

module apiRoleSearchIndexDataReader 'core/security/role.bicep' = if (useSearchService) {
  name: 'api-role-search-index-data-reader'
  params: {
    principalType: 'ServicePrincipal'
    principalId: api.outputs.SERVICE_API_IDENTITY_PRINCIPAL_ID
    roleDefinitionId: '1407120a-92aa-4202-b7e9-c0e197c71c8f'
  }
}

module userRoleSearchServiceContributor 'core/security/role.bicep' = if (useSearchService) {
  name: 'user-role-search-service-contributor'
  params: {
    principalType: runnerPrincipalType
    principalId: principalId
    roleDefinitionId: '7ca78c08-252a-4471-8644-bb5ff32d4ba0'
  }
}

module apiRoleSearchServiceContributor 'core/security/role.bicep' = if (useSearchService) {
  name: 'api-role-search-service-contributor'
  params: {
    principalType: 'ServicePrincipal'
    principalId: api.outputs.SERVICE_API_IDENTITY_PRINCIPAL_ID
    roleDefinitionId: '7ca78c08-252a-4471-8644-bb5ff32d4ba0'
  }
}

// App principal access to AI services
module apiRoleAzureAIDeveloper 'core/security/role.bicep' = if (shouldEnableAI && enableManagedIdentity) {
  name: 'api-role-azureai-developer'
  params: {
    principalType: 'ServicePrincipal'
    principalId: api.outputs.SERVICE_API_IDENTITY_PRINCIPAL_ID
    roleDefinitionId: '64702f94-c441-49e6-a78b-ef80e0188fee'
  }
}

// App principal access to Key Vault (Key Vault Secrets Officer - allows read/write)
module apiRoleKeyVaultSecretsOfficer 'core/security/role.bicep' = if (enableKeyVault && enableManagedIdentity) {
  name: 'api-role-keyvault-secrets-officer'
  params: {
    principalType: 'ServicePrincipal'
    principalId: api.outputs.SERVICE_API_IDENTITY_PRINCIPAL_ID
    roleDefinitionId: 'b86a8fe4-44ce-4948-aee5-eccb2c155cd7' // Key Vault Secrets Officer
  }
}

// User access to Key Vault (Key Vault Administrator for deployment) - temporarily disabled
// module userRoleKeyVaultAdministrator 'core/security/role.bicep' = if (enableKeyVault) {
//   name: 'user-role-keyvault-administrator'
//   scope: rg
//   params: {
//     principalType: runnerPrincipalType
//     principalId: principalId
//     roleDefinitionId: '00482a5a-887f-4fb3-b363-3b7fe8e74483' // Key Vault Administrator
//   }
// }

// Debug Outputs - Track deployment flow and values for KeyVault-first approach
output DEBUG_PARAMETERS object = {
  enableKeyVault: enableKeyVault
  enableManagedIdentity: enableManagedIdentity
  principalIdProvided: !empty(principalId)
  principalIdLength: length(principalId)
  resolvedKeyVaultName: resolvedKeyVaultName
  externalAzureAIEndpointProvided: !empty(externalAzureAIEndpoint)
  keyVaultSecretsModuleDeployed: enableKeyVault && !empty(externalAzureAIEndpoint)
}

// Resource Naming Debug - Show what names will be used
output DEBUG_RESOURCE_NAMES object = {
  environmentName: environmentName
  resourceToken: resourceToken
  appServiceName: '${replace(environmentName, '-', '')}app'
  appServicePlanName: !empty(appServicePlanName) ? appServicePlanName : '${environmentName}-asplan'
  keyVaultName: resolvedKeyVaultName
  managedIdentityName: enableManagedIdentity ? '${environmentName}-mi' : ''
  aiProjectName: !empty(aiProjectName) ? aiProjectName : '${abbrs.machineLearningServicesWorkspaces}${resourceToken}'
  aiServicesName: !empty(aiServicesName) ? aiServicesName : '${abbrs.cognitiveServicesAccounts}${resourceToken}'
  storageAccountName: !empty(storageAccountName) ? storageAccountName : '${abbrs.storageStorageAccounts}${resourceToken}'
}

output DEBUG_KEYVAULT_FIRST_DEPLOYMENT object = {
  step1_keyVault: enableKeyVault ? 'Deployed first (no app dependency)' : 'Disabled'
  step2_appService: 'Deployed after KeyVault'
  step3_secrets: enableKeyVault && !empty(externalAzureAIEndpoint) ? 'Will populate after app' : 'No endpoint provided'
  step4_roleAssignments: 'RBAC roles assigned automatically'
}

// Outputs
output AZURE_LOCATION string = location
output AZURE_RESOURCE_GROUP string = resourceGroup().name

// Outputs required for local development server
output AZURE_TENANT_ID string = tenant().tenantId
output AZURE_EXISTING_AIPROJECT_RESOURCE_ID string = azureExistingAIProjectResourceId
output AZURE_AI_CHAT_DEPLOYMENT_NAME string = shouldEnableAI ? chatDeploymentName : ''
output AZURE_AI_EMBED_DEPLOYMENT_NAME string = shouldEnableSearch ? embeddingDeploymentName : ''
output AZURE_AI_SEARCH_INDEX_NAME string = shouldEnableSearch ? aiSearchIndexName : ''
output AZURE_AI_SEARCH_ENDPOINT string = ''
output AZURE_AI_EMBED_DIMENSIONS string = shouldEnableSearch ? embeddingDeploymentDimensions : ''
output AZURE_EXISTING_AIPROJECT_ENDPOINT string = ''
output ENABLE_AZURE_MONITOR_TRACING bool = shouldEnableAppInsights ? enableAzureMonitorTracing : false
output AZURE_TRACING_GEN_AI_CONTENT_RECORDING_ENABLED bool = shouldEnableAppInsights ? azureTracingGenAIContentRecordingEnabled : false

// Key Vault outputs
output AZURE_KEY_VAULT_NAME string = enableKeyVault ? resolvedKeyVaultName : ''
output AZURE_KEY_VAULT_URI string = enableKeyVault ? 'https://${resolvedKeyVaultName}${environment().suffixes.keyvaultDns}/' : ''

// Outputs required by azd for App Service
output SERVICE_API_IDENTITY_PRINCIPAL_ID string = api.outputs.SERVICE_API_IDENTITY_PRINCIPAL_ID
output SERVICE_API_NAME string = api.outputs.SERVICE_API_NAME
output SERVICE_API_URI string = api.outputs.SERVICE_API_URI
output SERVICE_API_ENDPOINTS array = ['${api.outputs.SERVICE_API_URI}']
