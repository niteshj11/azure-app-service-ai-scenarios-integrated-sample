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
@description('The Log Analytics resource name.')
param logAnalyticsName string = ''
@description('The Application Insights resource name.')
param applicationInsightsName string = ''
@description('The Azure Search resource name.')
param searchServiceName string = ''
@description('The Application Insights connection name.')
param appInsightConnectionName string
param tags object = {}
param runnerPrincipalId string
param runnerPrincipalType string

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

module logAnalytics '../monitor/loganalytics.bicep' = if (!empty(logAnalyticsName)) {
  name: 'logAnalytics'
  params: {
    location: location
    tags: tags
    name: logAnalyticsName
  }
}

module applicationInsights '../monitor/applicationinsights.bicep' = if (!empty(applicationInsightsName)) {
  name: 'applicationInsights'
  params: {
    location: location
    tags: tags
    name: applicationInsightsName
    logAnalyticsWorkspaceId: !empty(logAnalyticsName) ? logAnalytics.outputs.id : ''
  }
}

module aiServices '../ai/cognitiveservices.bicep' = {
  name: 'aiServices'
  params: {
    location: location
    tags: tags
    aiServiceName: aiServicesName
    aiProjectName: aiProjectName
    deployments: aiServiceModelDeployments
    appInsightsId: !empty(applicationInsightsName) ? applicationInsights.outputs.id : ''
    appInsightConnectionString: !empty(applicationInsightsName) ? applicationInsights.outputs.connectionString : ''
    appInsightConnectionName: appInsightConnectionName
    storageAccountId: storageAccount.outputs.id
    storageAccountConnectionName: 'storage-connection'
  }
}

output projectId string = aiServices.outputs.projectId
output projectEndpoint string = aiServices.outputs.projectEndpoint
output storageAccountId string = storageAccount.outputs.id
