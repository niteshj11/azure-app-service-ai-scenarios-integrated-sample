"""
Azure AI client management utilities following Microsoft Azure AI Foundry best practices.

This module provides Azure AI Foundry integration using the official azure.ai.inference SDK
with proper error handling and configuration management.
"""

import os
import logging
from typing import Optional, Union
from azure.identity import DefaultAzureCredential, ManagedIdentityCredential
from ..config import get_azure_config, is_configured

# Use OpenAI SDK for better Azure integration
try:
    from openai import AzureOpenAI
    OPENAI_SDK_AVAILABLE = True
except ImportError:
    # Fallback to azure.ai.inference
    from azure.ai.inference import ChatCompletionsClient
    from azure.core.credentials import AzureKeyCredential
    OPENAI_SDK_AVAILABLE = False

logger = logging.getLogger(__name__)


class AzureClientManager:
    """Manages Azure AI Foundry client instances following Microsoft patterns."""
    
    def __init__(self):
        self._client: Optional[Union[AzureOpenAI, "ChatCompletionsClient"]] = None
        self._last_endpoint = None
        self._last_api_key = None
        self._last_auth_mode = None
    
    def _is_using_managed_identity(self) -> bool:
        """Check if Managed Identity is configured and should be used."""
        return os.getenv('AZURE_CLIENT_ID') == 'system-assigned-managed-identity'
    
    def get_client(self) -> Union[AzureOpenAI, "ChatCompletionsClient"]:
        """
        Get Azure AI Foundry client with automatic Managed Identity or API key authentication.
        
        Returns:
            AzureOpenAI or ChatCompletionsClient: Configured Azure AI client
        """
        if not is_configured():
            raise RuntimeError("Azure configuration required")
        
        endpoint, api_key, api_version = get_azure_config()
        
        if not endpoint:
            raise RuntimeError("Azure endpoint is required")
        
        if not endpoint.startswith('https://'):
            raise RuntimeError("Invalid endpoint format")
        
        # Determine authentication method
        use_managed_identity = self._is_using_managed_identity()
        
        # For Managed Identity, we don't need an API key
        if not use_managed_identity and not api_key:
            raise RuntimeError("Azure API key required when not using Managed Identity")
        
        # Recreate client if configuration changed
        if (self._client is None or 
            endpoint != self._last_endpoint or 
            api_key != self._last_api_key or
            use_managed_identity != self._last_auth_mode):
            
            if OPENAI_SDK_AVAILABLE:
                # Use OpenAI SDK for better Azure managed identity support
                if use_managed_identity:
                    logger.info("Creating AzureOpenAI client with Managed Identity authentication")
                    try:
                        # Get token provider for managed identity
                        from azure.identity import get_bearer_token_provider
                        
                        # Use ManagedIdentityCredential directly for App Service
                        # This avoids the EnvironmentCredential issues with DefaultAzureCredential
                        logger.info("Using ManagedIdentityCredential for App Service")
                        credential = ManagedIdentityCredential()
                        
                        # Test credential by getting a token first
                        logger.info("Testing credential by requesting a token...")
                        test_token = credential.get_token("https://cognitiveservices.azure.com/.default")
                        logger.info(f"Token acquired successfully, expires at: {test_token.expires_on}")
                        
                        # Use the correct scope for Azure Cognitive Services
                        token_provider = get_bearer_token_provider(
                            credential, 
                            "https://cognitiveservices.azure.com/.default"
                        )
                        
                        # Remove /models suffix for OpenAI SDK
                        base_endpoint = endpoint.replace('/models', '').rstrip('/')
                        
                        self._client = AzureOpenAI(
                            azure_endpoint=base_endpoint,
                            azure_ad_token_provider=token_provider,
                            api_version=api_version
                        )
                        
                        logger.info("Successfully created AzureOpenAI client with managed identity")
                        
                    except Exception as e:
                        logger.error(f"OpenAI SDK with Managed Identity failed: {e}")
                        raise RuntimeError(f"Managed Identity authentication failed: {e}")
                else:
                    # Use API key authentication with OpenAI SDK
                    logger.info("Creating AzureOpenAI client with API key authentication")
                    base_endpoint = endpoint.replace('/models', '').rstrip('/')
                    
                    self._client = AzureOpenAI(
                        azure_endpoint=base_endpoint,
                        api_key=api_key,
                        api_version=api_version
                    )
            else:
                # Fallback to azure.ai.inference (original implementation)
                logger.warning("OpenAI SDK not available, using azure.ai.inference fallback")
                if use_managed_identity:
                    credential = DefaultAzureCredential()
                    self._client = ChatCompletionsClient(
                        endpoint=endpoint,
                        credential=credential
                    )
                else:
                    self._client = ChatCompletionsClient(
                        endpoint=endpoint,
                        credential=AzureKeyCredential(api_key)
                    )
            
            self._last_endpoint = endpoint
            self._last_api_key = api_key
            self._last_auth_mode = use_managed_identity
        
        return self._client
    
    def test_connection(self) -> tuple[bool, str]:
        """
        Test Azure AI service connection with detailed diagnostics.
        
        Returns:
            tuple[bool, str]: (success, diagnostic_message)
        """
        try:
            from ..config import get_model_config
            
            # Get configuration
            config = get_model_config()
            endpoint, api_key, api_version = get_azure_config()
            use_managed_identity = self._is_using_managed_identity()
            
            logger.info(f"Testing connection with endpoint: {endpoint}")
            logger.info(f"Using Managed Identity: {use_managed_identity}")
            logger.info(f"Model: {config.model}")
            
            # Environment diagnostics
            env_vars = {
                'AZURE_CLIENT_ID': os.getenv('AZURE_CLIENT_ID', 'Not set'),
                'AZURE_TENANT_ID': os.getenv('AZURE_TENANT_ID', 'Not set'),
                'IDENTITY_ENDPOINT': os.getenv('IDENTITY_ENDPOINT', 'Not set'),
                'IDENTITY_HEADER': os.getenv('IDENTITY_HEADER', 'Not set'),
                'MSI_ENDPOINT': os.getenv('MSI_ENDPOINT', 'Not set'),
                'MSI_SECRET': 'Set' if os.getenv('MSI_SECRET') else 'Not set',
                'WEBSITE_SITE_NAME': os.getenv('WEBSITE_SITE_NAME', 'Not set')
            }
            
            logger.info(f"Environment variables: {env_vars}")
            
            # Verify managed identity is properly configured for App Service
            if use_managed_identity:
                if not os.getenv('IDENTITY_ENDPOINT') and not os.getenv('MSI_ENDPOINT'):
                    logger.error("Managed Identity endpoints not found - App Service might not be configured correctly")
                if not os.getenv('WEBSITE_SITE_NAME'):
                    logger.warning("WEBSITE_SITE_NAME not found - might not be running in App Service")
            
            # Create client
            client = self.get_client()
            
            # Test connection - handle both OpenAI SDK and azure.ai.inference
            if OPENAI_SDK_AVAILABLE and isinstance(client, AzureOpenAI):
                # Use OpenAI SDK interface
                response = client.chat.completions.create(
                    messages=[{"role": "user", "content": "Test"}],
                    model=config.model,
                    max_tokens=1
                )
            else:
                # Use azure.ai.inference interface
                response = client.complete(
                    messages=[{"role": "user", "content": "Test"}],
                    model=config.model,
                    max_tokens=1
                )
            
            logger.info("Connection test successful")
            return True, f"✅ Connection successful using {'Managed Identity' if use_managed_identity else 'API Key'}"
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Connection test failed: {error_msg}")
            
            # Provide detailed error analysis
            if "DefaultAzureCredential" in error_msg:
                analysis = "❌ DefaultAzureCredential authentication failed. Check Managed Identity configuration and RBAC permissions."
            elif "401" in error_msg or "unauthorized" in error_msg.lower():
                analysis = "❌ Authentication failed. Check API key or Managed Identity permissions."
            elif "403" in error_msg or "forbidden" in error_msg.lower():
                analysis = "❌ Access forbidden. Check RBAC role assignments for the Managed Identity."
            elif "404" in error_msg or "not found" in error_msg.lower():
                analysis = "❌ Endpoint or model not found. Verify Azure AI endpoint and model name."
            elif "timeout" in error_msg.lower():
                analysis = "❌ Connection timeout. Check network connectivity to Azure AI service."
            else:
                analysis = f"❌ Connection failed: {error_msg}"
            
            return False, f"{analysis}\n\nDetailed error: {error_msg}"


# Global client manager instance
client_manager = AzureClientManager()


def get_azure_client() -> Union[AzureOpenAI, "ChatCompletionsClient"]:
    """
    Get configured Azure AI client.
    
    Returns:
        AzureOpenAI or ChatCompletionsClient: Ready-to-use Azure AI client
    """
    return client_manager.get_client()


def test_azure_connection() -> bool:
    """
    Test Azure AI service connection.
    
    Returns:
        bool: True if connection successful
    """
    success, _ = client_manager.test_connection()
    return success


def test_azure_connection_detailed() -> tuple[bool, str]:
    """
    Test Azure AI service connection with detailed diagnostics.
    
    Returns:
        tuple[bool, str]: (success, diagnostic_message)
    """
    return client_manager.test_connection()