metadata description = 'Creates an Azure App Service Plan'
param name string
param location string = resourceGroup().location
param tags object = {}

@description('The pricing tier for the hosting plan.')
param sku object = {
  name: 'B1'
  capacity: 1
}

@description('The operating system the app service plan should target.')
@allowed([
  'windows'
  'linux'
])
param kind string = 'linux'

@description('True if the App Service Plan should be reserved (Linux), false otherwise.')
param reserved bool = true

resource appServicePlan 'Microsoft.Web/serverfarms@2022-09-01' = {
  name: name
  location: location
  tags: tags
  sku: sku
  kind: kind
  properties: {
    reserved: reserved
  }
}

output id string = appServicePlan.id
output name string = appServicePlan.name
