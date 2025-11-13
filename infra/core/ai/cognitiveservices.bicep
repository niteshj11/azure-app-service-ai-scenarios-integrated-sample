metadata description = 'Creates an Azure Cognitive Services instance.'
param aiServiceName string
param aiProjectName string
param location string = resourceGroup().location
param tags object = {}
@description('The custom subdomain name used to access the API. Defaults to the value of the name parameter.')
param customSubDomainName string = aiServiceName
param disableLocalAuth bool = true
param deployments array = []
param appInsightsId string = ''
param appInsightConnectionString string = ''
param appInsightConnectionName string
param storageAccountId string
param storageAccountConnectionName string

@allowed([ 'Enabled', 'Disabled' ])
param publicNetworkAccess string = 'Enabled'
param sku object = {
  name: 'S0'
}

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
  kind: 'AIServices'
  identity: {
    type: 'SystemAssigned'
  }
  tags: tags
  properties: {
    customSubDomainName: customSubDomainName
    networkAcls: networkAcls
    publicNetworkAccess: publicNetworkAccess
    disableLocalAuth: disableLocalAuth 
  }
}

// Creates the Azure Foundry connection to your Azure App Insights resource
resource appInsightConnection 'Microsoft.CognitiveServices/accounts/connections@2023-10-01-preview' = if (!empty(appInsightsId)) {
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

// Creates the Azure Foundry connection to your Azure Storage resource
resource storageAccountConnection 'Microsoft.CognitiveServices/accounts/connections@2023-10-01-preview' = {
  name: storageAccountConnectionName
  parent: account
  properties: {
    category: 'AzureStorageAccount'
    target: storageAccountId
    authType: 'AAD'
    isSharedToAll: true    
    metadata: {
      ApiType: 'Azure'
      ResourceId: storageAccountId
    }
  }
}

resource aiProject 'Microsoft.CognitiveServices/accounts/projects@2023-10-01-preview' = {
  parent: account
  name: aiProjectName
  location: location
  tags: tags  
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    description: 'AI Project for TechMart Chatbot'
    displayName: 'TechMart AI Project'
  }
}

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
output endpoint string = account.properties.endpoint
output projectId string = aiProject.id
output projectEndpoint string = 'https://${account.properties.endpoint}/api/projects/${aiProject.name}'