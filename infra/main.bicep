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

@description('Location for AI services (must support required models like gpt-4o-mini)')
param aiLocation string = 'swedencentral'  // Default to Sweden Central which supports both chat and audio models

@description('Id of the user or app to assign application roles')
param principalId string = ''

// User Configuration Options - Parameters populated by azd from environment variables
// These are set by the preprovision hook in azure.yaml and passed via main.parameters.json
@description('Choose: new (create AI services) or existing (use your AI Foundry project)')
param aSetupChoice string = 'new'

@description('Your existing AI Foundry project endpoint URL (collected conditionally)')
param bFoundryEndpoint string = ''

@description('Your chat model deployment name (collected conditionally)')
param cChatModelName string = ''

@description('Your audio model deployment name (collected conditionally)')
param dAudioModelName string = ''

@description('AI Foundry subscription ID (automatically detected from endpoint)')
param eAISubscriptionId string = ''

@description('AI Foundry resource group name (automatically detected from endpoint)')
param fAIResourceGroup string = ''

// Optional Configuration - Strategic defaults (will not prompt unless overridden)  
@description('Subscription ID where your existing AI Foundry project is located')
param existingAISubscriptionId string = !empty(eAISubscriptionId) ? eAISubscriptionId : subscription().subscriptionId

@description('Resource Group name where your existing AI Foundry project is located')
param existingAIResourceGroupName string = !empty(fAIResourceGroup) ? fAIResourceGroup : resourceGroup().name



@description('Enable Managed Identity for the App Service (required for Azure AI integration)')
param enableManagedIdentity bool = true



// Azure AI Search service archived - not used in current implementation

// Key Vault functionality archived - using Managed Identity with environment variables

// Computed values - Handle conditional parameters
var shouldProvisionNewAI = aSetupChoice == 'new'

// Extract AI account name from endpoint URL and construct resource ID (only for existing AI)
// User provides complete endpoint with /models, so we extract the base URL for account name
var baseEndpointForName = !shouldProvisionNewAI ? replace(bFoundryEndpoint, '/models', '') : ''
var aiAccountName = !shouldProvisionNewAI ? split(split(baseEndpointForName, '://')[1], '.')[0] : ''
var computedAIResourceId = !shouldProvisionNewAI ? '/subscriptions/${existingAISubscriptionId}/resourceGroups/${existingAIResourceGroupName}/providers/Microsoft.CognitiveServices/accounts/${aiAccountName}' : ''

// Model deployment names (no fallbacks - require explicit parameters)
var effectiveChatModelName = shouldProvisionNewAI ? chatModelName : cChatModelName
var effectiveAudioModelName = shouldProvisionNewAI ? audioModelName : dAudioModelName


// Resource names (optional - will be generated if not provided)
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

@description('Name of the chat model to deploy (use gpt-4o-mini for better availability)')
param chatModelName string = 'gpt-4o-mini'

@description('Version of the chat model to deploy')
// See version availability in this table:
// https://learn.microsoft.com/azure/ai-services/openai/concepts/models#global-standard-model-availability
param chatModelVersion string = '2024-07-18'

@description('Sku of the chat deployment')
param chatDeploymentSku string = 'GlobalStandard'

@description('Capacity of the chat deployment')
// You can increase this, but capacity is limited per model/region, so you will get errors if you go over
// https://learn.microsoft.com/en-us/azure/ai-services/openai/quotas-limits
param chatDeploymentCapacity int = 100

// Audio model - Strategic defaults for new AI deployments
@description('Format of the audio model to deploy')
@allowed(['Microsoft', 'OpenAI'])
param audioModelFormat string = 'OpenAI'

@description('Name of the audio model to deploy')
param audioModelName string = 'gpt-4o-mini-audio-preview'

@description('Version of the audio model to deploy')
param audioModelVersion string = '2024-12-17'

@description('Sku of the audio deployment')
param audioDeploymentSku string = 'GlobalStandard'

@description('Capacity of the audio deployment')
param audioDeploymentCapacity int = 30

@description('Enable multi-service AI capabilities (required for vision and audio)')
param enableMultiServiceAI bool = true

// Embedding model parameters archived - not used without search functionality

// Legacy compatibility parameters archived
// RAG search parameter archived - not used in current implementation



// Computed values based on user choices and legacy parameters
var shouldEnableAI = true  // Always enable AI (either new or existing)

// AI Resource variables are now handled directly in the module calls
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
      name: effectiveChatModelName
      version: chatModelVersion
    }
    sku: {
      name: chatDeploymentSku
      capacity: chatDeploymentCapacity
    }
  }
]

var aiAudioModel = [
  {
    name: effectiveAudioModelName
    model: {
      format: audioModelFormat
      name: effectiveAudioModelName
      version: audioModelVersion
    }
    sku: {
      name: audioDeploymentSku
      capacity: audioDeploymentCapacity
    }
  }
]

// Validated regions that support BOTH gpt-4o-mini AND gpt-4o-mini-audio-preview
// Based on official Azure OpenAI documentation (Nov 2025) - eastus and eastus2 have better support
var dualModelSupportedRegions = ['eastus', 'eastus2', 'swedencentral']
var isDualModelSupported = contains(dualModelSupportedRegions, aiLocation)

// Deploy both chat and audio models in supported regions (only for new AI)
var aiDeployments = shouldProvisionNewAI ? (isDualModelSupported ? union(aiChatModel, aiAudioModel) : aiChatModel) : []

// Add validation message for unsupported regions
output deploymentWarning string = isDualModelSupported ? 'Both models deployed successfully' : 'Audio model skipped - unsupported region. Use swedencentral for full support.'
// Embedding model removed - not used without search functionality

// Resources will be deployed to the resource group managed by azd

// Search service variables moved to archive with search module

// Key Vault name resolution archived

// STEP 1: AI and Search services (provision new AI services only)
module ai 'core/host/ai-environment.bicep' = if (shouldProvisionNewAI) {
  name: 'ai'
  params: {
    location: aiLocation
    tags: tags
    aiServicesName: !empty(aiServicesName) ? aiServicesName : '${environmentName}-ai'
    storageAccountName: !empty(storageAccountName) ? storageAccountName : '${replace(environmentName, '-', '')}st'
    aiServiceModelDeployments: aiDeployments
    enableMultiServiceAI: enableMultiServiceAI
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

// App Service Plan for hosting the Zava AI chatbot
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

// STEP 2: Zava AI App Service deployment
module api 'api.bicep' = {
  name: 'api'
  params: {
    name: '${replace(environmentName, '-', '')}app'
    location: location
    tags: union(tags, { 'azd-service-name': 'api' })
    appServicePlanId: appServicePlan.outputs.id
    enableAIServices: shouldEnableAI
    enableManagedIdentity: enableManagedIdentity
    aiFoundryEndpoint: shouldProvisionNewAI ? ai!.outputs.endpoint : bFoundryEndpoint
    chatDeploymentName: effectiveChatDeploymentName
    audioDeploymentName: effectiveAudioModelName
  }
  dependsOn: shouldProvisionNewAI ? [ai] : []
}

// Key Vault module archived - using environment variables with Managed Identity

// Key Vault secrets module archived - using environment variables

// User roles - resource group level access for development
module userRoleAzureAIDeveloper 'core/security/role-resourcegroup.bicep' = if (shouldEnableAI && !empty(principalId)) {
  name: 'user-role-azureai-developer'
  params: {
    principalType: runnerPrincipalType
    principalId: principalId
    roleDefinitionId: '64702f94-c441-49e6-a78b-ef80e0188fee'
  }
}

// Search service role assignments archived - search functionality removed

// RBAC assignment for App Service MI to newly provisioned AI resource
module newAiServiceRoleAssignment 'core/security/role.bicep' = if (enableManagedIdentity && shouldProvisionNewAI) {
  name: 'new-ai-service-role-assignment'
  params: {
    principalType: 'ServicePrincipal'
    principalId: api.outputs.SERVICE_API_IDENTITY_PRINCIPAL_ID
    roleDefinitionId: '64702f94-c441-49e6-a78b-ef80e0188fee'  // Azure AI Developer
    targetResourceId: ai!.outputs.resourceId
  }
}

// RBAC assignment for App Service MI to existing AI resource
module existingAiServiceRoleAssignment 'core/security/role.bicep' = if (enableManagedIdentity && !shouldProvisionNewAI) {
  name: 'existing-ai-service-role-assignment'
  scope: resourceGroup(existingAISubscriptionId, existingAIResourceGroupName)
  params: {
    principalType: 'ServicePrincipal'
    principalId: api.outputs.SERVICE_API_IDENTITY_PRINCIPAL_ID
    roleDefinitionId: '64702f94-c441-49e6-a78b-ef80e0188fee'  // Azure AI Developer
    targetResourceId: computedAIResourceId
  }
}

// Key Vault role assignment archived - no longer needed with environment variables

// Key Vault user role archived

// Debug Outputs - Track deployment flow and parameter validation
output DEBUG_PARAMETERS object = {
  // Input Parameters Debug
  aSetupChoice: aSetupChoice
  shouldProvisionNewAI: shouldProvisionNewAI
  bFoundryEndpoint: bFoundryEndpoint
  cChatModelName: cChatModelName
  dAudioModelName: dAudioModelName
  eAISubscriptionId: eAISubscriptionId
  fAIResourceGroup: fAIResourceGroup
  
  // Computed Values Debug
  existingAISubscriptionId: existingAISubscriptionId
  existingAIResourceGroupName: existingAIResourceGroupName
  effectiveChatModelName: effectiveChatModelName
  effectiveAudioModelName: effectiveAudioModelName
  
  // Authentication Debug
  enableManagedIdentity: enableManagedIdentity
  principalIdProvided: !empty(principalId)
  principalIdLength: length(principalId)
  principalId: principalId
  
  // Legacy Parameter Debug
  externalAzureAIEndpointProvided: !empty(externalAzureAIEndpoint)
  externalAzureAIEndpoint: externalAzureAIEndpoint
  
  // Environment Debug
  location: location
  aiLocation: aiLocation
  environmentName: environmentName
  resourceToken: resourceToken
}

// Resource Naming Debug - Show what names will be used
output DEBUG_RESOURCE_NAMES object = {
  environmentName: environmentName
  resourceToken: resourceToken
  appServiceName: '${replace(environmentName, '-', '')}app'
  appServicePlanName: !empty(appServicePlanName) ? appServicePlanName : '${environmentName}-asplan'
  // keyVaultName archived
  // managedIdentityName archived - using system-assigned identity only
  aiServicesName: !empty(aiServicesName) ? aiServicesName : '${abbrs.cognitiveServicesAccounts}${resourceToken}'
  storageAccountName: !empty(storageAccountName) ? storageAccountName : '${abbrs.storageStorageAccounts}${resourceToken}'
}

// Debug Conditional Logic and Resource ID Construction
output DEBUG_CONDITIONAL_LOGIC object = {
  // Setup Choice Logic
  aSetupChoiceRaw: aSetupChoice
  shouldProvisionNewAI: shouldProvisionNewAI
  shouldProvisionNewAIExpression: 'aSetupChoice == "new" = ${aSetupChoice == 'new'}'
  
  // Existing AI Resource Construction
  bFoundryEndpointRaw: bFoundryEndpoint
  baseEndpointForName: baseEndpointForName
  aiAccountName: aiAccountName
  computedAIResourceId: computedAIResourceId
  
  // Model Name Resolution
  chatModelNameFromBicep: chatModelName
  chatModelNameFromUser: cChatModelName
  effectiveChatResult: effectiveChatModelName
  audioModelNameFromBicep: audioModelName
  audioModelNameFromUser: dAudioModelName
  effectiveAudioResult: effectiveAudioModelName
  
  // AI Location and Deployment Logic
  aiLocationUsed: aiLocation
  isDualModelSupported: isDualModelSupported
  dualModelSupportedRegions: dualModelSupportedRegions
  aiDeploymentsCount: length(aiDeployments)
}

output DEBUG_AI_FOUNDRY_DEPLOYMENT object = {
  aiFoundryMode: aSetupChoice
  shouldProvisionNewAI: shouldProvisionNewAI
  existingEndpoint: bFoundryEndpoint
  existingResourceId: computedAIResourceId
  configurationMethod: 'direct-environment-variables'
  rbacInstructions: !shouldProvisionNewAI ? 'Existing AI RBAC via existingAiServiceRoleAssignment module' : 'New AI RBAC via newAiServiceRoleAssignment module'
  
  // Module Deployment Debug
  aiModuleWillDeploy: shouldProvisionNewAI
  newAiRoleAssignmentWillDeploy: enableManagedIdentity && shouldProvisionNewAI
  existingAiRoleAssignmentWillDeploy: enableManagedIdentity && !shouldProvisionNewAI
  userRoleAssignmentWillDeploy: shouldEnableAI && !empty(principalId)
}

// Debug Endpoint Resolution
output DEBUG_ENDPOINTS object = {
  // Endpoint Logic Debug
  shouldProvisionNewAI: shouldProvisionNewAI
  bFoundryEndpointInput: bFoundryEndpoint
  
  // API Module Endpoint Parameter
  apiModuleEndpointParam: shouldProvisionNewAI ? 'ai!.outputs.endpoint' : bFoundryEndpoint
  
  // Output Endpoint Resolution
  azureInferenceEndpointLogic: shouldProvisionNewAI ? 'ai!.outputs.endpoint' : bFoundryEndpoint
  
  // Expected Endpoint Format Examples
  expectedNewAIFormat: 'https://[env-name]-ai.openai.azure.com/openai/models'
  expectedExistingFormat: 'https://[project-name].openai.azure.com/models'
  
  // Conditional Module Status
  aiModuleExists: shouldProvisionNewAI ? 'YES (will be deployed)' : 'NO (condition false)'
}

// Outputs
output AZURE_LOCATION string = location
output AZURE_RESOURCE_GROUP string = resourceGroup().name

// Outputs required for local development server
output AZURE_TENANT_ID string = tenant().tenantId
output AZURE_AI_CHAT_DEPLOYMENT_NAME string = shouldEnableAI ? effectiveChatDeploymentName : ''
// Search-related outputs archived - search functionality removed
output AZURE_AI_SEARCH_ENDPOINT string = ''
output AZURE_INFERENCE_ENDPOINT string = shouldProvisionNewAI ? ai!.outputs.endpoint : bFoundryEndpoint
output AZURE_AI_AUDIO_DEPLOYMENT_NAME string = shouldEnableAI ? effectiveAudioModelName : ''

// Key Vault outputs archived

// Outputs required by azd for App Service
output SERVICE_API_IDENTITY_PRINCIPAL_ID string = api.outputs.SERVICE_API_IDENTITY_PRINCIPAL_ID
output SERVICE_API_NAME string = api.outputs.SERVICE_API_NAME
output SERVICE_API_URI string = api.outputs.SERVICE_API_URI
output SERVICE_API_ENDPOINTS array = ['${api.outputs.SERVICE_API_URI}']
