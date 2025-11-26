# 🧪 TechMart AI Chatbot - Testing Guide

This guide covers testing the TechMart AI Chatbot both locally and on Azure, with manual testing procedures and automated test scripts.

## 🏠 Local Testing

### Deploy Locally
```powershell
# 1. Install dependencies
pip install -r requirements.txt

# 2. Configure Azure AI Foundry credentials  
# Edit AIPlaygroundCode/settings.json with your Azure AI Foundry endpoint and API key

# 3. Start the application
python app.py
# Application runs at http://127.0.0.1:5000
```

### Manual Testing (Local)
1. **Open browser** to http://127.0.0.1:5000
2. **Test basic chat**: Type "Hello, can you help me?" 
3. **Test file uploads**: Use the 📎 button in popup to attach images/audio
4. **Test scenarios**:
   - Simple chat: "What laptops do you have?"
   - Reasoning: "Recommend a gaming laptop under $1500 and explain why"
   - Structured output: "Create a JSON list of 3 laptops with specs"
   - Image analysis: Upload a product image and ask "What is this?"
   - Audio processing: Upload an audio file for transcription

### Automated Testing (Local)  
```powershell
# Run all test scenarios locally
python tests/test_simple_chat.py popup local
python tests/test_reasoning_scenario.py popup local  
python tests/test_structured_output.py popup local
python tests/test_multimodal_image.py popup local
python tests/test_multimodal_audio.py popup local

# Quick basic tests (first scenario only)
python tests/test_simple_chat.py popup local basic
python tests/test_structured_output.py popup local basic
```

### Check Test Reports (Local)
- **HTML Reports**: Generated in `tests/reports/` directory  
- **Console Output**: Real-time pass/fail status and performance metrics
- **Report Content**: Detailed test results, screenshots, and AI response analysis

---

## ☁️ Azure Testing

### Deploy to Azure
```powershell
# Option 1: Fresh deployment (recommended)
.\scripts\clean-azd-environment.ps1  # Clean previous environments
azd up                              # Deploy to Azure (will prompt for settings)

# Option 2: Deploy to existing environment  
azd deploy                          # Deploy to existing Azure environment
```

**Deployment Results:**
- **Azure URL**: `https://[your-app-name].azurewebsites.net/`
- **Resources Created**: App Service, Azure AI Foundry resources (if new), Managed Identity configuration
- **Expected Time**: 3-5 minutes for complete deployment

### Manual Testing (Azure)
1. **Open Azure URL** in browser (from azd deployment output)
2. **Verify Azure AI Foundry Configuration** (automatic in most cases):
   - Configuration is usually automatic via Managed Identity
   - If needed: Click Settings (⚙️) → Verify Azure AI Foundry endpoint → Test Config
3. **Test all scenarios** (same as local testing):
   - Basic chat functionality
   - File upload capabilities (📎 button)
   - AI scenario responses
   - Popup interface behavior

### Automated Testing (Azure)
```powershell
# Run all test scenarios on Azure
python tests/test_simple_chat.py popup azure
python tests/test_reasoning_scenario.py popup azure
python tests/test_structured_output.py popup azure 
python tests/test_multimodal_image.py popup azure
python tests/test_multimodal_audio.py popup azure

# Quick validation tests (first scenario only)
python tests/test_simple_chat.py popup azure basic
python tests/test_structured_output.py popup azure basic
```

**Test Configuration:**
- Tests automatically detect Azure URL from `azd env get-values`
- No manual URL configuration needed
- Tests validate popup interface and file upload functionality

### Check Test Reports (Azure)
- **HTML Reports**: Same as local - generated in `tests/reports/`
- **Console Output**: Shows Azure URL being tested and response times
- **Success Criteria**: 
  - ✅ All tests should pass with "AZURE POPUP ✅ PASSED"
  - ✅ Response times should be reasonable (< 30 seconds)
  - ✅ File uploads should work correctly
  - ✅ AI responses should be relevant and properly formatted
3. **Pattern Matching**: Analyzes output for expected vs. unwanted prompts
4. **Safe Termination**: Stops azd up before actual resource provisioning
5. **Environment Restoration**: Restores original environment after testing

#### 🚀 Running azd Tests

**Quick Validation**
```powershell
# Run the main test (recommended)
.\tests\azd-tests\test-azd-final.ps1
```

**From Project Root**
```powershell
# All tests can be run from project root
.\tests\azd-tests\test-azd-final.ps1
```

#### 📋 Expected Test Output

When tests pass, you should see:
- ✅ **No resource group prompts detected**
- ✅ **No environment name prompts detected** 
- ✅ **Bicep provider initialization**
- ✅ **Configuration loaded from azure.yaml**
- ⚠️ **Process terminated before resource creation** (by design)

#### 🔧 Troubleshooting azd Tests

If tests fail:
1. Check `azure.yaml` configuration
2. Verify azd CLI installation: `azd version`
3. Ensure authenticated: `azd auth login --check-status`
4. Review detailed log files for specific errors

### 🤖 AI Application Tests
Automated tests for validating the AI chatbot functionality across different scenarios.

| File | Purpose | Usage |
|------|---------|-------|
| `test_simple_chat.py` | Basic chat functionality | `python tests/test_simple_chat.py popup azure basic` |
| `test_structured_output.py` | JSON/structured response validation | `python tests/test_structured_output.py popup azure basic` |
| `test_reasoning_scenario.py` | Complex reasoning capabilities | `python tests/test_reasoning_scenario.py popup azure basic` |
| `test_multimodal_image.py` | Image processing features | `python tests/test_multimodal_image.py popup azure basic` |
| `test_multimodal_audio.py` | Audio processing features | `python tests/test_multimodal_audio.py popup azure basic` |

### 📊 Test Infrastructure
Supporting files for test execution and reporting.

| File | Purpose |
|------|---------|
| `test_config.py` | Centralized URL configuration with dynamic azd environment integration |
| `html_report_generator.py` | Automated HTML test report generation |
| `test_inputs/` | Sample media files for multimodal testing |

---

## 🚀 Quick Testing Workflow

### 1. Deploy Application
```powershell
# Deploy to Azure
azd up

# Configure Azure AI credentials via settings page
# Run all tests
python tests/test_simple_chat.py popup azure basic
```

### 2. Test Parameters
- **Interface**: `popup` (main interface) or `regular` (testing interface)
- **Environment**: `azure` (deployed app) or `local` (local development)
- **Mode**: `basic` (first test only) or omit for all tests

---

## 🖥️ Terminal Management

**⚠️ CRITICAL: You need TWO terminal windows for proper testing:**

1. **Flask App Terminal** (Primary) - Runs the web application
   - Purpose: Keeps the Flask app running continuously
   - Status: Shows real-time request logs and errors
   - Action: Start `python app.py` and LEAVE OPEN

2. **Testing Terminal** (Secondary) - For additional commands if needed
   - Purpose: Run additional scripts or commands during testing
   - Status: Available for troubleshooting or additional testing
   - Action: Use for any extra commands while Flask runs

**📝 Why Two Terminals?**
- Flask app blocks the terminal (runs continuously)
- You need to see real-time logs for debugging
- Separate terminal available for emergency commands
- Proper testing workflow requires monitoring both app status and test results

**💡 PowerShell Command Examples:**
```powershell
# Generic project path
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd 'C:\path\to\your\project'; python app.py"

# With virtual environment
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd 'C:\path\to\your\project'; & '.\\.venv\\Scripts\\python.exe' app.py"

# Example with actual path
```powershell
# Then start the application in a separate terminal
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$(Get-Location)'; & '$(Get-Location)\.venv\Scripts\python.exe' app.py"
```
```

---

## 🎯 Manual Testing Procedures

### Pre-Testing Setup

#### 1. Start the Application in Separate Terminal
**⚠️ IMPORTANT: Always run the Flask app in a separate terminal/window for testing**

**Option A: Launch in Separate Terminal (Recommended)**
```powershell
# From current project directory, launch Flask app in new terminal window
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$pwd'; python app.py"

# Alternative: If using virtual environment
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$pwd'; & '.\.venv\Scripts\python.exe' app.py"
```

**Option B: Run in Current Terminal (Will Block)**
```powershell
# Navigate to project directory first
cd "path\to\your\TechMart-AI-Chatbot"

# Run the Flask app (this will block the terminal)
python app.py
```

**Option C: Direct Flask Execution**
```powershell
# Alternative method
python -m flask run --host=0.0.0.0 --port=5000
```

#### 2. Verify Application is Running
- Flask app should show: `Running on http://127.0.0.1:5000`
- Open browser to: http://127.0.0.1:5000
- You should see the TechMart AI Chatbot interface

#### 3. Configure Azure AI (If Not Already Done)
If you see "Configuration Error" or need to set up Azure AI:
1. Click the settings (⚙️) button
2. Enter your Azure AI credentials:
   - **Azure AI Endpoint**: Your Azure AI service endpoint
   - **Azure AI API Key**: Your Azure AI service API key
   - **Chat Deployment Name**: Your GPT model deployment name
   - **Embedding Deployment Name**: Your embedding model deployment name
3. Click "Save Configuration"

---

## 🔍 Manual Test Scenarios

### Test 1: Simple Chat Functionality
**Purpose**: Verify basic conversational AI capabilities

1. **Navigate**: Go to http://127.0.0.1:5000
2. **Action**: Type a simple greeting: "Hello, can you help me?"
3. **Expected**: Bot responds with helpful greeting
4. **Verify**: Response is relevant and properly formatted

### Test 2: TechMart Retail Scenarios
**Purpose**: Test domain-specific retail knowledge

1. **Product Inquiry**: "What laptops do you have available?"
2. **Expected**: Bot provides product information or asks clarifying questions
3. **Price Check**: "What's the price of the ThinkPad X1?"
4. **Expected**: Bot responds with pricing information or requests more details

### Test 3: Structured Output
**Purpose**: Verify JSON/structured response generation

1. **Request**: "Create a JSON list of 3 popular laptops with their specs"
2. **Expected**: Bot returns properly formatted JSON structure
3. **Verify**: JSON is valid and contains requested information

### Test 4: Reasoning Capabilities
**Purpose**: Test complex problem-solving abilities

1. **Complex Question**: "A customer wants a laptop for gaming under $1500. What would you recommend and why?"
2. **Expected**: Bot provides reasoned recommendation with justification
3. **Follow-up**: "What if they also need it for video editing?"
4. **Expected**: Bot adjusts recommendation based on new requirements

### Test 5: Image Analysis (Multimodal)
**Purpose**: Test visual AI capabilities

1. **Action**: Upload a product image using the image upload feature
2. **Request**: "What product is this and what can you tell me about it?"
3. **Expected**: Bot analyzes image and provides product description
4. **Verify**: Analysis is accurate and detailed

### Test 6: Audio Processing (Multimodal)
**Purpose**: Test audio transcription and analysis

1. **Action**: Upload an audio file using the audio upload feature
2. **Request**: "Transcribe this audio and summarize the customer's needs"
3. **Expected**: Bot transcribes audio and provides summary
4. **Verify**: Transcription is accurate and summary is relevant

---

## 🔧 Troubleshooting Manual Tests

### Common Issues and Solutions

#### Application Won't Start
**Symptoms**: Flask app fails to start or crashes
**Solutions**:
1. Check Python dependencies: `pip install -r requirements.txt`
2. Verify Python version: `python --version` (should be 3.11+)
3. Check for port conflicts: Try different port `python app.py --port=5001`

#### Configuration Error
**Symptoms**: "Configuration Error" message appears
**Solutions**:
1. Check `settings.json` file exists and has proper format
2. Verify Azure AI Foundry credentials are correct (for local) or Managed Identity permissions (for Azure)
3. Test Azure AI Foundry endpoint connectivity
4. For Azure: Verify `AZURE_INFERENCE_ENDPOINT` environment variable is set

#### No AI Response
**Symptoms**: Chat interface loads but bot doesn't respond
**Solutions**:
1. Check Flask terminal for error messages
2. Verify Azure AI Foundry service is accessible
3. For local: Check API key permissions and quotas
4. For Azure: Verify Managed Identity has proper roles (Cognitive Services OpenAI User, Azure AI Developer)
5. Review configuration settings and model deployment status

#### Image/Audio Upload Fails
**Symptoms**: Multimodal features don't work
**Solutions**:
1. Check file size limits (typically 16MB max)
2. Verify file format is supported
3. Check upload directory permissions
4. Monitor Flask logs for upload errors

---

## 📊 Automated Test Execution

### Running All Tests
```powershell
# Run complete test suite for Azure deployment
python tests/test_simple_chat.py popup azure
python tests/test_structured_output.py popup azure
python tests/test_reasoning_scenario.py popup azure
python tests/test_multimodal_image.py popup azure
python tests/test_multimodal_audio.py popup azure
```

### Running Basic Tests (First Scenario Only)
```powershell
# Quick validation with basic mode
python tests/test_simple_chat.py popup azure basic
python tests/test_structured_output.py popup azure basic
```

### Running Local Tests
```powershell
# Test against local development server
python tests/test_simple_chat.py popup local basic
```

### Azure Deployment Validation
```powershell
# Test azd deployment process
.\tests\azd-tests\test-azd-final.ps1
```

---

## 📈 Test Reporting

### HTML Reports
- Generated automatically in `tests/reports/` directory
- Include detailed test results, screenshots, and performance metrics
- Open in browser for comprehensive test analysis

### Console Output
- Real-time test progress and results
- Pass/fail status for each test scenario
- Performance timing and response analysis

---

## 🎯 Success Criteria

### Manual Testing Success
- ✅ All test scenarios complete without errors
- ✅ AI responses are relevant and accurate
- ✅ Multimodal features work correctly
- ✅ No configuration or connectivity issues

### Automated Testing Success
- ✅ All test scripts return "PASSED" status
- ✅ HTML reports show green status indicators
- ✅ Response times within acceptable limits
- ✅ No HTTP errors or exceptions
- ✅ For Azure: Managed Identity authentication working correctly

### Deployment Testing Success
- ✅ `azd up` completes without unexpected prompts
- ✅ Application accessible at deployed URL
- ✅ All features work in production environment

---

## 📚 Additional Resources

- **Configuration**: See `docs/CONFIGURATION_GUIDE.md` for detailed setup
- **Project Structure**: See `docs/PROJECT_STRUCTURE.md` for codebase organization  
- **Deployment**: See `README.md` for deployment instructions
- **Troubleshooting**: Check Flask terminal logs for detailed error information