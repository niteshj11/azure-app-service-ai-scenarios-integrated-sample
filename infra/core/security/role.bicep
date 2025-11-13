metadata description = 'Creates a role assignment for a given principal and role definition.'

@description('The principal ID to assign the role to')
param principalId string

@description('The role definition ID to assign')
param roleDefinitionId string

@description('The type of principal (User, ServicePrincipal, Group, etc.)')
param principalType string

@description('The resource ID to assign the role to. If not provided, the assignment will be at the current scope.')
param resourceId string = ''

var roleAssignmentName = guid(principalId, roleDefinitionId, resourceId)

resource roleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: roleAssignmentName
  properties: {
    principalId: principalId
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', roleDefinitionId)
    principalType: principalType
  }
}

output id string = roleAssignment.id
