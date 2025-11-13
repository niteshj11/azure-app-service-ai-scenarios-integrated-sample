param name string
param location string = resourceGroup().location
param tags object = {}

// Core required parameters
param appServicePlanId string

// Optional feature flags
param enableManagedIdentity bool = false
param enableAIServices bool = false

// Optional resource parameters
param identityName string = ''
param azureExistingAIProjectResourceId string = ''
param chatDeploymentName string = ''
param embeddingDeploymentName string = ''
param aiSearchIndexName string = ''
param embeddingDeploymentDimensions string = ''
param searchServiceEndpoint string = ''
param enableAzureMonitorTracing bool = false
param azureTracingGenAIContentRecordingEnabled bool = false
param projectEndpoint string = ''
param applicationInsightsName string = ''

resource apiIdentity 'Microsoft.ManagedIdentity/userAssignedIdentities@2023-01-31' = if (enableManagedIdentity) {
  name: identityName
  location: location
}

// Key Vault integration parameters (infrastructure resources only)
param enableKeyVault bool = false
param keyVaultName string = ''

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
  {
    name: 'AZURE_KEY_VAULT_NAME'
    value: keyVaultName
  }
  {
    name: 'ENABLE_KEY_VAULT'
    value: string(enableKeyVault)
  }
]

// AI-specific environment variables
var aiEnv = enableAIServices ? [
  {
    name: 'AZURE_EXISTING_AIPROJECT_RESOURCE_ID'
    value: azureExistingAIProjectResourceId
  }
  {
    name: 'AZURE_AI_CHAT_DEPLOYMENT_NAME'
    value: chatDeploymentName
  }
  {
    name: 'AZURE_AI_EMBED_DEPLOYMENT_NAME'
    value: embeddingDeploymentName
  }
  {
    name: 'AZURE_AI_SEARCH_INDEX_NAME'
    value: aiSearchIndexName
  }
  {
    name: 'AZURE_AI_EMBED_DIMENSIONS'
    value: embeddingDeploymentDimensions
  }
  {
    name: 'AZURE_AI_SEARCH_ENDPOINT'
    value: searchServiceEndpoint
  }
  {
    name: 'ENABLE_AZURE_MONITOR_TRACING'
    value: string(enableAzureMonitorTracing)
  }
  {
    name: 'AZURE_TRACING_GEN_AI_CONTENT_RECORDING_ENABLED'
    value: string(azureTracingGenAIContentRecordingEnabled)
  }
  {
    name: 'AZURE_EXISTING_AIPROJECT_ENDPOINT'
    value: projectEndpoint
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
  enableKeyVault: enableKeyVault
  keyVaultName: keyVaultName
}

output SERVICE_API_IDENTITY_PRINCIPAL_ID string = enableManagedIdentity ? app.outputs.identityPrincipalId : ''
output SERVICE_API_NAME string = app.outputs.name
output SERVICE_API_URI string = app.outputs.uri
output SERVICE_API_ENDPOINTS array = [app.outputs.uri]
