param name string
param location string = resourceGroup().location
param tags object = {}

// Core required parameters
param appServicePlanId string

// Optional feature flags
param enableManagedIdentity bool = false
param enableAIServices bool = false

// Optional resource parameters
// identityName parameter removed - using system-assigned managed identity only
param aiFoundryEndpoint string = ''
param chatDeploymentName string = ''
param audioDeploymentName string = ''
// Embedding and search parameters archived - not used without search functionality
// applicationInsightsName parameter archived - not used in simplified config

// User-assigned managed identity removed - using system-assigned identity only

// Key Vault integration archived - using environment variables with Managed Identity

// Note: Azure AI credentials are now managed by the application via settings page
// No longer passed as Bicep parameters - cleaner separation of infrastructure vs user configuration

// Base environment variables for minimal deployment
var baseEnv = [
  {
    name: 'FLASK_APP'
    value: 'app.py'
  }
  {
    name: 'FLASK_ENV'
    value: 'production'
  }
  {
    name: 'PYTHONUNBUFFERED'
    value: '1'
  }
  {
    name: 'WEBSITE_WEBDEPLOY_USE_SCM'
    value: 'true'
  }
  // Note: PORT removed - controlled by Gunicorn command line (--bind=0.0.0.0:8000)
  {
    name: 'PYTHONPATH'
    value: '/home/site/wwwroot'
  }
  {
    name: 'WEBSITES_ENABLE_APP_SERVICE_STORAGE'
    value: 'false'
  }
  {
    name: 'SCM_DO_BUILD_DURING_DEPLOYMENT'
    value: 'true'
  }
  {
    name: 'ENABLE_ORYX_BUILD'
    value: 'true'
  }
]

// Infrastructure resource identifiers (NOT user credentials)
var infrastructureEnv = [
  // Key Vault environment variables archived
]

// AI-specific environment variables - Always set if AI services enabled OR if we have endpoint/models
var hasAIConfig = enableAIServices || (!empty(aiFoundryEndpoint) || !empty(chatDeploymentName))
var aiEnv = hasAIConfig ? [
  {
    name: 'AZURE_INFERENCE_ENDPOINT'
    value: aiFoundryEndpoint
  }
  {
    name: 'AZURE_CLIENT_ID'
    value: 'system-assigned-managed-identity'
  }
  {
    name: 'AZURE_AI_CHAT_DEPLOYMENT_NAME'
    value: chatDeploymentName
  }
  {
    name: 'AZURE_AI_AUDIO_DEPLOYMENT_NAME'
    value: audioDeploymentName
  }
] : []

// Combined environment variables
var env = concat(concat(baseEnv, aiEnv), infrastructureEnv)

// Convert environment variables to app settings object
var appSettings = reduce(env, {}, (acc, curr) => union(acc, { '${curr.name}': curr.value }))

module app 'core/host/appservice.bicep' = {
  name: 'appservice'
  params: {
    name: name
    location: location
    tags: tags
    appServicePlanId: appServicePlanId
    runtimeName: 'python'
    runtimeVersion: '3.11'
    appCommandLine: 'gunicorn --bind=0.0.0.0:8000 --workers=1 --timeout=600 --preload wsgi:app'
    managedIdentity: enableManagedIdentity
    allowedOrigins: [
      'https://portal.azure.com'
      'https://ms.portal.azure.com'
      'https://ai.azure.com'
    ]
    appSettings: appSettings
    scmDoBuildDuringDeployment: true
    enableOryxBuild: true
    linuxFxVersion: 'PYTHON|3.11'
  }
}

// Debug Output
output DEBUG_API object = {
  enableManagedIdentity: enableManagedIdentity
  identityPrincipalIdLength: enableManagedIdentity ? length(app.outputs.identityPrincipalId) : 0
  // AI Configuration Debug
  enableAIServices: enableAIServices
  hasAIConfig: hasAIConfig
  aiFoundryEndpoint: aiFoundryEndpoint
  chatDeploymentName: chatDeploymentName
  audioDeploymentName: audioDeploymentName
  receivedParameters: {
    aiFoundryEndpoint: aiFoundryEndpoint
    chatDeploymentName: chatDeploymentName
    audioDeploymentName: audioDeploymentName
  }
  // Key Vault outputs archived
}

output SERVICE_API_IDENTITY_PRINCIPAL_ID string = enableManagedIdentity ? app.outputs.identityPrincipalId : ''
output SERVICE_API_NAME string = app.outputs.name
output SERVICE_API_URI string = app.outputs.uri
output SERVICE_API_ENDPOINTS array = [app.outputs.uri]
