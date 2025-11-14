# Key Vault Archive

This folder contains Key Vault related Bicep files that were removed from the main infrastructure.

## Archived Files

- `keyvault.bicep` - Main Key Vault resource provisioning
- `keyvault-secrets.bicep` - Key Vault secrets management

## Why Archived?

The application now uses Managed Identity with environment variables for configuration, eliminating the need for Key Vault:

- **Simpler Architecture**: Direct environment variable access vs Key Vault SDK calls
- **Better Performance**: No additional network calls to retrieve secrets
- **Reduced Complexity**: Fewer infrastructure components to manage
- **Cost Optimization**: No Key Vault resource costs
- **Managed Identity**: Built-in authentication without API keys

## Configuration Flow (New Approach)

1. **Infrastructure (Bicep)**: Sets App Service environment variables
2. **Application (config.py)**: Reads from environment variables
3. **Settings UI**: Displays configuration via config.py properties

## Restoration (If Needed)

To restore Key Vault functionality:

1. Move files back to `infra/core/security/`
2. Uncomment Key Vault modules in `main.bicep`
3. Add Key Vault parameters back to `api.bicep`
4. Update application code to use Key Vault SDK