metadata description = 'Creates a role assignment for a resource group.'
@description('The principal id to assign the role to')
param principalId string

@description('The role definition id to assign to the principal')
param roleDefinitionId string

@description('The type of the principal (ServicePrincipal or User)')
@allowed([
  'Device'
  'ForeignGroup'
  'Group'
  'ServicePrincipal'
  'User'
])
param principalType string = 'ServicePrincipal'

resource roleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(subscription().id, resourceGroup().id, principalId, roleDefinitionId)
  properties: {
    principalId: principalId
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', roleDefinitionId)
    principalType: principalType
  }
}

output roleAssignmentId string = roleAssignment.id
