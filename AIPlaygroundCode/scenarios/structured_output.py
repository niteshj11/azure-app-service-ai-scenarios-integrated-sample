"""
Structured Output Scenario - Azure AI Foundry JSON Schema

JSON formatted responses using Azure AI Foundry structured output capabilities.
"""

import json
from typing import List, Dict, Any
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


def handle_structured_message(user_message: str) -> str:
    """
    Handle structured JSON output using Azure AI Foundry patterns.
    
    Args:
        user_message: User's request for structured data
        
    Returns:
        Formatted response with structured JSON data
    """
    client = get_azure_client()
    config = get_model_config()
    
    output_type = detect_structure_type(user_message)
    messages = build_structured_messages(user_message, output_type)
    
    # Handle both OpenAI SDK and azure.ai.inference
    if OPENAI_SDK_AVAILABLE and isinstance(client, AzureOpenAI):
        # Use OpenAI SDK interface with JSON response format
        response = client.chat.completions.create(
            messages=messages,
            model=config.model,
            max_tokens=1500,
            temperature=0.1,
            response_format={"type": "json_object"}  # Microsoft recommended approach
        )
    else:
        # Use azure.ai.inference interface
        response = client.complete(
            messages=messages,
            model=config.model,
            max_tokens=1500,
            temperature=0.1,
            response_format={"type": "json_object"}  # Microsoft recommended approach
        )
    
    raw_response = response.choices[0].message.content
    structured_data = extract_and_validate_json(raw_response)
    
    return format_structured_response(structured_data, output_type)


def detect_structure_type(user_message: str) -> str:
    """Detect structure type from user message."""
    message_lower = user_message.lower()
    
    structure_patterns = {
        "product_info": ["product", "item", "catalog", "inventory"],
        "customer_data": ["customer", "user", "client", "contact"],
        "business_analysis": ["analysis", "report", "metrics", "kpi"],
        "task_list": ["tasks", "todo", "steps", "checklist"],
        "general": []
    }
    
    for structure_type, keywords in structure_patterns.items():
        if any(keyword in message_lower for keyword in keywords):
            return structure_type
    
    return "general"


def build_structured_messages(user_message: str, output_type: str) -> List[Dict[str, str]]:
    """Build messages for structured JSON output following Microsoft patterns."""
    messages = [
        {
            "role": "system",
            "content": get_structured_system_prompt(output_type)
        }
    ]
    
    # Add minimal conversation context
    history = get_conversation_history()[-3:]
    messages.extend(history)
    
    messages.append({
        "role": "user",
        "content": f"{user_message}\n\nProvide response in valid JSON format."
    })
    
    return messages


def get_structured_system_prompt(output_type: str) -> str:
    """Get system prompt for structured output."""
    config = get_model_config()
    
    # Combine configured system message with structured output requirements
    structured_instructions = """

For structured output tasks:
- Always return valid JSON
- Use snake_case for field names  
- Include relevant metadata
- Ensure data completeness

Respond only with JSON, no additional text."""
    
    return config.system_message + structured_instructions


def extract_and_validate_json(response_text: str) -> Dict[str, Any]:
    """Extract and validate JSON from response following Microsoft patterns."""
    try:
        response_text = response_text.strip()
        
        # Handle markdown code blocks
        if "```json" in response_text:
            start = response_text.find("```json") + 7
            end = response_text.find("```", start)
            json_text = response_text[start:end].strip()
        elif response_text.startswith("{"):
            json_text = response_text
        else:
            # Extract JSON pattern
            import re
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                json_text = json_match.group()
            else:
                raise ValueError("No JSON found")
        
        return json.loads(json_text)
        
    except (json.JSONDecodeError, ValueError) as e:
        return {
            "error": "Failed to parse JSON",
            "raw_response": response_text[:500],
            "details": str(e)
        }


def format_structured_response(data: Dict[str, Any], output_type: str) -> str:
    """Format structured data for display."""
    try:
        formatted_json = json.dumps(data, indent=2, ensure_ascii=False)
        
        return f"""🔧 **Structured Output ({output_type})**

```json
{formatted_json}
```

✅ **Integration Ready** - JSON format for APIs and systems
📊 **Fields**: {len(data)} top-level fields
"""
        
    except Exception:
        return f"Structured data: {str(data)}"