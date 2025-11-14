// Update App Service with Key Vault references after Key Vault is created
param appServiceName string
param keyVaultName string
param azureInferenceEndpointReference string
param azureInferenceCredentialReference string

// Reference to existing App Service
resource appService 'Microsoft.Web/sites@2022-09-01' existing = {
  name: appServiceName
}

// Update App Service settings with Key Vault references
resource appSettings 'Microsoft.Web/sites/config@2022-09-01' = {
  parent: appService
  name: 'appsettings'
  properties: {
    // Keep existing settings and add Key Vault references
    AZURE_INFERENCE_ENDPOINT: azureInferenceEndpointReference
    AZURE_INFERENCE_CREDENTIAL: azureInferenceCredentialReference
    KEY_VAULT_NAME: keyVaultName
    USE_KEY_VAULT: 'true'
    // Base Flask settings
    RUNNING_IN_PRODUCTION: 'true'
    FLASK_APP: 'app.py'
    FLASK_ENV: 'production'
    PYTHONUNBUFFERED: '1'
    WEBSITE_WEBDEPLOY_USE_SCM: 'true'
    PORT: '8000'
    PYTHONPATH: '/home/site/wwwroot'
    WEBSITES_ENABLE_APP_SERVICE_STORAGE: 'false'
    SCM_DO_BUILD_DURING_DEPLOYMENT: 'true'
    ENABLE_ORYX_BUILD: 'true'
  }
}

output completed bool = true
