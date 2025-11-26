metadata description = 'Creates a role assignment for a given principal and role definition.'

@description('The principal ID to assign the role to')
param principalId string

@description('The role definition ID to assign')
param roleDefinitionId string

@description('The type of principal (User, ServicePrincipal, Group, etc.)')
param principalType string

@description('The AI resource ID to assign the role to.')
param targetResourceId string

var roleAssignmentName = guid(principalId, roleDefinitionId, targetResourceId, resourceGroup().id)

// Extract resource information from the full resource ID
var resourceParts = split(targetResourceId, '/')
var aiAccountName = last(resourceParts)

// Reference the existing AI resource
resource aiAccount 'Microsoft.CognitiveServices/accounts@2023-10-01-preview' existing = {
  name: aiAccountName
}

resource roleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: roleAssignmentName
  scope: aiAccount
  properties: {
    principalId: principalId
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', roleDefinitionId)
    principalType: principalType
  }
}

output id string = roleAssignment.id
