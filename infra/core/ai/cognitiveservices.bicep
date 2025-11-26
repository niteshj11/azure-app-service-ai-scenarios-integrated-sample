metadata description = 'Creates an Azure Cognitive Services instance.'
param aiServiceName string
param location string = resourceGroup().location
param tags object = {}
@description('The custom subdomain name used to access the API. Defaults to the value of the name parameter.')
param customSubDomainName string = aiServiceName
param disableLocalAuth bool = true
param deployments array = []
param appInsightsId string = ''
param appInsightConnectionString string = ''
param appInsightConnectionName string

@allowed([ 'Enabled', 'Disabled' ])
param publicNetworkAccess string = 'Enabled'
param sku object = {
  name: 'S0'
}

@description('Enable multi-service capabilities for vision and audio')
param enableMultiService bool = true

param allowedIpRules array = []
param networkAcls object = empty(allowedIpRules) ? {
  defaultAction: 'Allow'
} : {
  ipRules: allowedIpRules
  defaultAction: 'Deny'
}

resource account 'Microsoft.CognitiveServices/accounts@2023-10-01-preview' = {
  name: aiServiceName
  location: location
  sku: sku
  kind: enableMultiService ? 'AIServices' : 'OpenAI'
  identity: {
    type: 'SystemAssigned'
  }
  tags: tags
  properties: {
    customSubDomainName: customSubDomainName
    networkAcls: networkAcls
    publicNetworkAccess: publicNetworkAccess
    disableLocalAuth: disableLocalAuth
    // Enable multi-service capabilities for vision and audio
    restore: false
    restrictOutboundNetworkAccess: false
  }
}

// Creates the Azure Foundry connection to your Azure App Insights resource
resource appInsightConnection 'Microsoft.CognitiveServices/accounts/connections@2025-04-01-preview' = if (!empty(appInsightsId)) {
  name: appInsightConnectionName
  parent: account
  properties: {
    category: 'AppInsights'
    target: appInsightsId
    authType: 'ApiKey'
    isSharedToAll: true
    credentials: {
      key: appInsightConnectionString
    }
    metadata: {
      ApiType: 'Azure'
      ResourceId: appInsightsId
    }
  }
}

// Storage connection temporarily disabled - not required for basic OpenAI functionality
// resource storageAccountConnection 'Microsoft.CognitiveServices/accounts/connections@2025-04-01-preview' = {
//   name: storageAccountConnectionName
//   parent: account
//   properties: {
//     category: 'AzureStorageAccount'
//     target: storageAccountEndpoint
//     authType: 'AAD'
//     isSharedToAll: true    
//     metadata: {
//       ApiType: 'Azure'
//       ResourceId: storageAccountId
//     }
//   }
// }

// AI Project temporarily disabled - not required for basic OpenAI functionality
// resource aiProject 'Microsoft.CognitiveServices/accounts/projects@2025-04-01-preview' = {
//   parent: account
//   name: aiProjectName
//   location: location
//   tags: tags  
//   identity: {
//     type: 'SystemAssigned'
//   }
//   properties: {
//     description: 'AI Project for TechMart Chatbot'
//     displayName: 'TechMart AI Project'
//   }
// }

@batchSize(1)
resource aiServicesDeployments 'Microsoft.CognitiveServices/accounts/deployments@2023-10-01-preview' = [for deployment in deployments: {
  parent: account
  name: deployment.name
  properties: {
    model: deployment.model
    raiPolicyName: deployment.?raiPolicyName
  }
  sku: deployment.sku
}]

output id string = account.id
output name string = account.name
output endpoint string = '${account.properties.endpoint}models'
// AI Project outputs temporarily disabled
// output projectId string = aiProject.id
// output projectEndpoint string = 'https://${account.properties.endpoint}/api/projects/${aiProject.name}'
