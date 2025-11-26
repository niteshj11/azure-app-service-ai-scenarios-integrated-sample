"""
Chat Scenario - Azure AI Foundry Chat Completions

Basic conversational AI using Azure AI Foundry following Microsoft's recommended patterns.
"""

from typing import List, Dict
from ..utils.azure_client import get_azure_client
from ..utils.helpers import get_conversation_history
from ..config import get_model_config

# Import OpenAI SDK if available
try:
    from openai import AzureOpenAI
    OPENAI_SDK_AVAILABLE = True
except ImportError:
    OPENAI_SDK_AVAILABLE = False


def handle_chat_message(user_message: str) -> str:
    """
    Handle chat message using Azure AI Foundry chat completions.
    
    Args:
        user_message: User's input message
        
    Returns:
        AI assistant's response
    """
    client = get_azure_client()
    config = get_model_config()
    
    messages = build_chat_messages(user_message)
    
    # Handle both OpenAI SDK and azure.ai.inference
    if OPENAI_SDK_AVAILABLE and isinstance(client, AzureOpenAI):
        # Use OpenAI SDK interface
        response = client.chat.completions.create(
            messages=messages,
            model=config.model,
            max_tokens=config.max_tokens,
            temperature=config.temperature,
            top_p=config.top_p,
            frequency_penalty=config.frequency_penalty,
            presence_penalty=config.presence_penalty
        )
        return response.choices[0].message.content
    else:
        # Use azure.ai.inference interface
        response = client.complete(
            messages=messages,
            model=config.model,
            max_tokens=config.max_tokens,
            temperature=config.temperature
        )
        return response.choices[0].message.content


def build_chat_messages(user_message: str) -> List[Dict[str, str]]:
    """Build messages for Azure AI chat completion following Microsoft patterns."""
    config = get_model_config()
    
    messages = [
        {
            "role": "system",
            "content": config.system_message
        }
    ]
    
    # Add conversation history (last 10 messages)
    conversation_history = get_conversation_history()[-10:]
    messages.extend(conversation_history)
    
    messages.append({
        "role": "user", 
        "content": user_message
    })
    
    return messages