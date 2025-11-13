metadata description = 'Creates an Application Insights instance.'
param name string
param location string = resourceGroup().location
param tags object = {}

@description('The resource ID of the Log Analytics workspace to send data to.')
param logAnalyticsWorkspaceId string = ''

@description('The type of Application Insights to create.')
@allowed(['web', 'other'])
param kind string = 'web'

resource applicationInsights 'Microsoft.Insights/components@2020-02-02' = {
  name: name
  location: location
  tags: tags
  kind: kind
  properties: {
    Application_Type: kind
    WorkspaceResourceId: !empty(logAnalyticsWorkspaceId) ? logAnalyticsWorkspaceId : null
    IngestionMode: !empty(logAnalyticsWorkspaceId) ? 'LogAnalytics' : 'ApplicationInsights'
    publicNetworkAccessForIngestion: 'Enabled'
    publicNetworkAccessForQuery: 'Enabled'
  }
}

output id string = applicationInsights.id
output name string = applicationInsights.name
output connectionString string = applicationInsights.properties.ConnectionString
output instrumentationKey string = applicationInsights.properties.InstrumentationKey
