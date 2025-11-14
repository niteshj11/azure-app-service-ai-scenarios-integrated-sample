metadata description = 'Creates RBAC role assignment for App Service Managed Identity to access existing AI Foundry resources using deployment script.'

@description('Resource ID of the existing Azure AI Foundry service')
param aiFoundryResourceId string

@description('Principal ID of the App Service Managed Identity')  
param appServicePrincipalId string

// Cognitive Services OpenAI User role definition ID
var cognitiveServicesOpenAIUserRoleId = '5e0bd9bd-7b93-4f28-af87-19fc36ad61bd'

// Use deployment script to create cross-resource-group role assignment
resource rbacDeploymentScript 'Microsoft.Resources/deploymentScripts@2023-08-01' = {
  name: 'rbac-assignment-script'
  location: resourceGroup().location
  kind: 'AzureCLI'
  properties: {
    azCliVersion: '2.52.0'
    timeout: 'PT10M'
    retentionInterval: 'P1D'
    environmentVariables: [
      {
        name: 'PRINCIPAL_ID'
        value: appServicePrincipalId
      }
      {
        name: 'SCOPE'
        value: aiFoundryResourceId
      }
      {
        name: 'ROLE_ID'
        value: cognitiveServicesOpenAIUserRoleId
      }
    ]
    scriptContent: '''
      echo "Creating role assignment..."
      echo "Principal ID: $PRINCIPAL_ID"
      echo "Scope: $SCOPE"
      echo "Role ID: $ROLE_ID"
      
      # Create role assignment
      az role assignment create --role $ROLE_ID --assignee $PRINCIPAL_ID --scope $SCOPE
      
      echo "Role assignment created successfully"
    '''
  }
}

output aiFoundryResourceId string = aiFoundryResourceId
output appServicePrincipalId string = appServicePrincipalId
output roleAssignmentStatus string = 'RBAC assignment created via deployment script'
output deploymentScriptResult string = rbacDeploymentScript.properties.outputs.result
