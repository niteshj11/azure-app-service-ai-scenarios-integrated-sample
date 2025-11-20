metadata description = 'Creates RBAC assignment for App Service Managed Identity to access existing AI Foundry resources.'

@description('Resource ID of the existing Azure AI Foundry service')
param aiFoundryResourceId string

@description('Principal ID of the App Service Managed Identity')  
param appServicePrincipalId string

// Cognitive Services OpenAI User role definition ID
var cognitiveServicesOpenAIUserRoleId = '5e0bd9bd-7b93-4f28-af87-19fc36ad61bd'

// Generate a unique name for reference
var roleAssignmentName = guid(aiFoundryResourceId, appServicePrincipalId, cognitiveServicesOpenAIUserRoleId)

// Parse the AI service name from the resource ID
var aiServiceName = split(aiFoundryResourceId, '/')[8]

// Reference the existing AI service (we're deploying in the correct scope now)
resource existingAIService 'Microsoft.CognitiveServices/accounts@2023-05-01' existing = {
  name: aiServiceName
}

// Create the actual RBAC assignment
resource rbacAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: roleAssignmentName
  scope: existingAIService
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', cognitiveServicesOpenAIUserRoleId)
    principalId: appServicePrincipalId
    principalType: 'ServicePrincipal'
  }
}

output aiFoundryResourceId string = aiFoundryResourceId
output appServicePrincipalId string = appServicePrincipalId
output roleAssignmentName string = roleAssignmentName
output roleDefinitionId string = subscriptionResourceId('Microsoft.Authorization/roleDefinitions', cognitiveServicesOpenAIUserRoleId)
output rbacInstructions string = 'RBAC assignment created automatically via Bicep deployment'
output rbacAssignmentId string = rbacAssignment.id
