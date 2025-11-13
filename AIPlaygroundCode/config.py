"""
Configuration management for Azure Linux App Service AI Chatbot.

This module handles all configuration settings with Key Vault as the source of truth
for sensitive data (endpoint, API key), App Service settings as fallback,
and JSON file for non-sensitive settings.
"""

import os
import json
import logging
from typing import Optional, Dict, Any
from dataclasses import dataclass, asdict
from pathlib import Path

# Azure Key Vault integration
try:
    from azure.keyvault.secrets import SecretClient
    from azure.identity import DefaultAzureCredential, ManagedIdentityCredential
    from azure.core.exceptions import AzureError
    KEY_VAULT_AVAILABLE = True
except ImportError:
    KEY_VAULT_AVAILABLE = False

# Setup logging
logger = logging.getLogger(__name__)


@dataclass
class UnifiedConfig:
    """Unified configuration for all chatbot settings."""
    
    # Azure AI Connection - Loaded hierarchically: Key Vault > App Settings > JSON > defaults
    endpoint: str = ""
    api_key: str = ""
    api_version: str = "2024-02-15-preview"
    
    # Model Settings - User configurable via settings page
    model: str = "gpt-4o-mini"
    audio_model: str = "gpt-4o-mini-audio-preview"
    max_tokens: int = 2000
    temperature: float = 0.3
    top_p: float = 0.8
    frequency_penalty: float = 0.0
    presence_penalty: float = 0.0
    system_message: str = """You are TechMart Enterprise AI Assistant, a professional customer service and business intelligence AI for TechMart, a leading multi-channel retailer specializing in electronics, fashion, home & garden, books, and sports equipment. 

Your role includes:
- Customer Service: Help customers find products, process orders, handle returns, and resolve issues
- Product Expert: Provide detailed product information, specifications, comparisons, and recommendations
- Business Intelligence: Analyze market trends, sales data, inventory, and provide strategic insights
- Store Operations: Assist with inventory management, visual merchandising, and operational efficiency

Communication Style:
- Professional yet friendly and approachable
- Use clear, concise language appropriate for business context
- Provide specific, actionable recommendations
- Include relevant metrics, pricing, and availability when discussing products
- Escalate complex issues appropriately

Company Context:
- TechMart Enterprise: 500+ stores globally, 50M+ customers, 100K+ SKUs, $5B annual revenue
- Focus on customer experience, data-driven decisions, and operational excellence
- Omnichannel approach combining online and physical retail presence

Sample Product Catalog (Gaming Laptops $1500-2000):
- TechMart Pro Gaming X1: $1699 - RTX 4070, Intel i7-13700H, 16GB RAM, 1TB SSD
- UltraGame Elite 15: $1899 - RTX 4070 Ti, AMD Ryzen 9 7900HX, 32GB RAM, 1TB SSD
- PowerBook Gaming Pro: $1549 - RTX 4060, Intel i5-13600H, 16GB RAM, 512GB SSD

Store Information:
- Business Hours: Monday-Saturday 10AM-9PM, Sunday 11AM-7PM
- Chicago Downtown: 123 Michigan Ave, Phone: (312) 555-TECH
- Services: In-store pickup available, same-day delivery in metro areas
- Customer Service: For order tracking, direct customers to online portal or call 1-800-TECHMART

Order Management:
- For order inquiries, explain that customers can track orders online at techmart.com/orders or call customer service
- Standard shipping: 3-5 business days, Express: 1-2 business days
- Return policy: 30-day return window with receipt

Always maintain customer confidentiality and follow enterprise data handling policies."""
    
    # Advanced Features
    enable_multimodal: bool = True
    max_image_size: int = 5  # MB
    max_audio_size: int = 10  # MB
    
    enable_reasoning: bool = True
    reasoning_effort: str = "medium"  # low, medium, high
    show_reasoning: bool = True
    
    enable_structured_output: bool = True
    response_format: str = "text"  # text, json_object, json_schema
    json_schema: str = ""
    schema_name: str = "Response"
    
    # Application Settings (not editable via UI)
    secret_key: str = "dev-secret-key-change-in-production"
    debug: bool = True
    host: str = "127.0.0.1"
    port: int = 5000
    max_content_length: int = 50 * 1024 * 1024  # 50MB
    upload_folder: str = "AIPlaygroundCode/uploads"
    session_timeout: int = 3600
    log_level: str = "INFO"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)
    
    def update_from_dict(self, data: Dict[str, Any]) -> None:
        """Update configuration from dictionary."""
        for key, value in data.items():
            if hasattr(self, key):
                # Handle type conversion
                field_type = type(getattr(self, key))
                if field_type == bool:
                    # Handle checkbox values (can be 'on', '1', True, etc.)
                    setattr(self, key, value in ['on', '1', 'true', True, 1])
                elif field_type in [int, float]:
                    try:
                        setattr(self, key, field_type(value) if value else getattr(self, key))
                    except (ValueError, TypeError):
                        pass  # Keep original value if conversion fails
                else:
                    setattr(self, key, str(value) if value is not None else "")
    
    def is_azure_configured(self) -> bool:
        """Check if Azure configuration is complete."""
        return bool(self.endpoint and self.endpoint.strip() and 
                   self.api_key and self.api_key.strip())
    
    def get_model_params(self) -> Dict[str, Any]:
        """Get parameters for Azure AI API calls."""
        # Base parameters supported by most Azure AI models
        params = {
            'model': self.model,
            'max_tokens': self.max_tokens,
            'temperature': self.temperature,
            'top_p': self.top_p,
            'frequency_penalty': self.frequency_penalty,
            'presence_penalty': self.presence_penalty
        }
        
        # Add response format if structured output is enabled
        if self.enable_structured_output and self.response_format != "text":
            if self.response_format == "json_object":
                params['response_format'] = {"type": "json_object"}
            elif self.response_format == "json_schema" and self.json_schema:
                try:
                    schema = json.loads(self.json_schema)
                    params['response_format'] = {
                        "type": "json_schema",
                        "json_schema": {
                            "name": self.schema_name or "Response",
                            "schema": schema
                        }
                    }
                except json.JSONDecodeError:
                    pass  # Fall back to text format if schema is invalid
        
        return params
    
    def get_reasoning_params(self) -> Dict[str, Any]:
        """Get parameters specifically for reasoning models."""
        params = self.get_model_params()
        
        # Add reasoning-specific parameters if enabled
        if self.enable_reasoning:
            # Note: reasoning_effort might not be supported by all models
            # This is model-dependent and should be handled by specific scenarios
            pass
        
        return params


class KeyVaultClient:
    """Client for accessing Azure Key Vault secrets with intelligent initialization."""
    
    def __init__(self, key_vault_name: Optional[str] = None, is_production: bool = True):
        # Auto-detect Key Vault name from multiple sources
        self.key_vault_name = (
            key_vault_name or 
            os.getenv('AZURE_KEY_VAULT_NAME') or 
            os.getenv('KEY_VAULT_NAME') or
            self._extract_keyvault_name_from_env()
        )
        
        self.is_production = is_production
        self.client = None
        
        # Initialize Key Vault client if available and needed
        if self._should_initialize_keyvault():
            self._initialize_client()
        else:
            reason = self._get_skip_reason()
            logger.info(f"Key Vault client not initialized: {reason}")
    
    def _extract_keyvault_name_from_env(self) -> str:
        """Extract Key Vault name from Key Vault reference strings in environment variables."""
        # Check common environment variables for Key Vault references
        env_vars_to_check = [
            'AZURE_INFERENCE_ENDPOINT',
            'AZURE_INFERENCE_CREDENTIAL', 
            'AZURE_OPENAI_ENDPOINT',
            'AZURE_OPENAI_KEY'
        ]
        
        for env_var in env_vars_to_check:
            value = os.getenv(env_var, '')
            if value.startswith('@Microsoft.KeyVault(VaultName='):
                # Extract vault name from: @Microsoft.KeyVault(VaultName=mykeyvault;SecretName=mysecret)
                try:
                    start = value.find('VaultName=') + len('VaultName=')
                    end = value.find(';', start)
                    if end == -1:
                        end = value.find(')', start)
                    vault_name = value[start:end]
                    logger.info(f"Extracted Key Vault name from {env_var}: {vault_name}")
                    return vault_name
                except Exception as e:
                    logger.debug(f"Failed to extract Key Vault name from {env_var}: {e}")
        
        return ''
    
    def _should_initialize_keyvault(self) -> bool:
        """Determine if Key Vault client should be initialized."""
        return (
            KEY_VAULT_AVAILABLE and 
            self.key_vault_name and 
            self.is_production
        )
    
    def _get_skip_reason(self) -> str:
        """Get human-readable reason why Key Vault initialization was skipped."""
        if not KEY_VAULT_AVAILABLE:
            return "Azure Key Vault SDK not available"
        elif not self.key_vault_name:
            return "No Key Vault name found"
        elif not self.is_production:
            return "Local development mode"
        else:
            return "Unknown reason"
    
    def _initialize_client(self) -> None:
        """Initialize the Key Vault client."""
        try:
            # Use DefaultAzureCredential which works with managed identity in Azure
            credential = DefaultAzureCredential()
            key_vault_url = f"https://{self.key_vault_name}.vault.azure.net/"
            self.client = SecretClient(vault_url=key_vault_url, credential=credential)
            logger.info(f"Key Vault client initialized: {self.key_vault_name}")
        except Exception as e:
            logger.warning(f"Failed to initialize Key Vault client for {self.key_vault_name}: {e}")
            self.client = None
    
    def get_secret(self, secret_name: str) -> Optional[str]:
        """Get a secret from Key Vault."""
        if not self.client:
            return None
            
        try:
            secret = self.client.get_secret(secret_name)
            logger.info(f"Successfully retrieved secret: {secret_name}")
            return secret.value
        except AzureError as e:
            logger.warning(f"Failed to get secret '{secret_name}' from Key Vault: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error getting secret '{secret_name}': {e}")
            return None
    
    def set_secret(self, secret_name: str, secret_value: str) -> bool:
        """Set a secret in Key Vault."""
        if not self.client:
            return False
            
        try:
            self.client.set_secret(secret_name, secret_value)
            logger.info(f"Successfully set secret: {secret_name}")
            return True
        except AzureError as e:
            logger.warning(f"Failed to set secret '{secret_name}' in Key Vault: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error setting secret '{secret_name}': {e}")
            return False


class ConfigManager:
    """Manages configuration with intelligent environment auto-detection."""
    
    def __init__(self, config_file: str = None):
        # Auto-detect environment and config file
        self.is_production = self._detect_production_environment()
        
        if config_file is None:
            config_file = self._detect_config_file()
        
        self.config_file = Path(config_file)
        self.config = UnifiedConfig()
        
        # Log detected environment and config file
        env_type = "PRODUCTION" if self.is_production else "LOCAL"
        logger.info(f"Auto-detected environment: {env_type}")
        logger.info(f"Using config file: {self.config_file}")
        
        # Initialize Key Vault with production flag
        if self.is_production:
            self.key_vault = KeyVaultClient(is_production=self.is_production)
        else:
            self.key_vault = None
            
        self._load_config()
        self._ensure_upload_folder()
    
    def _detect_production_environment(self) -> bool:
        """
        Clean environment detection - determines if running in Azure (production) or local mode.
        
        Detection logic (in priority order):
        1. Azure App Service runtime indicators (automatic)
        2. Azure infrastructure resource indicators (set by Bicep)
        3. Azure Managed Identity indicators (automatic)
        4. Explicit overrides (manual control if needed)
        5. Default to local development
        """
        # 1. Azure App Service Runtime Indicators (Automatic)
        azure_app_service_indicators = [
            'WEBSITE_INSTANCE_ID',      # Unique instance identifier
            'WEBSITE_SITE_NAME',        # Your app service name
            'WEBSITE_RESOURCE_GROUP',   # Resource group name
            'SERVER_SOFTWARE',          # Azure-specific server software
        ]
        
        for indicator in azure_app_service_indicators:
            if os.getenv(indicator):
                logger.info(f"Azure App Service detected ({indicator}={os.getenv(indicator)})")
                return True
        
        # 2. Azure Infrastructure Resource Indicators (Set by Bicep)
        azure_infrastructure_indicators = [
            'AZURE_KEY_VAULT_NAME',     # Key Vault created by Bicep
            'ENABLE_KEY_VAULT',         # Key Vault enabled flag from Bicep
        ]
        
        for indicator in azure_infrastructure_indicators:
            value = os.getenv(indicator)
            if value and value.lower() != 'false':
                logger.info(f"Azure infrastructure detected ({indicator}={value})")
                return True
        
        # 3. Azure Managed Identity Indicators (Automatic)
        azure_identity_indicators = [
            'MSI_ENDPOINT',             # Managed Service Identity endpoint
            'MSI_SECRET',               # Managed Service Identity secret
            'IDENTITY_ENDPOINT',        # Azure Identity endpoint (newer)
            'IDENTITY_HEADER',          # Azure Identity header (newer)
        ]
        
        for indicator in azure_identity_indicators:
            if os.getenv(indicator):
                logger.info(f"Azure Managed Identity detected ({indicator} present)")
                return True
        
        # 4. Explicit Override (Manual Control)
        explicit_override = os.getenv('FORCE_ENVIRONMENT', '').lower()
        if explicit_override == 'azure':
            logger.info("Explicit override: FORCE_ENVIRONMENT=azure")
            return True
        elif explicit_override == 'local':
            logger.info("Explicit override: FORCE_ENVIRONMENT=local")
            return False
        
        # 5. Default to Local Development Mode
        logger.info("No Azure indicators found - defaulting to local development")
        return False
    
    def _detect_config_file(self) -> str:
        """
        Intelligently detect which config file to use based on availability and environment.
        
        Detection logic:
        1. In production: Always use settings.json (settings.local.json excluded from deployment)
        2. In local development: Use settings.local.json if exists, otherwise settings.json
        """
        if self.is_production:
            # Production: Always use settings.json (local files not deployed)
            return 'AIPlaygroundCode/settings.json'
        else:
            # Local development: Prefer local settings if available
            if Path('AIPlaygroundCode/settings.local.json').exists():
                logger.info("Found settings.local.json - using for local development")
                return 'AIPlaygroundCode/settings.local.json'
            else:
                logger.info("settings.local.json not found - using settings.json")
                return 'AIPlaygroundCode/settings.json'
    
    def _load_config(self) -> None:
        """Load configuration with intelligent environment-aware strategy."""
        logger.info(f"Loading configuration - Production mode: {self.is_production}")
        
        if self.is_production:
            # PRODUCTION MODE: Sensitive data from Key Vault, others from JSON/env
            self._load_production_config()
        else:
            # LOCAL DEVELOPMENT MODE: All settings from JSON file
            self._load_local_config()
        
        # Post-load validation and smart environment re-detection
        self._validate_and_adjust_environment()
        
        logger.info(f"Configuration loaded - Endpoint configured: {bool(self.config.endpoint)}, API Key configured: {bool(self.config.api_key)}")
    
    def _validate_and_adjust_environment(self) -> None:
        """
        Validate configuration after loading to ensure consistency.
        
        After cleanup - this mainly validates that we have credentials configured,
        since Azure/Key Vault references are no longer automatically set by Bicep.
        """
        has_direct_credentials = (
            self.config.endpoint and 
            self.config.api_key and 
            self.config.endpoint.strip() and
            self.config.api_key.strip()
        )
        
        # Log configuration status
        if has_direct_credentials:
            source = "Key Vault" if self.is_production else "settings file"
            logger.info(f"Azure AI credentials loaded from {source}")
        else:
            if self.is_production:
                logger.warning("Azure environment detected but no credentials found - configure via settings page")
            else:
                logger.info("Local environment - configure credentials via settings.json or settings page")
    
    def _load_production_config(self) -> None:
        """Load configuration for production: Key Vault for sensitive, JSON for others."""
        # First: Load non-sensitive settings from settings.json
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # Only load non-sensitive data from JSON in production
                    sensitive_keys = {'endpoint', 'api_key'}
                    non_sensitive_data = {k: v for k, v in data.items() if k not in sensitive_keys}
                    self.config.update_from_dict(non_sensitive_data)
                    logger.info("Loaded non-sensitive configuration from settings.json")
            except (json.JSONDecodeError, FileNotFoundError, PermissionError) as e:
                logger.warning(f"Could not load settings.json: {e}")
        
        # Second: Load sensitive data from Key Vault (PRIMARY SOURCE)
        self._load_from_key_vault()
        
        # Third: Fallback to App Service settings (environment variables)
        if not self.config.endpoint or not self.config.api_key:
            self._load_from_environment()
    
    def _load_local_config(self) -> None:
        """Load configuration for local development: All settings from JSON file."""
        # Load all settings from settings.json (including sensitive data)
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.config.update_from_dict(data)
                    logger.info("Loaded all configuration from settings.json (local mode)")
            except (json.JSONDecodeError, FileNotFoundError, PermissionError) as e:
                logger.warning(f"Could not load settings.json: {e}")
        
        # Fallback to environment variables and .env file for local development
        if not self.config.endpoint or not self.config.api_key:
            self._load_from_environment()
            
        if not self.config.endpoint or not self.config.api_key:
            self._try_migrate_from_env()
    
    def _load_from_key_vault(self) -> None:
        """Load sensitive configuration from Azure Key Vault (production only)."""
        if not self.key_vault or not self.key_vault.client:
            logger.info("Key Vault not available, skipping Key Vault configuration load")
            return
        
        try:
            # Try to get endpoint from Key Vault using the actual secret names we created
            endpoint = self.key_vault.get_secret('AZURE-AI-ENDPOINT')
            if endpoint:
                self.config.endpoint = endpoint
                logger.info("Loaded Azure AI endpoint from Key Vault")
            
            # Try to get API key from Key Vault using the actual secret names we created
            api_key = self.key_vault.get_secret('AZURE-AI-KEY')
            if api_key:
                self.config.api_key = api_key
                logger.info("Loaded Azure AI API key from Key Vault")
                
        except Exception as e:
            logger.warning(f"Error loading from Key Vault: {e}")
    
    def _load_from_environment(self) -> None:
        """Load Azure credentials from environment variables."""
        # Check for Azure AI Inference credentials
        azure_endpoint = os.getenv('AZURE_INFERENCE_ENDPOINT')
        azure_credential = os.getenv('AZURE_INFERENCE_CREDENTIAL')
        
        # Check for legacy Azure OpenAI credentials
        if not azure_endpoint:
            azure_endpoint = os.getenv('AZURE_OPENAI_ENDPOINT')
        if not azure_credential:
            azure_credential = os.getenv('AZURE_OPENAI_KEY') or os.getenv('AZURE_OPENAI_API_KEY')
        
        # In production, skip Key Vault reference strings - let Azure resolve them
        if self.is_production and azure_endpoint and azure_endpoint.startswith('@Microsoft.KeyVault'):
            logger.info("Skipping Key Vault reference string in production - let Azure handle resolution")
            return
        
        # Update config if environment variables are found and not Key Vault references
        if azure_endpoint and azure_credential:
            # Ensure we don't use Key Vault reference strings directly
            if not azure_endpoint.startswith('@Microsoft.KeyVault') and not azure_credential.startswith('@Microsoft.KeyVault'):
                self.config.endpoint = azure_endpoint
                self.config.api_key = azure_credential
                logger.info("Loaded Azure credentials from environment variables")
    
    def _try_migrate_from_env(self) -> None:
        """Try to migrate settings from .env file for backward compatibility."""
        try:
            from dotenv import load_dotenv
            load_dotenv()
            
            endpoint = os.getenv('AZURE_INFERENCE_ENDPOINT')
            api_key = os.getenv('AZURE_INFERENCE_CREDENTIAL')
            
            if endpoint and api_key:
                self.config.endpoint = endpoint
                self.config.api_key = api_key
                self.save_config()  # Save migrated settings
        except ImportError:
            pass  # dotenv not available, skip migration
    
    def _ensure_upload_folder(self) -> None:
        """Ensure upload folder exists."""
        upload_path = Path(self.config.upload_folder)
        upload_path.mkdir(exist_ok=True)
    
    def save_config(self) -> bool:
        """Save configuration with environment-aware storage strategy."""
        success = True
        
        if self.is_production:
            # PRODUCTION MODE: Sensitive data to Key Vault, others to JSON
            success = self._save_production_config()
        else:
            # LOCAL DEVELOPMENT MODE: All settings to JSON file
            success = self._save_local_config()
        
        return success
    
    def _save_production_config(self) -> bool:
        """Save configuration for production: Key Vault for sensitive, JSON for others."""
        success = True
        
        # Save sensitive data to Key Vault
        if self.key_vault and self.key_vault.client:
            try:
                if self.config.endpoint:
                    if not self.key_vault.set_secret('AZURE-AI-ENDPOINT', self.config.endpoint):
                        success = False
                        
                if self.config.api_key:
                    if not self.key_vault.set_secret('AZURE-AI-KEY', self.config.api_key):
                        success = False
                        
                logger.info("Saved sensitive configuration to Key Vault")
            except Exception as e:
                logger.error(f"Failed to save to Key Vault: {e}")
                success = False
        else:
            logger.warning("Key Vault not available, sensitive data not saved")
            success = False
        
        # Save non-sensitive configuration to JSON file
        try:
            config_dict = self.config.to_dict()
            # Remove sensitive keys from JSON storage in production
            sensitive_keys = {'endpoint', 'api_key'}
            non_sensitive_dict = {k: v for k, v in config_dict.items() if k not in sensitive_keys}
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(non_sensitive_dict, f, indent=2)
            logger.info("Saved non-sensitive configuration to settings.json")
        except (PermissionError, OSError) as e:
            logger.error(f"Failed to save settings.json: {e}")
            success = False
        
        return success
    
    def _save_local_config(self) -> bool:
        """Save configuration for local development: All settings to JSON file."""
        try:
            config_dict = self.config.to_dict()
            # Save all settings including sensitive data in local mode
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config_dict, f, indent=2)
            logger.info("Saved all configuration to settings.json (local mode)")
            return True
        except (PermissionError, OSError) as e:
            logger.error(f"Failed to save settings.json: {e}")
            return False
    
    def update_config(self, **kwargs) -> bool:
        """Update configuration and save appropriately (Key Vault for sensitive, JSON for non-sensitive)."""
        # Check if we're updating sensitive data
        sensitive_keys = {'endpoint', 'api_key'}
        has_sensitive_update = any(key in sensitive_keys for key in kwargs.keys())
        
        # Update the config object
        old_endpoint = self.config.endpoint
        old_api_key = self.config.api_key
        
        self.config.update_from_dict(kwargs)
        
        # Log configuration validation
        if has_sensitive_update:
            logger.info(f"Configuration update includes sensitive data")
            if not self.config.endpoint.strip():
                logger.warning("Endpoint is empty after update")
            if not self.config.api_key.strip():
                logger.warning("API key is empty after update")
        
        return self.save_config()
    
    def get_config(self) -> UnifiedConfig:
        """Get current configuration."""
        return self.config
    
    def is_configured(self) -> bool:
        """Check if Azure configuration is complete."""
        return self.config.is_azure_configured()
    
    def reset_to_defaults(self) -> bool:
        """Reset configuration to defaults but preserve environment variables."""
        # Store current Azure credentials if they exist
        current_endpoint = self.config.endpoint
        current_api_key = self.config.api_key
        
        # Reset to defaults
        self.config = UnifiedConfig()
        
        # Reload from environment variables to preserve Azure credentials
        self._load_from_environment()
        
        # If no environment credentials, but we had working credentials before, keep them
        if not self.config.is_azure_configured() and current_endpoint and current_api_key:
            self.config.endpoint = current_endpoint
            self.config.api_key = current_api_key
        
        return self.save_config()


# Global configuration manager
config_manager = ConfigManager()


def get_model_config() -> UnifiedConfig:
    """Get current unified configuration (for backward compatibility)."""
    return config_manager.get_config()


def update_model_config(**kwargs) -> bool:
    """Update model configuration parameters."""
    return config_manager.update_config(**kwargs)


def is_configured() -> bool:
    """Check if Azure configuration is properly set up."""
    return config_manager.is_configured()


def get_azure_config() -> tuple:
    """Get Azure connection details."""
    config = config_manager.get_config()
    return config.endpoint, config.api_key, config.api_version


# Application configuration for Flask
@dataclass
class AppConfig:
    """Flask application configuration."""
    
    def __init__(self):
        config = config_manager.get_config()
        self.secret_key = config.secret_key
        self.debug = config.debug
        self.host = config.host
        self.port = config.port
        self.max_content_length = config.max_content_length
        self.upload_folder = config.upload_folder
        self.session_timeout = config.session_timeout
        self.log_level = config.log_level
        
        # Allowed file extensions
        self.allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'mp3', 'wav', 'mp4', 'webm', 'ogg'}
    
    def allowed_file(self, filename: str) -> bool:
        """Check if file extension is allowed."""
        return ('.' in filename and 
                filename.rsplit('.', 1)[1].lower() in self.allowed_extensions)


# Global app config
app_config = AppConfig()