"""
Multimodal Scenario - Azure AI Foundry Multimodal Processing

Image and audio processing using Azure AI Foundry following Microsoft's patterns.
"""

import os
import logging
import base64
from typing import List, Dict
from werkzeug.datastructures import FileStorage
from ..utils.azure_client import get_azure_client
from ..utils.helpers import save_uploaded_file, get_conversation_history
from ..config import get_model_config, app_config

logger = logging.getLogger(__name__)

# Check for OpenAI SDK availability
try:
    from openai import AzureOpenAI
    OPENAI_SDK_AVAILABLE = True
except ImportError:
    OPENAI_SDK_AVAILABLE = False
    AzureOpenAI = None

# Supported file types
IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
AUDIO_EXTENSIONS = {'mp3', 'wav', 'ogg', 'm4a', 'flac'}


def handle_multimodal_message(user_message: str, uploaded_file: FileStorage) -> str:
    """
    Handle message with uploaded image or audio file.
    
    Demonstrates multimodal AI capabilities with file processing.
    Perfect example for applications that need to analyze images or transcribe audio.
    
    Args:
        user_message: User's text message
        uploaded_file: Uploaded file (image or audio)
        
    Returns:
        str: AI assistant's response including file analysis
        
    Raises:
        Exception: If file processing or Azure AI call fails
    """
    try:
        if not uploaded_file or not uploaded_file.filename:
            return handle_text_only_multimodal(user_message)
        
        # Save uploaded file
        file_path = save_uploaded_file(uploaded_file, app_config.upload_folder)
        if not file_path:
            raise Exception("Failed to save uploaded file")
        
        # Determine file type and process accordingly
        file_extension = get_file_extension(uploaded_file.filename)
        
        if file_extension in IMAGE_EXTENSIONS:
            response = process_image_message(user_message, file_path)
        elif file_extension in AUDIO_EXTENSIONS:
            response = process_audio_message(user_message, file_path)
        else:
            response = f"Unsupported file type: {file_extension}. Supported types: {IMAGE_EXTENSIONS | AUDIO_EXTENSIONS}"
        
        # Clean up uploaded file
        cleanup_file(file_path)
        
        logger.info(f"Successfully processed multimodal message with {file_extension} file")
        return response
        
    except Exception as e:
        logger.error(f"Error in multimodal scenario: {e}")
        raise Exception(f"Failed to process multimodal message: {str(e)}")


def process_image_message(user_message: str, image_path: str) -> str:
    """
    Process message with image using Azure AI vision capabilities.
    
    Args:
        user_message: User's text message
        image_path: Path to uploaded image file
        
    Returns:
        AI response analyzing the image
    """
    try:
        # Get Azure AI client
        client = get_azure_client()
        config = get_model_config()
        
        # Encode image to base64
        image_data = encode_image_to_base64(image_path)
        
        # Build multimodal messages
        messages = build_image_messages(user_message, image_data)
        
        # Handle both OpenAI SDK and azure.ai.inference
        if OPENAI_SDK_AVAILABLE and isinstance(client, AzureOpenAI):
            # Use OpenAI SDK interface
            response = client.chat.completions.create(
                messages=messages,
                **config.get_model_params()
            )
        else:
            # Use azure.ai.inference interface
            response = client.complete(
                messages=messages,
                **config.get_model_params()
            )
        
        return response.choices[0].message.content
        
    except Exception as e:
        logger.error(f"Error processing image: {e}")
        raise Exception(f"Failed to analyze image: {str(e)}")


def process_audio_message(user_message: str, audio_path: str) -> str:
    """
    Process message with audio file using Azure OpenAI audio capabilities.
    
    Uses GPT-4o audio preview models for direct audio transcription and analysis.
    Supports various audio formats and provides both transcription and intelligent analysis.
    
    Args:
        user_message: User's text message
        audio_path: Path to uploaded audio file
        
    Returns:
        Response with audio transcription and analysis
    """
    try:
        # Get Azure AI client
        client = get_azure_client()
        config = get_model_config()
        
        logger.info(f"Audio processing - Model: {config.model}, Audio Model: {config.audio_model}")
        
        # Check if we have an audio-capable model
        if not is_audio_model_available(config.audio_model):
            logger.warning(f"Audio model not available: {config.audio_model}, using fallback")
            return get_audio_fallback_response(user_message, audio_path)
        
        # Encode audio to base64
        audio_data = encode_audio_to_base64(audio_path)
        
        # Determine audio format
        audio_format = get_audio_format(audio_path)
        
        # Build audio processing messages
        messages = build_audio_messages(user_message, audio_data, audio_format)
        
        # Call Azure AI Foundry with audio capabilities using official SDK
        response = call_audio_model(audio_path, user_message)
        
        # Handle different response types
        if isinstance(response, str):
            # Fallback response (error case)
            return response
        
        # Extract transcription and response from successful API call
        response_content = response.choices[0].message.content
        
        # For audio models, the transcription is included in the content
        # Extract the actual transcription from the formatted response content
        audio_transcript = response_content if response_content else ""
        
        # Check if we have separate audio transcript available (fallback)
        if hasattr(response.choices[0].message, 'audio') and response.choices[0].message.audio:
            if hasattr(response.choices[0].message.audio, 'transcript'):
                audio_transcript = response.choices[0].message.audio.transcript
        
        # Format the complete response
        formatted_response = format_audio_response(
            response_content, 
            audio_transcript, 
            user_message, 
            os.path.basename(audio_path)
        )
        
        logger.info(f"Successfully processed audio message with Azure OpenAI audio model")
        return formatted_response
        
    except Exception as e:
        logger.error(f"Error processing audio with Azure OpenAI: {e}")
        # Fallback to basic response
        return get_audio_fallback_response(user_message, audio_path)


def handle_text_only_multimodal(user_message: str) -> str:
    """
    Handle multimodal scenario without file upload.
    
    Args:
        user_message: User's text message
        
    Returns:
        Response explaining multimodal capabilities
    """
    return (
        f"I can analyze images and process audio files! "
        f"Your message: {user_message}\n\n"
        "To use multimodal features:\n"
        "• Upload an image for visual analysis\n"
        "• Upload audio for transcription and analysis\n"
        f"Supported formats: Images ({', '.join(IMAGE_EXTENSIONS)}), "
        f"Audio ({', '.join(AUDIO_EXTENSIONS)})"
    )


def encode_image_to_base64(image_path: str) -> str:
    """
    Encode image file to base64 for Azure AI.
    
    Args:
        image_path: Path to image file
        
    Returns:
        Base64 encoded image data
    """
    with open(image_path, 'rb') as image_file:
        image_data = image_file.read()
        return base64.b64encode(image_data).decode('utf-8')


def build_image_messages(user_message: str, image_data: str) -> List[Dict]:
    """
    Build message array for Azure AI vision completion.
    
    Args:
        user_message: User's text message
        image_data: Base64 encoded image data
        
    Returns:
        List of messages for Azure AI multimodal call
    """
    config = get_model_config()
    messages = []
    
    # Use configured system message with vision context
    system_message = config.system_message + (
        "\n\nFor vision tasks, analyze images accurately and provide helpful insights. "
        "Describe what you see and answer questions about the image content."
    )
    
    # System message for vision tasks
    messages.append({
        "role": "system",
        "content": system_message
    })
    
    # Add conversation history (limited for token efficiency)
    conversation_history = get_conversation_history()[-5:]
    messages.extend(conversation_history)
    
    # Add current message with image
    messages.append({
        "role": "user",
        "content": [
            {"type": "text", "text": user_message},
            {
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/jpeg;base64,{image_data}"
                }
            }
        ]
    })
    
    return messages


def get_file_extension(filename: str) -> str:
    """
    Get file extension in lowercase.
    
    Args:
        filename: Original filename
        
    Returns:
        Lowercase file extension
    """
    return filename.rsplit('.', 1)[1].lower() if '.' in filename else ''


def cleanup_file(file_path: str) -> None:
    """
    Safely delete uploaded file after processing.
    
    Args:
        file_path: Path to file to delete
    """
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            logger.debug(f"Cleaned up file: {file_path}")
    except Exception as e:
        logger.warning(f"Failed to cleanup file {file_path}: {e}")


def encode_audio_to_base64(audio_path: str) -> str:
    """
    Encode audio file to base64 for Azure OpenAI audio processing.
    
    Args:
        audio_path: Path to audio file
        
    Returns:
        Base64 encoded audio data
    """
    with open(audio_path, 'rb') as audio_file:
        audio_data = audio_file.read()
        return base64.b64encode(audio_data).decode('utf-8')


def get_audio_format(audio_path: str) -> str:
    """
    Determine audio format from file path.
    
    Args:
        audio_path: Path to audio file
        
    Returns:
        Audio format string for Azure OpenAI
    """
    extension = get_file_extension(os.path.basename(audio_path))
    
    # Map file extensions to Azure OpenAI audio formats
    format_mapping = {
        'wav': 'wav',
        'mp3': 'mp3',
        'm4a': 'm4a',
        'ogg': 'ogg',
        'flac': 'flac'
    }
    
    return format_mapping.get(extension, 'wav')  # Default to wav


def is_audio_model_available(model_name: str) -> bool:
    """
    Check if the current model supports audio processing.
    
    Args:
        model_name: Name of the Azure AI model
        
    Returns:
        True if model supports audio, False otherwise
    """
    # Azure AI Foundry multimodal models that support audio
    audio_models = [
        'phi-4-multimodal-instruct',
        'phi-4-omni',
        'gpt-4o-audio-preview',
        'gpt-4o-mini-audio-preview'  # Add the mini audio model
    ]
    
    return any(audio_model in model_name.lower() for audio_model in audio_models)


def build_audio_messages(user_message: str, audio_data: str, audio_format: str) -> List[Dict]:
    """
    Build message array for Azure OpenAI audio processing.
    
    Args:
        user_message: User's text message
        audio_data: Base64 encoded audio data
        audio_format: Audio format (wav, mp3, etc.)
        
    Returns:
        List of messages for Azure OpenAI audio call
    """
    config = get_model_config()
    messages = []
    
    # Use configured system message with audio processing context
    system_message = config.system_message + (
        "\n\nFor audio processing, provide accurate transcription and intelligent analysis. "
        "For customer service calls, identify key issues, sentiment, and recommended actions. "
        "Always maintain a professional, helpful tone in your analysis."
    )
    
    # System message for audio processing
    messages.append({
        "role": "system",
        "content": system_message
    })
    
    # Add minimal conversation context
    conversation_history = get_conversation_history()[-3:]
    messages.extend(conversation_history)
    
    # Add current message with audio
    messages.append({
        "role": "user",
        "content": [
            {
                "type": "text", 
                "text": f"{user_message}\n\nPlease transcribe this audio and provide a detailed analysis including any customer service insights."
            },
            {
                "type": "input_audio",
                "input_audio": {
                    "data": audio_data,
                    "format": audio_format
                }
            }
        ]
    })
    
    return messages


def format_audio_response(response_content: str, transcript: str, user_message: str, filename: str) -> str:
    """
    Format the audio processing response for display.
    
    Args:
        response_content: AI's response content
        transcript: Audio transcription (if available)
        user_message: Original user message
        filename: Audio filename
        
    Returns:
        Formatted response string
    """
    formatted_response = f"🎤 **Audio Processing Complete**\n\n"
    formatted_response += f"**File**: {filename}\n"
    formatted_response += f"**Request**: {user_message}\n\n"
    
    if transcript and transcript.strip():
        formatted_response += f"**📝 Transcription:**\n{transcript}\n\n"
    
    formatted_response += f"**🧠 AI Analysis:**\n{response_content}\n\n"
    formatted_response += "✅ **Audio processed using Azure OpenAI audio capabilities**"
    
    return formatted_response


def call_audio_model(audio_file_path: str, user_message: str) -> str:
    """
    Call Azure AI Foundry audio model using the official Azure AI Inference approach.
    Following Microsoft's recommended pattern from the official documentation.
    
    Args:
        audio_file_path: Path to the audio file to process
        user_message: User's message/prompt for audio processing
        
    Returns:
        Processed response from the audio model
    """
    try:
        # Import Azure AI Inference SDK components
        from azure.ai.inference import ChatCompletionsClient
        from azure.ai.inference.models import (
            SystemMessage, 
            UserMessage, 
            TextContentItem, 
            AudioContentItem, 
            InputAudio, 
            AudioContentFormat
        )
        from azure.core.credentials import AzureKeyCredential
        from ..config import get_model_config
        
        config = get_model_config()
        
        # Create Azure AI Inference client following official docs
        client = ChatCompletionsClient(
            endpoint=config.endpoint,
            credential=AzureKeyCredential(config.api_key),
            model=config.audio_model  # Use the dedicated audio model
        )
        
        # Determine audio format from file extension
        file_ext = os.path.splitext(audio_file_path)[1].lower()
        if file_ext == '.mp3':
            audio_format = AudioContentFormat.MP3
        elif file_ext == '.wav':
            audio_format = AudioContentFormat.WAV
        else:
            raise Exception(f"Unsupported audio format: {file_ext}. Please use MP3 or WAV.")
        
        # Create messages using official Azure AI Inference models
        messages = [
            SystemMessage(
                "You are TechMart Enterprise's AI assistant with advanced audio processing capabilities. "
                "When processing audio, provide accurate transcription and intelligent analysis. "
                "For customer service calls, identify key issues, sentiment, and recommended actions. "
                "Always maintain a professional, helpful tone in your analysis."
            ),
            UserMessage(content=[
                TextContentItem(text=f"{user_message}\n\nPlease transcribe this audio and provide a detailed analysis including any customer service insights."),
                AudioContentItem(
                    input_audio=InputAudio.load(
                        audio_file=audio_file_path, 
                        audio_format=audio_format
                    )
                )
            ])
        ]
        
        # Handle both OpenAI SDK and azure.ai.inference
        if OPENAI_SDK_AVAILABLE and isinstance(client, AzureOpenAI):
            # Use OpenAI SDK interface
            response = client.chat.completions.create(
                messages=messages,
                temperature=0.3,
                max_tokens=2000
            )
        else:
            # Use azure.ai.inference interface
            response = client.complete(
                messages=messages,
                temperature=0.3,
                max_tokens=2000
            )
        
        return response
        
    except ImportError as e:
        logger.error(f"Azure AI Inference package not available: {e}")
        return get_audio_fallback_response(user_message, audio_file_path)
    except Exception as e:
        logger.error(f"Audio model call failed: {e}")
        return get_audio_fallback_response(user_message, audio_file_path)


def get_audio_fallback_response(user_message: str, audio_path: str) -> str:
    """
    Provide fallback response when audio models are not available.
    
    Args:
        user_message: User's text message
        audio_path: Path to uploaded audio file
        
    Returns:
        Fallback response explaining limitation
    """
    file_name = os.path.basename(audio_path)
    file_size_mb = os.path.getsize(audio_path) / (1024 * 1024)
    
    return (
        f"🎤 **Audio File Received**: {file_name} ({file_size_mb:.1f} MB)\n\n"
        f"**Request**: {user_message}\n\n"
        f"**Status**: Audio file uploaded successfully. Current model (`{get_model_config().model}`) "
        f"supports text and image processing. For audio transcription, configure an audio-capable model "
        f"or use Azure Speech Services.\n\n"
        f"**Available Features**: Text chat ✅ | Image analysis ✅ | Structured output ✅"
    )


