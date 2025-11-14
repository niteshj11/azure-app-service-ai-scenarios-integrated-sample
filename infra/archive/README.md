# Archived Infrastructure Files

This folder contains Bicep templates and ARM templates that are not currently used in the active deployment pipeline.

## Files Moved to Archive

### `api-update.bicep`
- **Reason**: Not referenced by any active Bicep template
- **Description**: Appears to be an alternative API deployment template
- **Status**: Safe to archive - not part of current deployment flow

### `managed-identity.bicep`
- **Reason**: Not referenced by any active Bicep template
- **Description**: Standalone managed identity template (identity creation is now handled within other templates)
- **Status**: Safe to archive - managed identity creation integrated into main templates

### `main.json`
- **Reason**: Auto-generated ARM template from main.bicep compilation
- **Description**: Compiled JSON ARM template (can be regenerated from main.bicep)
- **Status**: Safe to archive - can be regenerated with `az bicep build --file main.bicep`

### `search/` (folder)
- **Reason**: Optional feature - Azure AI Search for RAG scenarios
- **Description**: Contains search-services.bicep for Azure AI Search deployment
- **Status**: Safe to archive - not required for core AI Foundry functionality

## Active Infrastructure Files (Remaining)

The following files remain active and support the core deployment requirements (App Service, App Service Plan, Key Vault, Managed Identity, AI Foundry):

### Root Level
- `main.bicep` - Main deployment template
- `api.bicep` - App Service deployment
- `abbreviations.json` - Resource naming abbreviations

### Core Modules
- `core/host/ai-environment.bicep` - Azure AI Foundry deployment
- `core/host/appservice.bicep` - App Service configuration  
- `core/host/appservice-appsettings.bicep` - App Service settings
- `core/host/appserviceplan.bicep` - App Service Plan
- `core/security/keyvault.bicep` - Key Vault deployment
- `core/security/keyvault-secrets.bicep` - Key Vault secrets management
- `core/security/role.bicep` - RBAC role assignments
- `core/ai/cognitiveservices.bicep` - Azure AI services
- `core/ai/existing-ai-rbac.bicep` - RBAC for existing AI services

- `core/storage/storage-account.bicep` - Storage account for AI services
- `core/monitor/loganalytics.bicep` - Log Analytics workspace
- `core/monitor/applicationinsights.bicep` - Application Insights

## Restoration Notes

If any archived file is needed again:
1. Move the file back to its original location
2. Update references in calling templates
3. Test deployment to ensure functionality