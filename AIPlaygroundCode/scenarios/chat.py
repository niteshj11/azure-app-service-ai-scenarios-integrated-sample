"""
Chat Scenario - Azure AI Foundry Chat Completions

Basic conversational AI using Azure AI Foundry following Microsoft's recommended patterns.
"""

from typing import List, Dict
from ..utils.azure_client import get_azure_client
from ..utils.helpers import get_conversation_history
from ..config import get_model_config


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


def get_chat_example() -> Dict[str, str]:
    """
    Get example chat interaction for documentation.
    
    Returns:
        Dictionary with example user input and expected response pattern
    """
    return {
        "user_input": "What services does TechMart offer?",
        "response_pattern": "Professional response about TechMart's services",
        "description": "Basic conversational AI for customer service and general inquiries"
    }