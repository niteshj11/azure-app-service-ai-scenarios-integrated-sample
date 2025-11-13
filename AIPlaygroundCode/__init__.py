"""
AI Playground Package
Portable AI chatbot functionality for integration into existing Flask applications.
"""

from .config import get_model_config, update_model_config, is_configured

__version__ = "1.0.0"
__all__ = ["get_model_config", "update_model_config", "is_configured"]

# Package metadata
PACKAGE_INFO = {
    "name": "AI Playground",
    "version": __version__,
    "description": "Portable AI chatbot functionality for Flask applications",
    "author": "AI Playground Team",
    "license": "MIT"
}