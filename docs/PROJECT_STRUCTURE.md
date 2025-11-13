# 🏗️ TechMart AI Chatbot - Project Structure

> **Complete guide to understanding the clean, optimized codebase structure**

## 📋 Overview

This document provides a comprehensive overview of the TechMart AI Chatbot project structure after cleanup and optimization. The codebase is organized with **AIPlaygroundCode** as a portable integration package and root-level deployment files.

## 📁 Root Directory Files

### Core Application Files
```
📄 app.py                    # Main Flask web application importing from AIPlaygroundCode - simple integration layer
📄 wsgi.py                   # Production WSGI entry point for Gunicorn server deployment on Azure App Service
📄 requirements.txt          # Python package dependencies for Azure deployment
📄 azure.yaml                # Azure Developer CLI (azd) configuration for automated deployment
📄 README.md                 # Project documentation with integration guide for existing Flask apps
```

---

## 📂 AIPlaygroundCode - Portable AI Package

**Purpose**: Self-contained AI chatbot functionality that can be integrated into any Flask application with minimal setup.

### Core Configuration
```
📄 AIPlaygroundCode/
├── 📄 __init__.py           # Package initialization with register_ai_routes() function for easy integration
├── 📄 config.py             # Complete configuration management with Azure AI settings, Key Vault integration, and environment detection
├── 📄 settings.json         # Application configuration with Azure AI credentials (upload_folder: "AIPlaygroundCode/uploads")
├── 📄 settings.json.template # Template showing required configuration structure  
└── 📄 settings.local.json.template # Local development configuration template
```

### AI Scenario Modules
```
� AIPlaygroundCode/scenarios/
├── 📄 __init__.py           # Package initialization for AI scenario handlers
├── 📄 chat.py               # Basic conversational AI with TechMart retail context
├── � reasoning.py          # Advanced problem-solving with chain-of-thought capabilities
├── 📄 structured_output.py  # JSON formatted responses for system integration
└── 📄 multimodal.py         # Image analysis and audio transcription functionality
```

### Utility Components  
```
📁 AIPlaygroundCode/utils/
├── 📄 __init__.py           # Package initialization for utility functions
├── 📄 azure_client.py       # Azure AI SDK integration and connection management
└── 📄 helpers.py            # Session management, file handling, and error formatting (improved truncation limits)
```

### Web Interface Templates
```
📁 AIPlaygroundCode/templates/
├── 📄 popup.html            # Main popup chat interface with file upload support for multimodal scenarios
├── 📄 retail_home.html      # TechMart retail interface with localStorage popup persistence  
├── 📄 settings.html         # Configuration management page for Azure AI credentials
├── 📄 config_error.html     # User-friendly configuration error page with troubleshooting
├── 📄 404.html              # Custom 404 error page
└── 📄 500.html              # Custom 500 error page
```

### Upload Directory
```
📁 AIPlaygroundCode/uploads/  # File upload storage for images and audio (created automatically)
```

---

## 🧪 Testing & Quality Assurance

### Test Suite
```
📁 tests/
├── 📄 test_config.py             # URL configuration for local/Azure testing (ESSENTIAL - used by all tests)
├── 📄 test_simple_chat.py        # Basic conversation testing with TechMart scenarios
├── 📄 test_reasoning_scenario.py # Advanced reasoning validation with problem-solving tests
├── 📄 test_structured_output.py  # JSON output format testing with schema validation
├── 📄 test_multimodal_image.py   # Image processing validation with product analysis
├── 📄 test_multimodal_audio.py   # Audio transcription testing with accuracy validation
├── 📄 html_report_generator.py   # Automated HTML test report generation
└── 📁 test_inputs/               # Test media files (images, audio samples)
```

---

## � Deployment Infrastructure

### Azure Infrastructure
```
� infra/                    # Bicep templates for Azure App Service deployment
├── 📄 main.bicep            # Main infrastructure template with App Service and Key Vault
├── 📄 api.bicep             # App Service configuration with environment variables
├── 📄 main.json             # Compiled ARM template from main.bicep
├── 📄 abbreviations.json    # Azure resource naming conventions
└── 📁 core/host/            # App Service hosting components
```

### Automation Scripts
```
📁 scripts/
├── 📄 cleanup_project.ps1          # Improved project cleanup (handles __pycache__, uploads folder, .pyc files)
└── 📄 clean-azd-environment.ps1    # Clean azd environment for fresh deployments
```

---

## 📄 Documentation

### Essential Documentation (5 files only)
```
📁 docs/
├── 📄 CONFIGURATION_GUIDE.md       # Azure AI setup and configuration instructions
├── 📄 TESTING_GUIDE.md            # Local and Azure testing procedures  
├── 📄 PROJECT_CLEANUP_INSTRUCTIONS.md # Project cleanup and optimization guide
├── � PROJECT_STRUCTURE.md        # This file - current project structure
└── 📄 AGENT_INSTRUCTIONS.md       # AI assistant development guidelines
```

---

## 🎯 Integration Summary

### For Existing Flask Apps
1. **Copy AIPlaygroundCode folder** to your project root
2. **Add one line**: `from AIPlaygroundCode import register_ai_routes; register_ai_routes(app)`
3. **Configure Azure AI**: Update `AIPlaygroundCode/settings.json`
4. **Add popup HTML**: Include popup integration code in your templates

### Key Benefits
- **✅ Portable**: Self-contained AIPlaygroundCode package
- **✅ Clean**: Optimized file structure with no redundancy
- **✅ Multimodal**: File upload support in popup interface
- **✅ Production-ready**: Proper upload folder management and error handling
- **✅ Well-tested**: Comprehensive test suite with automated reporting

### File Management
- **Upload folder**: Always `AIPlaygroundCode/uploads` (not root)
- **Configuration**: Single source in `AIPlaygroundCode/config.py`
- **Templates**: All in `AIPlaygroundCode/templates/`
- **Clean structure**: No duplicate config files or __pycache__ folders

---

## 📚 Documentation & Guides

### `/docs/` - Comprehensive Documentation
**Purpose**: Complete customer documentation including setup guides, deployment instructions, testing procedures, and troubleshooting resources

```
📁 docs/
├── 📄 PROJECT_STRUCTURE.md         # This comprehensive architecture guide explaining codebase organization, file purposes, and development workflow
├── 📄 CONFIGURATION_GUIDE.md       # Azure AI configuration and settings management with environment setup and credential handling
├── 📄 TESTING_GUIDE.md             # Comprehensive testing guide covering automated tests, manual procedures, and deployment validation
├── 📄 PROJECT_CLEANUP_INSTRUCTIONS.md # Project cleanup automation guide for production deployment preparation
└── 📄 AGENT_INSTRUCTIONS.md        # AI agent development guidelines and best practices for maintaining and extending the codebase
```

---

## 🗂️ Runtime & Development Folders

### Generated/Runtime Folders (Excluded from Customer Delivery)
```
📁 .git/                    # Git version control repository with commit history, branches, and development tracking (development environment only)
📁 .venv/                   # Python virtual environment with isolated package dependencies and development tools (local development only)
📁 .vscode/                 # Visual Studio Code workspace settings, debugging configurations, and development preferences (development only)
📁 __pycache__/             # Python bytecode cache with compiled modules for improved runtime performance (automatically generated)
📁 uploads/                 # User file uploads directory for images, audio, and document processing (runtime created and managed)
📁 .azure/                  # Azure CLI configuration and deployment state management (generated during deployment process)
� to_be_deleted/           # Temporary folder for obsolete files and test artifacts scheduled for cleanup (maintained empty for project organization)
�📄 app.log                  # Application runtime logs with error tracking, performance metrics, and diagnostic information (runtime generated)
```

### Empty/Unused Folders
```
📁 static/                  # Static web assets directory for CSS, JavaScript, and images (currently empty, available for future enhancements)
```

