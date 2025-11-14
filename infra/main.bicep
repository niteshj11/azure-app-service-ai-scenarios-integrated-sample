@minLength(1)
@maxLength(64)  
@description('Name of the environment provided by azd')
param environmentName string = replace(resourceGroup().name, 'rg-', '')

@minLength(1)
@description('Primary location for all resources')
@metadata({
  azd: {
    type: 'location'
  }
})
param location string = resourceGroup().location

@description('Id of the user or app to assign application roles')
param principalId string = ''

// User Configuration Options - All collected via preprovision hook for better UX
// No direct prompting - all parameters have defaults and are populated by hook
@description('Choose: new (create AI services) or existing (use your AI Foundry project)')
@allowed(['new', 'existing', ''])
param aSetupChoice string = ''

@description('Your existing AI Foundry project endpoint URL (collected conditionally)')
param bFoundryEndpoint string = ''

@description('Your chat model deployment name (collected conditionally)')
param cChatModelName string = ''

@description('Your audio model deployment name (collected conditionally)')
param dAudioModelName string = ''

// Optional Configuration - Strategic defaults (will not prompt unless overridden)
@description('Subscription ID where your existing AI Foundry project is located')
param existingAISubscriptionId string = subscription().subscriptionId

@description('Resource Group name where your existing AI Foundry project is located')
param existingAIResourceGroupName string = resourceGroup().name

@description('Enable Managed Identity for the App Service (required for Azure AI integration)')
param enableManagedIdentity bool = true

@description('Enable Application Insights monitoring')
param enableApplicationInsights bool = false

// Azure AI Search service archived - not used in current implementation

// Key Vault functionality archived - using Managed Identity with environment variables

// Computed values - Handle conditional parameters
var shouldProvisionNewAI = aSetupChoice == 'new'
var shouldUseExistingAI = aSetupChoice == 'existing' && !empty(bFoundryEndpoint)

// Extract AI account name from endpoint URL and construct resource ID (only for existing AI)
// Handles both cognitiveservices.azure.com and services.ai.azure.com domains
var aiAccountName = shouldUseExistingAI ? split(split(bFoundryEndpoint, '://')[1], '.')[0] : ''
var computedAIResourceId = shouldUseExistingAI ? '/subscriptions/${existingAISubscriptionId}/resourceGroups/${existingAIResourceGroupName}/providers/Microsoft.CognitiveServices/accounts/${aiAccountName}' : ''

// Model deployment names with intelligent defaults
var effectiveChatModelName = !empty(cChatModelName) ? cChatModelName : (shouldProvisionNewAI ? chatModelName : 'gpt-4o-mini')
var effectiveAudioModelName = !empty(dAudioModelName) ? dAudioModelName : 'gpt-4o-mini-audio-preview'


// Resource names (optional - will be generated if not provided)
@description('The Azure AI Foundry Hub resource name. If omitted will be generated')
param aiProjectName string = ''
// Application insights name parameter archived
@description('The AI Services resource name. If omitted will be generated')
param aiServicesName string = ''
// Search index name parameter archived
@description('The Azure Storage Account resource name. If omitted will be generated')
param storageAccountName string = ''
@description('The App Service plan name. If omitted will be generated')
param appServicePlanName string = ''
// Key Vault name parameter archived

// Legacy parameters (kept for compatibility)
@description('Legacy parameter - use aiFoundryMode instead')
param externalAzureAIEndpoint string = ''

// Chat completion model - Strategic defaults for new AI deployments
@description('Format of the chat model to deploy')
@allowed(['Microsoft', 'OpenAI'])
param chatModelFormat string = 'OpenAI'

@description('Name of the chat model to deploy')
param chatModelName string = 'gpt-4o-mini'
// Note: Audio model deployment can be configured through the application settings page after deployment

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

// Embedding model parameters archived - not used without search functionality

// Legacy compatibility parameters archived
// RAG search parameter archived - not used in current implementation

@description('Do we want to use the Azure Monitor tracing')
param enableAzureMonitorTracing bool = false

@description('Do we want to use the Azure Monitor tracing for GenAI content recording')
param azureTracingGenAIContentRecordingEnabled bool = false

// Computed values based on user choices and legacy parameters
var shouldEnableAI = shouldProvisionNewAI || shouldUseExistingAI
var shouldEnableAppInsights = enableApplicationInsights
// useApplicationInsights parameter usage removed for simplicity
// shouldEnableSearch variable archived - search functionality not used

param templateValidationMode bool = false

@description('Random seed to be used during generation of new resources suffixes.')
param seed string = newGuid()

var runnerPrincipalType = templateValidationMode? 'ServicePrincipal' : 'User'

var abbrs = loadJsonContent('./abbreviations.json')
var resourceToken = templateValidationMode? toLower(uniqueString(resourceGroup().id, environmentName, location, seed)) : toLower(uniqueString(resourceGroup().id, environmentName, location))
var tags = { 'azd-env-name': environmentName }

// Use conditional parameter or intelligent default
var effectiveChatDeploymentName = effectiveChatModelName

var aiChatModel = [
  {
    name: effectiveChatDeploymentName
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
// aiEmbeddingModel variable archived - not used without search functionality

var aiDeployments = aiChatModel
// Embedding model removed - not used without search functionality

// Resources will be deployed to the resource group managed by azd

// Search service variables moved to archive with search module

// Key Vault name resolution archived

// STEP 1: AI and Search services (provision new AI services only)
module ai 'core/host/ai-environment.bicep' = if (shouldProvisionNewAI) {
  name: 'ai'
  params: {
    location: location
    tags: tags
    aiProjectName: !empty(aiProjectName) ? aiProjectName : '${environmentName}-aiproject'
    aiServicesName: !empty(aiServicesName) ? aiServicesName : '${environmentName}-ai'
    storageAccountName: !empty(storageAccountName) ? storageAccountName : '${replace(environmentName, '-', '')}st'
    aiServiceModelDeployments: aiDeployments
    appInsightConnectionName: 'appinsight-connection'
  }
}

// Search service module archived - uncomment and restore from archive/ if RAG scenarios needed
// module search 'core/search/search-services.bicep' = if (shouldEnableSearch && shouldProvisionNewAI) {
//   name: 'search'
//   params: {
//     location: location
//     tags: tags
//     name: resolvedSearchServiceName
//     authOptions: {
//       aadOrApiKey: {
//         aadAuthFailureMode: 'http401WithBearerChallenge'
//       }
//     }
//   }
// }

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
    appServicePlanId: appServicePlan.outputs.id
    enableAIServices: shouldEnableAI
    enableManagedIdentity: enableManagedIdentity
    azureExistingAIProjectResourceId: computedAIResourceId
    aiFoundryEndpoint: bFoundryEndpoint
    chatDeploymentName: effectiveChatDeploymentName
    audioDeploymentName: effectiveAudioModelName
    // aiSearchIndexName and searchServiceEndpoint archived
    // embeddingDeploymentName and embeddingDeploymentDimensions archived
    enableAzureMonitorTracing: enableAzureMonitorTracing
    azureTracingGenAIContentRecordingEnabled: azureTracingGenAIContentRecordingEnabled
    projectEndpoint: ''
    // applicationInsightsName parameter archived
    // Note: Configuration managed via environment variables with Managed Identity
  }
}

// Key Vault module archived - using environment variables with Managed Identity

// Key Vault secrets module archived - using environment variables

// User roles
module userRoleAzureAIDeveloper 'core/security/role.bicep' = if (shouldEnableAI && !empty(principalId)) {
  name: 'user-role-azureai-developer'
  params: {
    principalType: runnerPrincipalType
    principalId: principalId
    roleDefinitionId: '64702f94-c441-49e6-a78b-ef80e0188fee'
  }
}

// Search service role assignments archived - search functionality removed

// App principal access to AI services (for new AI services)
module apiRoleAzureAIDeveloper 'core/security/role.bicep' = if (shouldProvisionNewAI && enableManagedIdentity) {
  name: 'api-role-azureai-developer'
  params: {
    principalType: 'ServicePrincipal'
    principalId: api.outputs.SERVICE_API_IDENTITY_PRINCIPAL_ID
    roleDefinitionId: '64702f94-c441-49e6-a78b-ef80e0188fee'
  }
}

// RBAC setup instructions for existing AI Foundry (manual step required)
module existingAIRbacInstructions 'core/ai/existing-ai-rbac.bicep' = if (shouldUseExistingAI && enableManagedIdentity) {
  name: 'existing-ai-rbac-instructions'
  params: {
    aiFoundryResourceId: computedAIResourceId
    appServicePrincipalId: api.outputs.SERVICE_API_IDENTITY_PRINCIPAL_ID
  }
}

// Key Vault role assignment archived - no longer needed with environment variables

// Key Vault user role archived

// Debug Outputs - Track deployment flow
output DEBUG_PARAMETERS object = {
  enableManagedIdentity: enableManagedIdentity
  principalIdProvided: !empty(principalId)
  principalIdLength: length(principalId)
  externalAzureAIEndpointProvided: !empty(externalAzureAIEndpoint)
}

// Resource Naming Debug - Show what names will be used
output DEBUG_RESOURCE_NAMES object = {
  environmentName: environmentName
  resourceToken: resourceToken
  appServiceName: '${replace(environmentName, '-', '')}app'
  appServicePlanName: !empty(appServicePlanName) ? appServicePlanName : '${environmentName}-asplan'
  // keyVaultName archived
  // managedIdentityName archived - using system-assigned identity only
  aiProjectName: !empty(aiProjectName) ? aiProjectName : '${abbrs.machineLearningServicesWorkspaces}${resourceToken}'
  aiServicesName: !empty(aiServicesName) ? aiServicesName : '${abbrs.cognitiveServicesAccounts}${resourceToken}'
  storageAccountName: !empty(storageAccountName) ? storageAccountName : '${abbrs.storageStorageAccounts}${resourceToken}'
}

output DEBUG_AI_FOUNDRY_DEPLOYMENT object = {
  aiFoundryMode: aSetupChoice
  shouldProvisionNewAI: shouldProvisionNewAI
  shouldUseExistingAI: shouldUseExistingAI
  existingEndpoint: bFoundryEndpoint
  existingResourceId: computedAIResourceId
  configurationMethod: 'environment-variables'
  rbacInstructions: shouldUseExistingAI ? 'Check existingAIRbacInstructions module output' : 'Auto-configured for new AI services'
}

// Outputs
output AZURE_LOCATION string = location
output AZURE_RESOURCE_GROUP string = resourceGroup().name

// Outputs required for local development server
output AZURE_TENANT_ID string = tenant().tenantId
output AZURE_EXISTING_AIPROJECT_RESOURCE_ID string = computedAIResourceId
output AZURE_AI_CHAT_DEPLOYMENT_NAME string = shouldEnableAI ? effectiveChatDeploymentName : ''
// Search-related outputs archived - search functionality removed
output AZURE_AI_SEARCH_ENDPOINT string = ''
output AZURE_EXISTING_AIPROJECT_ENDPOINT string = ''
output ENABLE_AZURE_MONITOR_TRACING bool = shouldEnableAppInsights ? enableAzureMonitorTracing : false
output AZURE_TRACING_GEN_AI_CONTENT_RECORDING_ENABLED bool = shouldEnableAppInsights ? azureTracingGenAIContentRecordingEnabled : false

// Key Vault outputs archived

// Outputs required by azd for App Service
output SERVICE_API_IDENTITY_PRINCIPAL_ID string = api.outputs.SERVICE_API_IDENTITY_PRINCIPAL_ID
output SERVICE_API_NAME string = api.outputs.SERVICE_API_NAME
output SERVICE_API_URI string = api.outputs.SERVICE_API_URI
output SERVICE_API_ENDPOINTS array = ['${api.outputs.SERVICE_API_URI}']
