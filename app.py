"""
Azure Linux App Service - AI Chatbot Sample Application

A clean, educational example of integrating Azure AI services with Flask
for Linux App Service customers. Demonstrates multiple AI scenarios with
best practices for production deployment.
"""

import logging
from flask import Flask, render_template, request, session, jsonify, redirect, url_for
import markdown
from markupsafe import Markup

# Import configuration and utilities from AIPlaygroundCode
from AIPlaygroundCode.config import app_config, get_model_config, update_model_config, is_configured
from AIPlaygroundCode.utils.helpers import (
    setup_logging, 
    get_conversation_history, 
    add_to_conversation, 
    clear_conversation,
    format_error_response,
    validate_message_input
)

# Import AI scenario modules from AIPlaygroundCode
from AIPlaygroundCode.scenarios.chat import handle_chat_message
from AIPlaygroundCode.scenarios.multimodal import handle_multimodal_message  
from AIPlaygroundCode.scenarios.reasoning import handle_reasoning_message
from AIPlaygroundCode.scenarios.structured_output import handle_structured_message

# Initialize Flask application with production settings
app = Flask(__name__, template_folder='AIPlaygroundCode/templates')
app.secret_key = app_config.secret_key
app.config['MAX_CONTENT_LENGTH'] = app_config.max_content_length
app.config['UPLOAD_FOLDER'] = app_config.upload_folder
app.config['PERMANENT_SESSION_LIFETIME'] = app_config.session_timeout

# Set up minimal logging for production
setup_logging(app_config.log_level)
logger = logging.getLogger(__name__)

# Add markdown filter for message rendering
@app.template_filter('markdown')
def markdown_filter(text):
    """Convert markdown text to HTML."""
    try:
        # Configure markdown with extensions for better rendering
        md = markdown.Markdown(extensions=[
            'codehilite',  # For code syntax highlighting
            'fenced_code',  # For ```code``` blocks
            'tables',       # For table support
            'toc'          # For table of contents
        ])
        return Markup(md.convert(text))
    except Exception as e:
        # Fallback to basic HTML escaping if markdown fails
        return Markup(text.replace('\n', '<br>').replace('**', '<strong>').replace('**', '</strong>'))


@app.before_request
def check_configuration():
    """Ensure Azure configuration is available and manage session size."""
    # Clean up oversized sessions to prevent cookie warnings
    try:
        # Check if session is getting too large
        session_size = len(str(session))
        if session_size > 3000:  # Conservative limit
            logger.warning(f"Large session detected ({session_size} bytes), cleaning up")
            
            # Simple session cleanup to avoid recursion - just clear conversation data
            session.pop('conversation_compressed', None)
            session.pop('conversation', None)
            session.modified = True
            
    except Exception as e:
        # Don't let session cleanup break the request
        logger.warning(f"Session cleanup failed: {e}")
    
    # Check Azure configuration
    if not is_configured() and request.endpoint not in ['configuration_error', 'static', 'settings', 'update_settings']:
        return redirect(url_for('configuration_error'))


@app.route('/config-error')
def configuration_error():
    """Display configuration error page."""
    return render_template('config_error.html'), 500


@app.route('/')
def index():
    """Default popup chat interface for retail website integration."""
    try:
        conversation = get_conversation_history()
        config = get_model_config()
        
        return render_template(
            'retail_home.html', 
            conversation=conversation,
            config=config.__dict__
        )
    except Exception as e:
        return format_error_response(e), 500





@app.route('/', methods=['POST'])
def chat():
    """
    Handle popup chat messages with different AI scenarios.
    
    Routes messages to appropriate scenario handlers based on 
    current configuration and message content.
    """
    try:
        # Check if Azure configuration is complete
        config = get_model_config()
        missing_configs = []
        
        if not config.endpoint or not config.endpoint.strip():
            missing_configs.append("Azure AI Endpoint")
        if not config.api_key or not config.api_key.strip():
            missing_configs.append("API Key")
        if not config.model or not config.model.strip():
            missing_configs.append("Model Name")
        
        if missing_configs:
            missing_list = "\n".join(f"- {item}" for item in missing_configs)
            add_to_conversation('assistant', 
                f"❌ **Configuration Required**\n\n"
                f"The following settings are missing or empty:\n{missing_list}\n\n"
                f"Please configure these settings before sending messages:\n"
                f"1. Click the **⚙️ Settings** button in the top right\n"
                f"2. Fill in all required fields\n"
                f"3. Click **Save Settings**\n\n"
                f"📋 **Required Settings:**\n"
                f"- **Azure AI Endpoint**: Your Azure AI service endpoint URL\n"
                f"- **API Key**: Your Azure AI service API key\n"
                f"- **Model Name**: The AI model to use (e.g., gpt-4o-mini)\n\n"
                f"Once all settings are configured, you can start chatting!"
            )
            return redirect(url_for('index'))
        
        # Get and validate user message
        user_message = request.form.get('message', '').strip()
        
        if not validate_message_input(user_message):
            return redirect(url_for('index'))
        
        # Add user message to conversation
        add_to_conversation('user', user_message)
        
        # Determine scenario and route to appropriate handler
        scenario = request.form.get('scenario', 'chat')
        uploaded_file = request.files.get('file') or request.files.get('audio') or request.files.get('image')
        
        if scenario in ['image', 'audio']:
            # Multimodal scenarios - require file upload
            if uploaded_file and uploaded_file.filename:
                response = handle_multimodal_message(user_message, uploaded_file)
            else:
                response = f"❌ **File Required for {scenario.title()} Analysis**\n\nPlease upload a {scenario} file to proceed with {scenario} analysis."
        elif uploaded_file and uploaded_file.filename:
            # Multimodal scenario with file upload (legacy support)
            response = handle_multimodal_message(user_message, uploaded_file)
        elif scenario == 'reasoning':
            # Advanced reasoning scenario
            response = handle_reasoning_message(user_message)
        elif scenario == 'structured':
            # Structured output scenario  
            response = handle_structured_message(user_message)
        else:
            # Default chat scenario
            response = handle_chat_message(user_message)
        
        # Add assistant response to conversation
        add_to_conversation('assistant', response)
        
    except Exception as e:
        error_message = format_error_response(e)
        add_to_conversation('assistant', error_message)
    
    return redirect(url_for('index'))


@app.route('/testing', methods=['POST'])
def testing_chat_handler():
    """
    Handle detailed testing interface messages with different AI scenarios.
    
    Similar to main chat handler but returns to testing interface.
    Routes messages to appropriate scenario handlers based on 
    current configuration and message content.
    """
    try:
        # Check if Azure configuration is complete
        config = get_model_config()
        missing_configs = []
        
        if not config.endpoint or not config.endpoint.strip():
            missing_configs.append("Azure AI Endpoint")
        if not config.api_key or not config.api_key.strip():
            missing_configs.append("API Key")
        if not config.model or not config.model.strip():
            missing_configs.append("Model Name")
        
        if missing_configs:
            missing_list = "\n".join(f"- {item}" for item in missing_configs)
            add_to_conversation('assistant', 
                f"❌ **Configuration Required**\n\n"
                f"The following settings are missing or empty:\n{missing_list}\n\n"
                f"Please configure these settings before sending messages:\n"
                f"1. Click the **⚙️ Settings** button\n"
                f"2. Fill in all required fields\n"
                f"3. Click **Save Settings**\n\n"
                f"📋 **Required Settings:**\n"
                f"- **Azure AI Endpoint**: Your Azure AI service endpoint URL\n"
                f"- **API Key**: Your Azure AI service API key\n"
                f"- **Model Name**: The AI model to use (e.g., gpt-4o-mini)\n\n"
                f"Once all settings are configured, you can start chatting!"
            )
            return redirect(url_for('testing_interface'))
        
        # Get and validate user message
        user_message = request.form.get('message', '').strip()
        
        if not validate_message_input(user_message):
            return redirect(url_for('testing_interface'))
        
        # Add user message to conversation
        add_to_conversation('user', user_message)
        
        # Determine scenario and route to appropriate handler
        scenario = request.form.get('scenario', 'chat')
        uploaded_file = request.files.get('file') or request.files.get('audio') or request.files.get('image')
        
        if scenario in ['image', 'audio']:
            # Multimodal scenarios - require file upload
            if uploaded_file and uploaded_file.filename:
                response = handle_multimodal_message(user_message, uploaded_file)
            else:
                response = f"❌ **File Required for {scenario.title()} Analysis**\n\nPlease upload a {scenario} file to proceed with {scenario} analysis."
        elif uploaded_file and uploaded_file.filename:
            # Multimodal scenario with file upload (legacy support)
            response = handle_multimodal_message(user_message, uploaded_file)
        elif scenario == 'reasoning':
            # Advanced reasoning scenario
            response = handle_reasoning_message(user_message)
        elif scenario == 'structured':
            # Structured output scenario  
            response = handle_structured_message(user_message)
        else:
            # Default chat scenario
            response = handle_chat_message(user_message)
        
        # Add assistant response to conversation
        add_to_conversation('assistant', response)
        
    except Exception as e:
        error_message = format_error_response(e)
        add_to_conversation('assistant', error_message)
    
    return redirect(url_for('testing_interface'))


@app.route('/settings')
def settings():
    """Configuration settings page."""
    try:
        config = get_model_config()
        message = session.pop('settings_message', None)
        return render_template('settings.html', config=config, message=message)
    except Exception as e:
        return format_error_response(e), 500


@app.route('/settings', methods=['POST'])
def update_settings():
    """Update all configuration settings."""
    try:
        # Extract all form data
        form_data = {}
        
        # Basic Azure settings
        form_data['endpoint'] = request.form.get('endpoint', '').strip()
        form_data['api_key'] = request.form.get('api_key', '').strip()
        
        # Model settings
        form_data['model'] = request.form.get('model', 'gpt-4o-mini')
        form_data['audio_model'] = request.form.get('audio_model', '')
        form_data['max_tokens'] = request.form.get('max_tokens', 1000)
        form_data['temperature'] = request.form.get('temperature', 0.7)
        form_data['system_message'] = request.form.get('system_message', '')
        
        # Advanced features - multimodal
        form_data['enable_multimodal'] = 'enable_multimodal' in request.form
        form_data['max_image_size'] = request.form.get('max_image_size', 5)
        form_data['max_audio_size'] = request.form.get('max_audio_size', 10)
        
        # Advanced features - reasoning
        form_data['enable_reasoning'] = 'enable_reasoning' in request.form
        form_data['reasoning_effort'] = request.form.get('reasoning_effort', 'medium')
        form_data['show_reasoning'] = 'show_reasoning' in request.form
        
        # Advanced features - structured output
        form_data['enable_structured_output'] = 'enable_structured_output' in request.form
        form_data['response_format'] = request.form.get('response_format', 'text')
        form_data['json_schema'] = request.form.get('json_schema', '')
        form_data['schema_name'] = request.form.get('schema_name', 'Response')
        
        # Validate required fields
        if not form_data['endpoint'] or not form_data['endpoint'].strip():
            session['settings_message'] = {
                'type': 'error',
                'text': 'Azure endpoint is required. Please enter your Azure AI Foundry endpoint URL.'
            }
            return redirect(url_for('settings'))
        
        if not form_data['api_key'] or not form_data['api_key'].strip():
            session['settings_message'] = {
                'type': 'error',
                'text': 'Azure API key is required. Please enter your Azure AI Foundry API key.'
            }
            return redirect(url_for('settings'))
        
        # Validate endpoint format
        if not form_data['endpoint'].startswith('https://'):
            session['settings_message'] = {
                'type': 'error',
                'text': 'Invalid endpoint format. Azure endpoint must start with "https://".'
            }
            return redirect(url_for('settings'))
        
        # Update configuration
        success = update_model_config(**form_data)
        
        if success:
            session['settings_message'] = {
                'type': 'success',
                'text': 'Settings saved successfully! All features are now configured.'
            }
        else:
            session['settings_message'] = {
                'type': 'error',
                'text': 'Failed to save settings. Please check file permissions.'
            }
        
        return redirect(url_for('settings'))
        
    except Exception as e:
        session['settings_message'] = {
            'type': 'error',
            'text': f'Error updating settings: {str(e)}'
        }
        return redirect(url_for('settings'))
    
    return redirect(url_for('settings'))


@app.route('/test_config', methods=['POST'])
def test_config():
    """Test current Azure AI configuration."""
    try:
        if not is_configured():
            return jsonify({
                'status': 'error',
                'message': 'Configuration incomplete. Please set Azure endpoint and API key in settings.'
            })
        
        # Test with a simple message
        from AIPlaygroundCode.scenarios.chat import handle_chat_message
        test_response = handle_chat_message("Hello, this is a test message.")
        
        config = get_model_config()
        return jsonify({
            'status': 'success',
            'message': 'Configuration test successful!',
            'model': config.model,
            'response': test_response[:100] + "..." if len(test_response) > 100 else test_response
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Configuration test failed: {str(e)}'
        })


@app.route('/clear')
def clear_chat():
    """Clear conversation history for popup interface (default)."""
    try:
        clear_conversation()
    except Exception:
        pass  # Fail silently for non-critical operation
    
    return redirect(url_for('index'))


@app.route('/testing/clear')
def clear_testing_chat():
    """Clear conversation history for testing interface."""
    try:
        clear_conversation()
    except Exception:
        pass  # Fail silently for non-critical operation
    
    return redirect(url_for('testing_interface'))


@app.route('/health')
def health_check():
    """Health check endpoint for monitoring."""
    try:
        from AIPlaygroundCode.utils.azure_client import test_azure_connection
        
        # Check session size
        session_size = len(str(session))
        conversation_count = len(get_conversation_history())
        
        status = {
            'status': 'healthy',
            'azure_configured': is_configured(),
            'azure_connection': test_azure_connection() if is_configured() else False,
            'session_size_bytes': session_size,
            'conversation_messages': conversation_count,
            'session_healthy': session_size < 3500  # Well under 4093 limit
        }
        
        return jsonify(status)
    except Exception as e:
        return jsonify({'status': 'unhealthy', 'error': str(e)}), 500


@app.route('/reset-config', methods=['POST'])
def reset_configuration():
    """Reset configuration to code defaults (admin endpoint)."""
    try:
        from AIPlaygroundCode.config import config_manager
        
        # Use the new reset method that preserves Azure credentials
        success = config_manager.reset_to_defaults()
        
        if success:
            return jsonify({'success': True, 'message': 'Configuration reset to code defaults'})
        else:
            return jsonify({'success': False, 'error': 'Failed to save configuration'}), 500
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# Scenario-specific routes for examples
@app.route('/examples/<scenario>')
def scenario_example(scenario):
    """Display scenario-specific examples."""
    try:
        template_name = f'examples/{scenario}_example.html'
        return render_template(template_name)
    except Exception:
        return redirect(url_for('index'))


@app.errorhandler(404)
def not_found_error(error):
    """Handle 404 errors."""
    return render_template('404.html'), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors."""
    return render_template('500.html'), 500


if __name__ == '__main__':
    """
    Run the application.
    
    For production deployment on Azure Linux App Service,
    use a proper WSGI server like Gunicorn instead.
    """
    app.run(
        host=app_config.host,
        port=app_config.port,
        debug=app_config.debug
    )