"""
Configuration management for Azure Linux App Service AI Chatbot with Managed Identity.

This module handles all configuration settings with Azure Managed Identity authentication
eliminating the need for API keys. Configuration sources in priority order:
1. Environment variables (Azure App Service settings)
2. Local settings.json file for development
"""

import os
import json
import logging
from typing import Dict, Any, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path

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
    model: str = ""
    audio_model: str = ""
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
        import os
        
        # Check if using managed identity
        is_managed_identity = os.getenv('AZURE_CLIENT_ID') == 'system-assigned-managed-identity'
        
        if is_managed_identity:
            # For managed identity, we only need endpoint
            return bool(self.endpoint and self.endpoint.strip())
        else:
            # For API key authentication, we need both endpoint and API key
            return bool(self.endpoint and self.endpoint.strip() and 
                       self.api_key and self.api_key.strip())
    
    def is_using_managed_identity(self) -> bool:
        """Check if currently using Azure Managed Identity."""
        import os
        return (
            os.getenv('WEBSITE_SITE_NAME') and  # Azure App Service indicator
            os.getenv('AZURE_CLIENT_ID') == 'system-assigned-managed-identity'
        )
    

    
    @property
    def is_managed_identity_mode(self) -> bool:
        """Property to indicate if using managed identity for template access."""
        return self.is_using_managed_identity()
    
    @property
    def is_endpoint_from_deployment(self) -> bool:
        """Property to indicate if endpoint came from deployment parameters."""
        import os
        return (self.is_using_managed_identity() and 
                bool(os.getenv('AZURE_INFERENCE_ENDPOINT')))
    
    @property
    def is_model_from_deployment(self) -> bool:
        """Property to indicate if model came from deployment parameters."""
        import os
        return (self.is_using_managed_identity() and 
                bool(os.getenv('AZURE_AI_CHAT_DEPLOYMENT_NAME')))
    
    @property
    def is_audio_model_from_deployment(self) -> bool:
        """Property to indicate if audio model came from deployment parameters."""
        import os
        return (self.is_using_managed_identity() and 
                bool(os.getenv('AZURE_AI_AUDIO_DEPLOYMENT_NAME')))
    
    @property
    def auth_method_display(self) -> str:
        """Property to show authentication method in UI."""
        if self.is_using_managed_identity():
            return "🔐 Managed Identity (Automatic)"
        else:
            return ""
    
    @property
    def display_endpoint(self) -> str:
        """Get endpoint for display - shows actual value or empty for placeholder."""
        return self.endpoint or ''
    
    @property 
    def display_api_key(self) -> str:
        """Get API key for display based on authentication mode."""
        if self.is_using_managed_identity():
            return '🔐 Managed Identity (Automatic)'
        return self.api_key or ''
    
    @property
    def is_api_key_disabled(self) -> bool:
        """Check if API key field should be disabled."""
        return self.is_using_managed_identity()
    
    @property
    def display_model(self) -> str:
        """Get model name for display."""
        return self.model or ''
    
    @property
    def display_audio_model(self) -> str:
        """Get audio model name for display."""
        return self.audio_model or ''

    def validate_form_data(self, form_data: Dict[str, Any]) -> Tuple[bool, str]:
        """Validate form data considering authentication mode."""
        is_managed_identity = self.is_using_managed_identity()
        
        # Validate endpoint
        if not form_data.get('endpoint', '').strip():
            return False, 'Azure endpoint is required. Please enter your Azure AI Foundry endpoint URL.'
        
        # Validate API key only if not using managed identity
        if not is_managed_identity and not form_data.get('api_key', '').strip():
            return False, 'Azure API key is required. Please enter your Azure AI Foundry API key.'
        
        # If using managed identity, set placeholder for API key
        if is_managed_identity and not form_data.get('api_key'):
            form_data['api_key'] = 'managed-identity'
        
        # Validate endpoint format
        endpoint = form_data.get('endpoint', '')
        if not endpoint.startswith('https://'):
            return False, 'Invalid endpoint format. Azure endpoint must start with "https://".'
        
        return True, ''
    
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
        
        # No Key Vault needed for managed identity approach
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
        
        Handles both managed identity and API key authentication modes.
        """
        is_managed_identity = os.getenv('AZURE_CLIENT_ID') == 'system-assigned-managed-identity'
        
        has_endpoint = self.config.endpoint and self.config.endpoint.strip()
        has_api_key = self.config.api_key and self.config.api_key.strip()
        
        # For managed identity, we only need endpoint
        if is_managed_identity:
            if has_endpoint:
                logger.info("Azure AI configuration loaded - Using Managed Identity authentication")
            else:
                logger.warning("Managed Identity detected but no endpoint configured")
        else:
            # For API key authentication, we need both endpoint and API key
            has_credentials = has_endpoint and has_api_key
            
            if has_credentials:
                source = "Key Vault" if self.is_production else "settings file"
                logger.info(f"Azure AI credentials loaded from {source}")
            else:
                if self.is_production:
                    logger.warning("Azure environment detected but no credentials found - configure via settings page")
                else:
                    logger.info("Local environment - configure credentials via settings.json or settings page")
    
    def _load_production_config(self) -> None:
        """Load configuration for production: settings.json + environment variables."""
        # Load all settings from settings.json (no sensitive/non-sensitive distinction needed)
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.config.update_from_dict(data)
                    logger.info("Loaded configuration from settings.json")
            except (json.JSONDecodeError, FileNotFoundError, PermissionError) as e:
                logger.warning(f"Could not load settings.json: {e}")
        
        # Load from environment variables (for managed identity and deployment parameters)
        self._load_from_environment()
        
        logger.info(f"Production config loaded - Managed Identity: {self.config.is_using_managed_identity()}")
    
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
    

    
    def _load_from_environment(self) -> None:
        """Load Azure credentials and model configuration from environment variables."""
        # Check for Azure AI Inference credentials
        azure_endpoint = os.getenv('AZURE_INFERENCE_ENDPOINT')
        azure_credential = os.getenv('AZURE_INFERENCE_CREDENTIAL')
        
        # Check if we're using managed identity
        is_managed_identity = os.getenv('AZURE_CLIENT_ID') == 'system-assigned-managed-identity'
        
        # Check for legacy Azure OpenAI credentials
        if not azure_endpoint:
            azure_endpoint = os.getenv('AZURE_OPENAI_ENDPOINT')
        if not azure_credential and not is_managed_identity:
            azure_credential = os.getenv('AZURE_OPENAI_KEY') or os.getenv('AZURE_OPENAI_API_KEY')
        
        # Load endpoint from environment
        if azure_endpoint:
            self.config.endpoint = azure_endpoint
            logger.info("Loaded Azure endpoint from environment variables")
        
        # Handle authentication based on mode
        if is_managed_identity:
            # For managed identity, set a placeholder to satisfy validation
            self.config.api_key = 'managed-identity'
            logger.info("Using Azure Managed Identity authentication")
        elif azure_credential:
            self.config.api_key = azure_credential
            logger.info("Loaded Azure API key from environment variables")
        
        # Load model names from infrastructure environment variables
        chat_model = os.getenv('AZURE_AI_CHAT_DEPLOYMENT_NAME')
        audio_model = os.getenv('AZURE_AI_AUDIO_DEPLOYMENT_NAME')
        
        if chat_model:
            self.config.model = chat_model
            logger.info(f"Loaded chat model from environment: {chat_model}")
        
        if audio_model:
            self.config.audio_model = audio_model
            logger.info(f"Loaded audio model from environment: {audio_model}")
    
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
        """Save configuration for production: All settings to JSON file (no Key Vault needed)."""
        try:
            # For managed identity, we can save everything to settings.json
            # No sensitive API keys to protect
            config_dict = self.config.to_dict()
            
            # If using managed identity, don't save the placeholder API key
            if self.config.is_using_managed_identity() and config_dict.get('api_key') == 'managed-identity':
                config_dict.pop('api_key', None)
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config_dict, f, indent=2, ensure_ascii=False)
            logger.info("Saved configuration to settings.json")
            return True
        except Exception as e:
            logger.error(f"Failed to save configuration: {e}")
            return False
    
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