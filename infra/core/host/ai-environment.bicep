@minLength(1)
@description('Primary location for all resources')
param location string

@description('The AI Project resource name.')
param aiProjectName string
@description('The Storage Account resource name.')
param storageAccountName string
@description('The AI Services resource name.')
param aiServicesName string
@description('The AI Services model deployments.')
param aiServiceModelDeployments array = []
@description('The Application Insights connection name.')
param appInsightConnectionName string
@description('Enable multi-service AI capabilities for vision and audio')
param enableMultiServiceAI bool = true
param tags object = {}

module storageAccount '../storage/storage-account.bicep' = {
  name: 'storageAccount'
  params: {
    location: location
    tags: tags
    name: storageAccountName
    containers: [
      {
        name: 'default'
      }
    ]
    files: [
      {
        name: 'default'
      }
    ]
    queues: [
      {
        name: 'default'
      }
    ]
    tables: [
      {
        name: 'default'
      }
    ]
  }
}

// Simplified AI Services deployment without Application Insights dependency
// Application Insights can be added later if monitoring is required
module aiServices '../ai/cognitiveservices.bicep' = {
  name: 'aiServices'
  params: {
    location: location
    tags: tags
    aiServiceName: aiServicesName
    aiProjectName: aiProjectName
    deployments: aiServiceModelDeployments
    appInsightsId: ''
    appInsightConnectionString: ''
    appInsightConnectionName: appInsightConnectionName
    storageAccountId: storageAccount.outputs.id
    storageAccountConnectionName: 'storage-connection'
    enableMultiService: enableMultiServiceAI
  }
}

output projectId string = aiServices.outputs.projectId
output projectEndpoint string = aiServices.outputs.projectEndpoint
output storageAccountId string = storageAccount.outputs.id
