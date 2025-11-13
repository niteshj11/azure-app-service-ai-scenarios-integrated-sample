# 🔧 Configuration Guide

## 📋 Overview

The TechMart AI Chatbot uses AIPlaygroundCode's intelligent configuration system that automatically detects the environment (local vs Azure) and manages settings appropriately.

## 🚀 Quick Setup (Minimum Configuration)

### After Local Deployment
1. **Start the application**: `python app.py`
2. **Open settings page**: http://127.0.0.1:5000/settings  
3. **Configure minimum required settings**:
   - ✅ **Azure AI Endpoint**: `https://your-endpoint.services.ai.azure.com/models`
   - ✅ **API Key**: Your Azure AI Foundry API key
   - ✅ **Model Name**: `gpt-4o-mini` (or your deployed model)
4. **Click "Save Settings"** → Settings saved to `AIPlaygroundCode/settings.json`
5. **Test the configuration**: Click "🧪 Test Config" button to verify connection

### After Azure Deployment  
1. **Open your Azure app**: `https://[your-app-name].azurewebsites.net/settings`
2. **Configure same minimum settings** (endpoint, API key, model)
3. **Click "Save Settings"** → Sensitive data goes to Azure Key Vault, non-sensitive to settings.json
4. **Test the configuration**: Verify Azure AI connection works

**That's all you need!** The application will work with default settings for all other options.

---

## 🔄 How Configuration Works

### **1. Configuration Storage by Environment**

**�️ Local Development:**
- **All settings** stored in: `AIPlaygroundCode/settings.json` 
- **Alternative**: `AIPlaygroundCode/settings.local.json` (if exists, takes priority)
- **Security**: Keep API keys in settings.local.json (not committed to git)

**☁️ Azure Production:**  
- **Sensitive data** → **Azure Key Vault** (endpoint, api_key)
- **Non-sensitive data** → `AIPlaygroundCode/settings.json` (deployed with app)
- **Automatic environment detection** based on Azure App Service indicators

### **2. Settings Retrieval Process**

**Local Priority Order:**
1. `AIPlaygroundCode/settings.local.json` (highest priority)
2. `AIPlaygroundCode/settings.json` (default)  
3. Environment variables (fallback)

**Azure Priority Order:**
1. Azure Key Vault secrets: `AZURE-AI-ENDPOINT`, `AZURE-AI-KEY` (sensitive data)
2. `AIPlaygroundCode/settings.json` (non-sensitive data)  
3. App Service environment variables (fallback)

### **3. Settings Save Process (via /settings page)**

**When you click "Save Settings":**
1. Form data sent to `/settings` POST endpoint
2. `AIPlaygroundCode.config.update_model_config()` processes the data
3. **Environment-aware saving**:
   - **Local**: All data → `AIPlaygroundCode/settings.json`
   - **Azure**: Sensitive data → Key Vault, rest → `settings.json`
4. Settings immediately take effect (no restart needed)

---

## ⚙️ Settings Options in /settings Page

### **🔐 Required Settings (Must Configure)**
- **Azure AI Endpoint** - Your Azure AI Foundry endpoint URL ending with `/models`  
- **API Key** - Azure AI Foundry API key (stored securely in Key Vault on Azure)
- **Model Name** - Deployed model name (e.g., `gpt-4o-mini`, `claude-3-5-sonnet-20241022`)

### **🔤 Basic Text Settings**
- **Audio Model Name** - Model for audio transcription (e.g., `gpt-4o-mini-audio-preview`)
- **Max Tokens** - Response length limit (1-4000, default: 2000)
- **Temperature** - Creativity level (0.0-1.0, default: 0.3)
- **System Message** - Instructions defining AI behavior and personality

### **🚀 Advanced Features (Optional)**
- **Enable Multimodal** - Image and audio upload support (requires compatible models)
- **Max Image Size** - Image upload limit in MB (1-20, default: 5)
- **Max Audio Size** - Audio upload limit in MB (1-50, default: 10)
- **Enable Reasoning** - Advanced problem-solving capabilities (for reasoning models)
- **Reasoning Effort** - Processing intensity: Low/Medium/High
- **Show Reasoning** - Display reasoning steps to users
- **Enable Structured Output** - Force JSON responses with schemas
- **Response Format** - Output format: Text/JSON Object/JSON Schema
- **JSON Schema** - Custom schema for structured responses
- **Schema Name** - Name for the JSON schema definition

### **🧪 Configuration Testing**
- **Test Config Button** - Validates Azure AI connection without saving
- **Real-time Validation** - Form validates endpoint format and required fields
- **Current Configuration Preview** - Shows all active settings after saving

### **� Responsive Interface** 
- **Auto-focus** - Highlights first empty required field
- **Mobile-friendly** - Works on all device sizes
- **Help Text** - Contextual guidance for each setting
- **Model Examples** - Lists compatible models by capability (text, multimodal, reasoning)

**Access**: Open `/settings` in your browser after deploying locally or to Azure.

---

## 🔐 Data Classification & Storage

### **🔒 Sensitive Data (Secured Storage)**
- **Azure AI Endpoint** - Service URL (Key Vault on Azure, settings.json locally)
- **API Key** - Authentication token (Key Vault on Azure, settings.json locally)

### **📄 Non-Sensitive Data (Configuration Files)**
- **Model Settings**: `model`, `audio_model`, `max_tokens`, `temperature`
- **Feature Flags**: `enable_multimodal`, `enable_reasoning`, `enable_structured_output`  
- **UI Settings**: `system_message`, `max_image_size`, `max_audio_size`
- **Application Config**: `upload_folder`, `session_timeout`, `debug`

### **💾 Storage Locations**

**Local Development:**
```
📁 AIPlaygroundCode/
├── 📄 settings.local.json     # ← All settings (preferred, not in git)
└── 📄 settings.json           # ← All settings (fallback, safe for git)
```

**Azure Production:**
```  
🔐 Azure Key Vault             # ← Sensitive only
├── AZURE-AI-ENDPOINT          
└── AZURE-AI-KEY              

📄 AIPlaygroundCode/settings.json  # ← Non-sensitive (deployed with app)

🌐 App Service Environment     # ← Fallback references  
├── @Microsoft.KeyVault(SecretUri=...)
└── Infrastructure variables
```

### **📋 Key Configuration Paths**
- **Settings File**: Always `AIPlaygroundCode/settings.json` (portable package structure)
- **Upload Directory**: `AIPlaygroundCode/uploads` (configured in settings.json)
- **Local Override**: `AIPlaygroundCode/settings.local.json` (takes priority if exists)

---

## 🧪 Testing & Validation

### **Configuration Testing (via Settings Page)**
```  
1. Open /settings in browser (local or Azure)
2. Fill in Azure AI endpoint and API key  
3. Click "🧪 Test Config" button
4. Results show connection status and model response
```

### **Manual Testing (Python)**
```python
# Test configuration loading
python -c "from AIPlaygroundCode.config import get_model_config; print(get_model_config().endpoint)"

# Test Azure AI connection  
python -c "from AIPlaygroundCode.utils.azure_client import test_azure_connection; print('✅ Connected' if test_azure_connection() else '❌ Failed')"

# Verify upload folder path
python -c "from AIPlaygroundCode.config import get_model_config; print(f'Upload folder: {get_model_config().upload_folder}')"
```

### **File Verification**
```powershell
# Check settings file exists and has upload_folder configured  
Select-String -Path "AIPlaygroundCode/settings.json" -Pattern "upload_folder"
# Should show: "upload_folder": "AIPlaygroundCode/uploads"

# Verify no sensitive data in committed settings.json
Select-String -Path "AIPlaygroundCode/settings.json" -Pattern "api_key|endpoint"
```

---

## 🎯 Key Benefits

✅ **Simple Setup**: Just endpoint + API key + model name to get started  
✅ **Environment Aware**: Automatically adapts to local vs Azure deployment  
✅ **Security**: Sensitive data in Key Vault (Azure) or local files only  
✅ **Portable**: AIPlaygroundCode package structure works anywhere  
✅ **User Friendly**: Web interface for all configuration management  
✅ **Testing**: Built-in connection testing and validation  

---

**💡 Quick Reference**: 
- **Local**: All settings in `AIPlaygroundCode/settings.json` (or `.local.json`)
- **Azure**: Sensitive data in Key Vault + non-sensitive in `settings.json`  
- **Settings page**: `/settings` - configure via web interface with real-time testing
- **Minimum config**: Endpoint + API Key + Model Name = Ready to use!