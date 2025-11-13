"""
Azure AI client management utilities following Microsoft Azure AI Foundry best practices.

This module provides Azure AI Foundry integration using the official azure.ai.inference SDK
with proper error handling and configuration management.
"""

import logging
from typing import Optional
from azure.ai.inference import ChatCompletionsClient
from azure.core.credentials import AzureKeyCredential
from ..config import get_azure_config, is_configured

logger = logging.getLogger(__name__)


class AzureClientManager:
    """Manages Azure AI Foundry client instances following Microsoft patterns."""
    
    def __init__(self):
        self._client: Optional[ChatCompletionsClient] = None
        self._last_endpoint = None
        self._last_api_key = None
    
    def get_client(self) -> ChatCompletionsClient:
        """
        Get Azure AI Foundry client following official Microsoft patterns.
        
        Returns:
            ChatCompletionsClient: Configured Azure AI client
        """
        if not is_configured():
            raise RuntimeError("Azure configuration required")
        
        endpoint, api_key, _ = get_azure_config()
        
        if not endpoint or not api_key:
            raise RuntimeError("Azure endpoint and API key required")
        
        if not endpoint.startswith('https://'):
            raise RuntimeError("Invalid endpoint format")
        
        # Recreate client if configuration changed
        if (self._client is None or 
            endpoint != self._last_endpoint or 
            api_key != self._last_api_key):
            
            self._client = ChatCompletionsClient(
                endpoint=endpoint,
                credential=AzureKeyCredential(api_key)
            )
            self._last_endpoint = endpoint
            self._last_api_key = api_key
        
        return self._client
    
    def test_connection(self) -> bool:
        """Test Azure AI service connection."""
        try:
            from ..config import get_model_config
            
            client = self.get_client()
            config = get_model_config()
            
            response = client.complete(
                messages=[{"role": "user", "content": "Test"}],
                model=config.model,
                max_tokens=1
            )
            return True
        except Exception:
            return False


# Global client manager instance
client_manager = AzureClientManager()


def get_azure_client() -> ChatCompletionsClient:
    """
    Get configured Azure AI client.
    
    Returns:
        ChatCompletionsClient: Ready-to-use Azure AI client
    """
    return client_manager.get_client()


def test_azure_connection() -> bool:
    """
    Test Azure AI service connection.
    
    Returns:
        bool: True if connection successful
    """
    return client_manager.test_connection()