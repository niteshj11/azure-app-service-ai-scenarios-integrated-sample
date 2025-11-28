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
    Add message to conversation history with intelligent session size management.
    Uses smart truncation that removes old messages first, preserving recent complete messages.
    
    Args:
        role: Message role ('user' or 'assistant')
        content: Message content
    """
    try:
        # Get current conversation and session size
        conversation = get_conversation_history()
        current_session_size = _get_current_session_size()
        
        # Process content for multimodal scenarios (but don't truncate yet)
        processed_content = _process_multimodal_content_light(content)
        
        # Create new message
        new_message = {
            'role': role,
            'content': processed_content
        }
        
        # Apply intelligent session size management
        conversation = _apply_intelligent_truncation(conversation, new_message, current_session_size)
        
        # Store in compressed format
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
    Process content for multimodal scenarios to reduce session size while preserving key information.
    
    Args:
        content: Original message content
        
    Returns:
        Processed content optimized for session storage
    """
    # Check if content contains multimodal indicators
    if any(indicator in content.lower() for indicator in ['🎤 **audio', '🖼️ **image', 'data:image', 'input_audio']):
        # For multimodal content, intelligently preserve important parts
        if '🎤 **audio' in content:
            # Preserve more audio information - only compress if very long
            if len(content) > 1200:  # More generous limit
                lines = content.split('\n')
                preserved_lines = []
                transcription_section = False
                
                for line in lines:
                    # Always preserve headers and metadata
                    if any(key in line.lower() for key in ['**file**:', '**request**:', '**transcription**:', '**ai analysis**:', '**status**:']):
                        preserved_lines.append(line)
                        transcription_section = '**transcription**:' in line.lower()
                    # Preserve transcription content but compress if very long
                    elif transcription_section and line.strip() and not line.startswith('**'):
                        if len(line) > 300:
                            preserved_lines.append(line[:300] + '...[full transcription available]')
                            transcription_section = False
                        else:
                            preserved_lines.append(line)
                    # Preserve other content
                    elif not line.startswith('*[') and line.strip():  # Skip metadata markers
                        preserved_lines.append(line)
                
                return '\n'.join(preserved_lines) + '\n\n*[Audio response optimized for session storage]*'
            else:
                # Content is reasonable size - keep as is
                return content
        
        elif '🖼️ **image' in content or 'analyzed the image' in content.lower():
            # For image content, remove base64 data but keep analysis
            processed = content.replace('data:image/jpeg;base64,', '[image]')
            if len(processed) > 800:  # More generous limit for image analysis
                processed = processed[:800] + '...[image analysis continues]'
            return processed
    
    # For regular content, use light processing to preserve more content
    return _process_multimodal_content_light(content)


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


def _compress_multimodal_metadata(conversation: List[Dict[str, str]]) -> List[Dict[str, str]]:
    """
    Intelligently compress multimodal metadata from conversation to save space while preserving key information.
    
    Args:
        conversation: Conversation history
        
    Returns:
        Conversation with compressed multimodal metadata
    """
    compressed_conversation = []
    
    for msg in conversation:
        content = msg.get('content', '')
        
        # Compress audio processing responses intelligently
        if '🎤 **Audio Processing Complete**' in content:
            lines = content.split('\n')
            essential_lines = []
            transcription_found = False
            
            for line in lines:
                # Always keep file info and request
                if any(key in line for key in ['**File**:', '**Request**:']):
                    essential_lines.append(line)
                # Keep transcription but compress if too long
                elif '**Transcription**:' in line or '**📝 Transcription**:' in line:
                    essential_lines.append(line)
                    transcription_found = True
                elif transcription_found and line.strip() and not line.startswith('**'):
                    # This is transcription content - compress if needed
                    if len(line) > 200:
                        compressed_line = line[:200] + '...[transcription continues]'
                        essential_lines.append(compressed_line)
                        transcription_found = False  # Stop processing transcription
                    else:
                        essential_lines.append(line)
                # Keep AI analysis but compress if needed  
                elif any(key in line for key in ['**AI Analysis**:', '**🧠 AI Analysis**:']):
                    essential_lines.append(line)
                elif line.startswith('**') and 'analysis' in line.lower():
                    if len(line) > 150:
                        compressed_line = line[:150] + '...[analysis continues]'
                        essential_lines.append(compressed_line)
                    else:
                        essential_lines.append(line)
                # Keep status and completion indicators
                elif any(indicator in line for indicator in ['✅ **Audio processed', '**Status**:', 'Audio processed using']):
                    essential_lines.append(line)
            
            # Preserve the essential structure but indicate compression
            content = '\n'.join(essential_lines)
            if len(content) > 600:  # Still too long
                content = content[:600] + '\n\n*[Response compressed for session efficiency]*'
        
        # Compress image content similarly
        elif any(indicator in content.lower() for indicator in ['🖼️ **image', 'analyzed the image', 'image analysis']):
            # Remove base64 image data references but preserve analysis
            content = content.replace('data:image/jpeg;base64,', '[image data]')
            if len(content) > 400:
                content = content[:400] + '\n\n*[Image analysis compressed]*'
        
        # General content length management for non-multimodal content
        elif len(content) > 500:
            content = content[:500] + '...[message truncated]'
        
        compressed_conversation.append({
            'role': msg['role'],
            'content': content
        })
    
    return compressed_conversation


def _get_current_session_size() -> int:
    """
    Get current session size in bytes, accounting for Flask session overhead.
    
    Returns:
        Current session size in bytes
    """
    try:
        from flask import session
        # Calculate session size including Flask overhead
        session_str = str(session)
        return len(session_str.encode('utf-8'))
    except RuntimeError:
        # Outside Flask request context
        return 0


def _estimate_message_size(message: Dict[str, str]) -> int:
    """
    Estimate compressed size of a single message.
    
    Args:
        message: Dictionary with 'role' and 'content' keys
        
    Returns:
        Estimated compressed size in bytes
    """
    # Create a minimal conversation with just this message for size estimation
    temp_conv = [message]
    compressed = _compress_conversation(temp_conv)
    return len(compressed.encode('utf-8'))


def _apply_intelligent_truncation(conversation: List[Dict[str, str]], new_message: Dict[str, str], current_session_size: int) -> List[Dict[str, str]]:
    """
    Apply intelligent truncation logic that removes old messages first.
    
    Strategy:
    1. Calculate if adding new message would exceed threshold
    2. Remove oldest messages one by one until under threshold
    3. If new message alone is too large, truncate it as last resort
    
    Args:
        conversation: Current conversation history
        new_message: New message to add
        current_session_size: Current session size in bytes
        
    Returns:
        Conversation list that fits within session limits
    """
    # Session size thresholds (leaving room for Flask overhead)
    SESSION_LIMIT = 3200  # Conservative limit for total session
    MESSAGE_OVERHEAD = 200  # Estimated Flask session overhead per message
    
    # Add new message temporarily to test size
    test_conversation = conversation + [new_message]
    test_compressed = _compress_conversation(test_conversation)
    estimated_session_size = current_session_size + len(test_compressed.encode('utf-8'))
    
    logger.debug(f"Session size check: current={current_session_size}, estimated_with_new={estimated_session_size}, limit={SESSION_LIMIT}")
    
    # If we're under the limit, no truncation needed
    if estimated_session_size <= SESSION_LIMIT:
        logger.debug("No truncation needed - under session limit")
        return test_conversation
    
    # Strategy 1: Remove old messages until we fit
    logger.info(f"Session size ({estimated_session_size}) exceeds limit ({SESSION_LIMIT}). Removing old messages...")
    
    working_conversation = conversation.copy()
    messages_removed = 0
    
    while len(working_conversation) > 0:
        # Test if current conversation + new message fits
        test_conv = working_conversation + [new_message]
        test_compressed = _compress_conversation(test_conv)
        test_size = len(test_compressed.encode('utf-8')) + MESSAGE_OVERHEAD
        
        if test_size <= SESSION_LIMIT:
            logger.info(f"Truncation successful: removed {messages_removed} old messages, final size: {test_size}")
            return test_conv
        
        # Remove the oldest message and try again
        working_conversation.pop(0)
        messages_removed += 1
        logger.debug(f"Removed message {messages_removed}, remaining: {len(working_conversation)}")
    
    # Strategy 2: All old messages removed, but new message is still too large
    logger.warning("New message alone exceeds session limit. Truncating message content.")
    
    # Calculate how much we can keep of the new message
    max_content_size = SESSION_LIMIT - MESSAGE_OVERHEAD - 100  # Leave buffer
    
    if len(new_message['content']) > max_content_size:
        truncated_content = new_message['content'][:max_content_size-100]
        new_message['content'] = f"{truncated_content}..\n\n*[Response truncated - message too large for session storage]*"
        logger.info(f"Truncated new message content to fit session limit: {len(new_message['content'])} chars")
    
    return [new_message]


def _process_multimodal_content_light(content: str) -> str:
    """
    Light processing of multimodal content without aggressive truncation.
    Only removes base64 data and applies minimal compression.
    
    Args:
        content: Original message content
        
    Returns:
        Lightly processed content
    """
    # Remove base64 image data (can be very large)
    if 'data:image/jpeg;base64,' in content:
        content = content.replace('data:image/jpeg;base64,', '[image data removed]')
    
    # For very large content, apply minimal truncation as safety net
    if len(content) > 8000:  # Much more generous limit
        content = content[:7900] + '..\n\n*[Content lightly truncated for session efficiency]*'
    
    return content


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