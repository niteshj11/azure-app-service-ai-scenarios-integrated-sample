"""
Reasoning Scenario - Azure AI Foundry Reasoning Models

Advanced problem-solving using reasoning models following Microsoft's patterns.
"""

import re
from typing import List, Dict
from ..utils.azure_client import get_azure_client
from ..utils.helpers import get_conversation_history
from ..config import get_model_config

# Check for OpenAI SDK availability
try:
    from openai import AzureOpenAI
    OPENAI_SDK_AVAILABLE = True
except ImportError:
    OPENAI_SDK_AVAILABLE = False
    AzureOpenAI = None


def handle_reasoning_message(user_message: str) -> str:
    """
    Handle reasoning requests using Azure AI Foundry reasoning capabilities.
    
    Args:
        user_message: Complex question or problem
        
    Returns:
        Detailed reasoning response with thinking process
    """
    client = get_azure_client()
    config = get_model_config()
    
    messages = build_reasoning_messages(user_message)
    
    # Handle both OpenAI SDK and azure.ai.inference
    if OPENAI_SDK_AVAILABLE and isinstance(client, AzureOpenAI):
        # Use OpenAI SDK interface
        response = client.chat.completions.create(
            messages=messages,
            model=config.model,
            max_tokens=min(4000, config.max_tokens * 2),
            temperature=0.1,  # Lower for focused reasoning
        )
    else:
        # Use azure.ai.inference interface
        response = client.complete(
            messages=messages,
            model=config.model,
            max_tokens=min(4000, config.max_tokens * 2),
            temperature=0.1,  # Lower for focused reasoning
        )
    
    return format_reasoning_response(response, config)


def format_reasoning_response(response, config) -> str:
    """Format reasoning response following Microsoft patterns."""
    main_content = response.choices[0].message.content
    
    if not config.show_reasoning:
        # Clean <think></think> tags for production
        if main_content and '<think>' in main_content:
            clean_match = re.search(r'<think>.*?</think>(.*)', main_content, re.DOTALL)
            if clean_match:
                return clean_match.group(1).strip()
        return main_content
    
    # Handle reasoning content from different model types
    reasoning_content = None
    
    # Check for reasoning_content field (o1/o3 models)
    if hasattr(response.choices[0].message, 'reasoning_content'):
        reasoning_content = response.choices[0].message.reasoning_content
    # Check for <think></think> tags (DeepSeek-R1 style)
    elif main_content and '<think>' in main_content:
        think_match = re.search(r'<think>(.*?)</think>(.*)', main_content, re.DOTALL)
        if think_match:
            reasoning_content = think_match.group(1).strip()
            main_content = think_match.group(2).strip()
    
    if reasoning_content:
        return f"""🧠 **AI Reasoning Mode**

**Thinking Process:**
{reasoning_content}

**Final Answer:**
{main_content}"""
    
    return f"🧠 **Enhanced Reasoning Mode**\n\n{main_content}"


def build_reasoning_messages(user_message: str) -> List[Dict[str, str]]:
    """Build messages for reasoning following Microsoft patterns."""
    config = get_model_config()
    
    # Use configured system message with reasoning context
    system_message = config.system_message + (
        "\n\nFor reasoning tasks, provide step-by-step analysis for complex problems. "
        "Use logical reasoning and consider multiple perspectives."
    )
    
    messages = [
        {
            "role": "system",
            "content": system_message
        }
    ]
    
    # Add clean conversation history (limited for focus)
    history = get_conversation_history()[-6:]
    cleaned_history = clean_reasoning_from_history(history)
    messages.extend(cleaned_history)
    
    messages.append({
        "role": "user",
        "content": f"Please analyze this step by step: {user_message}"
    })
    
    return messages


def clean_reasoning_from_history(history: List[Dict[str, str]]) -> List[Dict[str, str]]:
    """Clean reasoning content from history to prevent token bloat."""
    cleaned = []
    
    for message in history:
        if message.get('role') == 'assistant':
            content = message.get('content', '')
            # Remove <think></think> tags and reasoning indicators
            if '<think>' in content:
                clean_match = re.search(r'<think>.*?</think>(.*)', content, re.DOTALL)
                content = clean_match.group(1).strip() if clean_match else content
            
            # Remove reasoning UI elements
            content = re.sub(r'🧠.*?\n\n', '', content)
            content = re.sub(r'\*\*Thinking Process:\*\*.*?\*\*Final Answer:\*\*', '', content, flags=re.DOTALL)
            
            cleaned.append({'role': message['role'], 'content': content.strip()})
        else:
            cleaned.append(message)
    
    return cleaned