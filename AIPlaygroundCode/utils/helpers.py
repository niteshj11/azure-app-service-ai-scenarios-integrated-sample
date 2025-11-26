"""
Common helper functions for the AI chatbot application.
"""

import os
import logging
import json
import zlib
import base64
from typing import Optional, List, Dict
from werkzeug.utils import secure_filename
from flask import session

# Set up logging
logger = logging.getLogger(__name__)


def setup_logging(log_level: str = 'INFO') -> None:
    """
    Configure application logging.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
    """
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('AIPlaygroundCode/app.log') if not os.getenv('FLASK_DEBUG') else logging.NullHandler()
        ]
    )


def save_uploaded_file(file, upload_folder: str) -> Optional[str]:
    """
    Safely save an uploaded file.
    
    Args:
        file: Uploaded file object
        upload_folder: Directory to save the file
        
    Returns:
        str: Path to saved file or None if failed
    """
    if not file or file.filename == '':
        return None
    
    try:
        filename = secure_filename(file.filename)
        if not filename:
            return None
        
        filepath = os.path.join(upload_folder, filename)
        file.save(filepath)
        logger.info(f"File saved successfully: {filepath}")
        return filepath
    except Exception as e:
        logger.error(f"Failed to save file: {e}")
        return None


def _compress_conversation(conversation: List[Dict[str, str]]) -> str:
    """
    Compress conversation history to reduce session size.
    
    Args:
        conversation: List of message dictionaries
        
    Returns:
        Compressed and base64 encoded conversation string
    """
    try:
        # Convert to JSON and compress
        json_str = json.dumps(conversation, separators=(',', ':'))
        compressed = zlib.compress(json_str.encode('utf-8'))
        encoded = base64.b64encode(compressed).decode('ascii')
        return encoded
    except Exception as e:
        logger.error(f"Failed to compress conversation: {e}")
        return ""


def _decompress_conversation(compressed_data: str) -> List[Dict[str, str]]:
    """
    Decompress conversation history from session.
    
    Args:
        compressed_data: Compressed and base64 encoded conversation string
        
    Returns:
        List of message dictionaries
    """
    try:
        if not compressed_data:
            return []
        
        # Decode and decompress
        decoded = base64.b64decode(compressed_data.encode('ascii'))
        decompressed = zlib.decompress(decoded).decode('utf-8')
        conversation = json.loads(decompressed)
        return conversation if isinstance(conversation, list) else []
    except Exception as e:
        logger.error(f"Failed to decompress conversation: {e}")
        return []


def _truncate_message_content(content: str, max_length: int = 8000) -> str:
    """
    Truncate message content if it's too long to keep session manageable.
    
    Args:
        content: Message content
        max_length: Maximum allowed length
        
    Returns:
        Truncated content with indicator if truncated
    """
    if len(content) <= max_length:
        return content
    
    # Truncate and add indicator
    truncated = content[:max_length-100]  # Leave more room for indicator
    return f"{truncated}...\n\n*[Response continued but truncated to manage session size]*"


def get_conversation_history() -> List[Dict[str, str]]:
    """
    Get conversation history from session with compression support.
    
    Returns:
        List of message dictionaries with 'role' and 'content' keys
    """
    try:
        # Try new compressed format first
        compressed_conv = session.get('conversation_compressed')
        if compressed_conv:
            return _decompress_conversation(compressed_conv)
        
        # Fall back to legacy uncompressed format
        legacy_conv = session.get('conversation', [])
        if legacy_conv:
            # Migrate to compressed format
            session['conversation_compressed'] = _compress_conversation(legacy_conv)
            session.pop('conversation', None)  # Remove legacy format
            session.modified = True
            return legacy_conv
        
        return []
    except RuntimeError as e:
        logger.warning(f"Session access failed in get_conversation_history: {e}")
        
        # Check if we're in a Flask request context
        from flask import has_request_context
        if has_request_context():
            # We're in a web request but session failed - log but return empty for graceful degradation
            logger.error("Session access failed during web request - returning empty conversation")
        
        return []


def add_to_conversation(role: str, content: str) -> None:
    """
    Add message to conversation history with compression and size management.
    Enhanced for multimodal content handling.
    
    Args:
        role: Message role ('user' or 'assistant')
        content: Message content
    """
    try:
        # Get current conversation
        conversation = get_conversation_history()
        
        # Enhanced content processing for multimodal scenarios
        processed_content = _process_multimodal_content(content)
        
        # Add new message
        conversation.append({
            'role': role,
            'content': processed_content
        })
        
        # Dynamic conversation length based on content size
        max_messages = _calculate_max_messages(conversation)
        if len(conversation) > max_messages:
            conversation = conversation[-max_messages:]
        
        # Store in compressed format
        compressed_conv = _compress_conversation(conversation)
        
        # Enhanced size checking with fallback strategies
        if len(compressed_conv) > 3500:  # Stricter limit for cookie safety
            # Strategy 1: Reduce conversation length further
            conversation = conversation[-8:]
            compressed_conv = _compress_conversation(conversation)
            
            # Strategy 2: If still too large, remove multimodal metadata
            if len(compressed_conv) > 3500:
                conversation = _strip_multimodal_metadata(conversation)
                compressed_conv = _compress_conversation(conversation)
        
        # Clear legacy format and store compressed
        session.pop('conversation', None)
        session['conversation_compressed'] = compressed_conv
        session.modified = True
            
    except RuntimeError as e:
        logger.error(f"Session error in add_to_conversation: {e}")
        
        # Check if we're in a Flask request context
        from flask import has_request_context
        if has_request_context():
            # We're in a web request but session failed - this is a real error
            raise RuntimeError(f"Session storage failed during web request: {e}")
        # Otherwise, we're in testing/outside context, so skip silently


def clear_conversation() -> None:
    """Clear conversation history from session (both legacy and compressed formats)."""
    try:
        session.pop('conversation', None)  # Legacy format
        session.pop('conversation_compressed', None)  # New compressed format
        session.modified = True
    except RuntimeError:
        # Working outside request context - nothing to clear
        pass


def format_error_response(error: Exception) -> str:
    """
    Format error for user-friendly display.
    
    Args:
        error: Exception object
        
    Returns:
        User-friendly error message
    """
    logger.error(f"Error occurred: {error}")
    error_str = str(error).lower()
    
    # Check for specific Azure SDK configuration issues
    if "unexpected keyword argument 'endpoint'" in error_str or "session.request()" in error_str:
        return (
            "🔧 **Configuration Issue Detected**\n\n"
            "There seems to be an issue with your Azure AI settings. This usually happens when:\n"
            "• Azure endpoint or API key is empty or invalid\n"
            "• Azure SDK version compatibility issue\n\n"
            "**To fix this:**\n"
            "1. Go to **Settings** page\n"
            "2. Verify your **Azure Endpoint** is complete (should end with '/models')\n"
            "3. Verify your **API Key** is properly set\n"
            "4. Click **Test Config** to validate your connection\n"
            "5. If issues persist, try refreshing the page\n\n"
            "Need help? Check the Settings page for endpoint format examples."
        )
    
    if "configuration not found" in error_str or "missing required azure configuration" in error_str:
        return (
            "⚙️ **Azure Configuration Required**\n\n"
            "Your Azure AI settings are not configured yet. To get started:\n\n"
            "1. Go to the **Settings** page\n"
            "2. Enter your **Azure AI Foundry Endpoint**\n"
            "3. Enter your **Azure API Key**\n"
            "4. Select your preferred **Model** (e.g., gpt-4.1)\n"
            "5. Click **Save Settings**\n"
            "6. Use **Test Config** to verify everything works\n\n"
            "Once configured, you can start chatting!"
        )
    
    if "authentication" in error_str or "unauthorized" in error_str:
        return (
            "🔐 **Authentication Error**\n\n"
            "There's an issue with your Azure credentials:\n\n"
            "• Your API key may be incorrect or expired\n"
            "• Your endpoint may not match your subscription\n\n"
            "**To fix this:**\n"
            "1. Go to **Settings** page\n"
            "2. Double-check your **API Key** (no extra spaces)\n"
            "3. Verify your **Endpoint** URL is correct\n"
            "4. Click **Test Config** to validate\n\n"
            "If you recently regenerated keys, make sure to use the new one."
        )
    
    if "model" in error_str and ("not found" in error_str or "does not exist" in error_str):
        return (
            "🤖 **Model Configuration Issue**\n\n"
            "The specified AI model is not available:\n\n"
            "**To fix this:**\n"
            "1. Go to **Settings** page\n"
            "2. Check your **Model Name** (e.g., 'gpt-4.1', 'gpt-4o')\n"
            "3. Make sure it matches your Azure deployment name\n"
            "4. Click **Test Config** to validate\n\n"
            "Common model names: gpt-4.1, gpt-4o, gpt-4o-mini"
        )
    
    # Don't expose detailed error info in production unless debug mode
    if os.getenv('FLASK_DEBUG', 'False').lower() == 'true':
        return f"🔧 **Technical Error (Debug Mode)**\n\nError: {str(error)}\n\nCheck the Settings page to verify your configuration."
    else:
        return (
            "⚠️ **Unexpected Issue**\n\n"
            "I encountered an unexpected issue processing your request.\n\n"
            "**Quick troubleshooting:**\n"
            "1. Check the **Settings** page for any configuration issues\n"
            "2. Try **Test Config** to verify your Azure connection\n"
            "3. Refresh the page and try again\n"
            "4. If the issue persists, check your internet connection\n\n"
            "The system is designed to help you resolve configuration issues automatically."
        )


def validate_message_input(message: str) -> bool:
    """
    Validate user message input.
    
    Args:
        message: User input message
        
    Returns:
        bool: True if valid, False otherwise
    """
    if not message or not message.strip():
        return False
    
    if len(message.strip()) > 4000:  # Reasonable limit
        return False
    
    return True


def _process_multimodal_content(content: str) -> str:
    """
    Process content for multimodal scenarios to reduce session size.
    
    Args:
        content: Original message content
        
    Returns:
        Processed content optimized for session storage
    """
    # Check if content contains multimodal indicators
    if any(indicator in content.lower() for indicator in ['🎤 **audio', '🖼️ **image', 'data:image', 'input_audio']):
        # For multimodal content, create a summary instead of storing full details
        if '🎤 **audio' in content:
            # Extract key information from audio processing response
            lines = content.split('\n')
            summary_lines = []
            for line in lines:
                if any(key in line.lower() for key in ['**file**:', '**request**:', '**transcription**:', '**ai analysis**:']):
                    # Truncate long transcriptions and analyses
                    if len(line) > 200:
                        line = line[:200] + '...[truncated]'
                    summary_lines.append(line)
            
            if summary_lines:
                return '\n'.join(summary_lines) + '\n\n*[Audio content summarized for session efficiency]*'
        
        elif '🖼️ **image' in content or 'analyzed the image' in content.lower():
            # For image content, keep summary but remove any base64 data
            processed = content.replace('data:image/jpeg;base64,', '[base64 data removed]')
            if len(processed) > 500:
                processed = processed[:500] + '...[truncated for session efficiency]'
            return processed
    
    # For regular content, apply standard truncation
    return _truncate_message_content(content)


def _calculate_max_messages(conversation: List[Dict[str, str]]) -> int:
    """
    Calculate maximum number of messages to keep based on content size.
    
    Args:
        conversation: Current conversation history
        
    Returns:
        Maximum number of messages to retain
    """
    # Estimate average message size
    if not conversation:
        return 16
    
    total_size = sum(len(msg.get('content', '')) for msg in conversation)
    avg_size = total_size / len(conversation) if conversation else 0
    
    # Adjust max messages based on average size
    if avg_size > 1000:  # Large messages (multimodal content)
        return 8
    elif avg_size > 500:  # Medium messages
        return 12
    else:  # Small messages
        return 20


def _strip_multimodal_metadata(conversation: List[Dict[str, str]]) -> List[Dict[str, str]]:
    """
    Remove multimodal metadata from conversation to save space.
    
    Args:
        conversation: Conversation history
        
    Returns:
        Conversation with multimodal metadata removed
    """
    cleaned_conversation = []
    
    for msg in conversation:
        content = msg.get('content', '')
        
        # Remove common multimodal metadata patterns
        if '🎤 **Audio Processing Complete**' in content:
            # Keep only the essential parts
            lines = content.split('\n')
            essential_lines = []
            for line in lines:
                if any(key in line for key in ['**AI Analysis**:', '**Transcription**:']):
                    essential_lines.append(line)
                elif line.startswith('**') and len(essential_lines) < 3:
                    essential_lines.append(line)
            
            content = '\n'.join(essential_lines) + '\n*[Audio metadata removed]*'
        
        # Remove base64 image data references
        content = content.replace('data:image/jpeg;base64,', '[image]')
        
        # Limit content length
        if len(content) > 300:
            content = content[:300] + '...[content trimmed]'
        
        cleaned_conversation.append({
            'role': msg['role'],
            'content': content
        })
    
    return cleaned_conversation


def clear_session_multimodal_data() -> None:
    """
    Clear multimodal-specific data from session to free up space.
    Called when session size becomes critical.
    """
    try:
        # Clear temporary upload data
        session.pop('temp_upload_data', None)
        
        # Clear any cached file references
        session.pop('last_upload_info', None)
        
        # Clear large response cache if present
        session.pop('response_cache', None)
        
        session.modified = True
        logger.info("Cleared multimodal session data")
        
    except RuntimeError:
        # Working outside request context
        pass