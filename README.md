# 🎯 Azure AI Scenarios - Sample Application for App Service

This sample application demonstrates how to implement various AI scenarios on Azure App Service using Azure AI Foundry. It provides production-ready code that you can integrate into your existing Flask applications by copying the `AIPlaygroundCode` package and following the integration steps.

**Ideal for**: Developers looking to add AI capabilities to existing Flask applications, learn Azure AI Foundry integration patterns, and implement enterprise-grade AI features with minimal setup effort.

## 🎯 Key Scenarios Covered

🤖 **Conversational AI**: Natural language processing with context awareness and session management  
🧠 **Reasoning Models**: Advanced problem-solving using o1-mini, o1-preview, and deepseek-r1 models  
📋 **Structured Output**: JSON-formatted responses with schema validation for system integration  
🎭 **Multimodal Processing**: Image analysis and audio transcription using vision and audio models  
🏪 **Enterprise Chat**: Retail-optimized AI assistant with TechMart customer service scenarios

## 🚀 Quick Start - Azure Deployment (Recommended)

### Prerequisites
- [Azure CLI](https://docs.microsoft.com/en-us/cli/azure/install-azure-cli) installed
- [Azure Developer CLI (azd)](https://docs.microsoft.com/en-us/azure/developer/azure-developer-cli/install-azd) installed
- Azure subscription with contributor access
- [Azure AI Foundry](https://ai.azure.com) access with **two model deployments**:
  - **Chat/Reasoning/Image model**: `gpt-4o-mini` or similar for conversational AI, reasoning, and image analysis
  - **Audio model**: `gpt-4o-mini-audio-preview` or similar for audio transcription and processing

### One-Command Deployment

1. **Clone and Deploy**
   ```bash
   git clone <repository-url>
   cd ChatBotOpenAIAppService
   azd up
   ```

2. **Configure AI Settings During Deployment**
   During `azd up`, you'll be prompted to configure AI setup:
   
   **AI Setup Choice**: Choose between:
   - **`new`**: Creates new Azure AI services automatically (recommended for testing)
   - **`existing`**: Use your existing Azure AI Foundry project
   
   **If you choose `existing`, you'll be prompted for**:
   - **AI Foundry Endpoint**: Enter your project endpoint (e.g., `https://myproject.openai.azure.com/`)
   - **Chat Model Name**: Your chat deployment name (e.g., `gpt-4o-mini`)
   - **Audio Model Name**: Your audio deployment name (e.g., `gpt-4o-mini-audio-preview`)
   
   **Configuration is automatic** - no manual settings page needed!

3. **Test Your Application**
   - Click "🧪 Test Config" to verify connection, then start using AI scenarios!
   - Refer to Usage Examples section below to test manually with sample scenarios

### What Gets Deployed
- ✅ **Azure App Service** (Basic B2 SKU) with Python 3.11 - Estimated cost: ~$27/month
- ✅ **Managed Identity** with proper RBAC permissions - No additional cost
- ✅ **Azure AI Foundry resources** (if `new` option chosen):
  - AI Services account with model deployments
  - AI Project workspace
  - Storage account for AI project data
- ✅ All necessary Azure resources configured automatically with environment variables

## 🖥️ Local Development Setup

### Prerequisites
- Python 3.8+ 
- [Azure AI Foundry](https://ai.azure.com) access with **two model deployments**:
  - **Chat/Reasoning/Image model**: `gpt-4o-mini` or similar for conversational AI, reasoning, and image analysis
  - **Audio model**: `gpt-4o-mini-audio-preview` or similar for audio transcription and processing

### Installation & Setup

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Launch Application**
   ```bash
   python app.py
   ```

3. **Configure AI Settings**
   Open http://localhost:5000/settings and configure:
   - ✅ **Azure AI Endpoint**: `https://your-endpoint.services.ai.azure.com/models`
   - ✅ **API Key**: Your Azure AI Foundry API key *(Note: For production, use Managed Identity instead)*
   - ✅ **Model Name**: Your deployed model name (e.g., `gpt-4o-mini`)
   - ✅ **Model Name (Audio)**: Your audio model (e.g., `gpt-4o-mini-audio-preview`)

4. **Test Your Application**
   - Click "🧪 Test Config" to verify connection, then start using AI scenarios!
   - Refer to Usage Examples section below to test manually with sample scenarios

## 💡 Usage Examples

*[Screenshot placeholder: Add application screenshot showing the main interface]*

**Getting Started**: Click the floating 🤖 AI chat button (bottom-right corner) to open the AI chat interface, then try these examples:

**🤖 Conversational AI**: 
- **Test Message**: "Who are you and what can you help with?"
- **Expected Response**: AI identifies as TechMart Enterprise AI Assistant, explains customer service and business intelligence capabilities

**🛍️ Product Inquiry**:
- **Test Message**: "Tell me about features and price for Pro Gaming X1" 
- **Expected Response**: Details about $1699 price, RTX 4070, Intel i7, 16GB RAM, 1TB SSD specifications

**📞 Customer Service**:
- **Test Message**: "What is TechMart's return policy and how do I process a customer refund?"
- **Expected Response**: 30-day return policy, receipt requirements, customer service contact information

**🎭 Multimodal Processing**: 
- **Image Analysis**: 
  - **Test Message**: "Analyze this laptop and tell me its specifications"
  - **Action**: Upload product images from `tests/test_inputs/laptop.jpeg` using the 📎 button
  - **Expected Response**: Detailed analysis of laptop specifications, features, and condition
- **Audio Processing**: 
  - **Test Message**: "Transcribe this customer service call"
  - **Action**: Upload audio files from `tests/test_inputs/test_customer_service_audio.mp3` using the 📎 button
  - **Expected Response**: Accurate transcription with customer service context analysis

**Sample Test Files Available**: Browse `tests/test_inputs/` folder for sample images and audio files to test multimodal capabilities.

## 🎯 Integration with Existing Applications

This section provides guidance for integrating AI capabilities into your existing Flask applications. Note that this requires additional Azure resource setup and dependency management.

### Prerequisites for Integration
- Existing Flask application with Azure App Service and App Service Plan
- Azure AI Foundry access with model deployments
- Managed Identity configured for App Service to access Azure AI Foundry endpoints

### Step 1: Set Up Azure Resources

**Configure App Service Managed Identity:**
```bash
# Enable system-assigned managed identity for your App Service
az webapp identity assign --name <your-app-name> --resource-group <your-rg>

# Grant Azure AI Developer role to your App Service for existing AI Foundry resources
az role assignment create \
  --role "Cognitive Services OpenAI User" \
  --assignee <managed-identity-principal-id> \
  --scope <your-ai-foundry-resource-id>
```

### Step 2: Copy and Merge Files

**Copy the AIPlaygroundCode folder:**
```bash
cp -r AIPlaygroundCode/ /path/to/your-existing-app/
```

**Merge Dependencies (Important!):**
- **requirements.txt**: Merge the dependencies from this sample's `requirements.txt` with your existing requirements file
- **wsgi.py**: If you have an existing `wsgi.py`, ensure it properly references your Flask app instance
- **app.py routes**: Copy the AI-related routes from the sample `app.py` to your existing Flask application

**Example requirements.txt merge:**
```txt
# Your existing dependencies
flask==2.3.3
# ... your other dependencies

# Add these AI-related dependencies from the sample
azure-identity==1.15.0
openai==1.35.13
pillow==10.0.0
pydub==0.25.1
```

### Step 3: Update App Service Configuration

**Add AI configuration as App Service environment variables:**
```bash
# Add AI configuration as App Service environment variables
az webapp config appsettings set --name <your-app-name> --resource-group <your-rg> --settings \
  AZURE_INFERENCE_ENDPOINT="https://your-endpoint.services.ai.azure.com/models" \
  AZURE_CLIENT_ID="system-assigned-managed-identity" \
  AZURE_AI_CHAT_DEPLOYMENT_NAME="gpt-4o-mini" \
  AZURE_AI_AUDIO_DEPLOYMENT_NAME="gpt-4o-mini-audio-preview"
```

**Note**: These environment variables will be automatically configured if you use `azd up` with this template.

### Step 4: Add AI Routes to Your Flask App

Add these imports and routes to your existing Flask application:
```python
# Add these imports to your existing app.py
from AIPlaygroundCode.config import get_model_config, update_model_config, is_configured
from AIPlaygroundCode.scenarios.chat import handle_chat_message
from AIPlaygroundCode.scenarios.multimodal import handle_multimodal_message

# Add AI configuration routes
@app.route('/settings')
def settings():
    from flask import render_template
    config = get_model_config()
    return render_template('AIPlaygroundCode/templates/settings.html', config=config)

@app.route('/settings', methods=['POST'])
def update_settings():
    # Copy the complete settings update logic from the sample app.py
    # This includes form handling, validation, and configuration updates
    pass

# Add AI chat routes
@app.route('/chat', methods=['POST'])
def chat():
    # Copy the complete chat logic from the sample app.py
    pass

@app.route('/multimodal', methods=['POST'])
def multimodal():
    # Copy the complete multimodal logic from the sample app.py  
    pass
```

### Step 5: Add AI Interface to Your Templates

Add this floating AI chat button to your existing HTML templates:
```html
<!-- Add this floating AI chat button to your templates -->
<div id="ai-chat-popup" style="position: fixed; bottom: 20px; right: 20px; z-index: 1000;">
    <button onclick="openAIChat()" style="background: #0078d4; color: white; border: none; border-radius: 50%; width: 60px; height: 60px; font-size: 24px; cursor: pointer;">🤖</button>
</div>
<script>
function openAIChat() {
    window.open('/settings', '_blank', 'width=800,height=600');
}
</script>
```

### Important Considerations:
- 🔐 **Security**: Uses Managed Identity for secure authentication, no API keys needed
- 🏗️ **Dependencies**: Carefully merge `requirements.txt` to avoid version conflicts
- ⚙️ **Configuration**: Update App Service settings with environment variables
- 🔧 **Routes**: Copy complete route logic from sample app.py, not just imports
- 🎯 **Testing**: Test thoroughly after integration to ensure existing functionality isn't affected

#### What You Get After Integration:
- 🎯 **New Routes**: `/settings`, `/chat`, `/multimodal` for AI capabilities
- ⚙️ **Settings Page**: Self-service configuration interface for AI endpoints
- 💬 **AI Chat Interface**: Floating AI assistant accessible from any page
- 🔐 **Secure Configuration**: Managed Identity authentication with Azure AI Foundry  

## 🧹 Resource Clean-up

To prevent incurring unnecessary charges, it's important to clean up your Azure resources after completing your work with the application.

### When to Clean Up
- After you have finished testing or demonstrating the application
- If the application is no longer needed or you have transitioned to a different project
- When you have completed development and are ready to decommission the application

### Removing Azure Resources
To delete all associated resources and shut down the application, execute the following command:
```bash
azd down
```
Please note that this process may take up to 10 minutes to complete.

⚠️ **Alternative:** You can delete the resource group directly from the Azure Portal to clean up resources.

---

## ❓ FAQ & Troubleshooting

### **Q: How do I add AI to my existing Flask application?**
**A:** See the [Easy Integration for Existing Apps](#-easy-integration-for-existing-apps) section above for step-by-step instructions.

### **Q: What Azure AI models are supported?**  
**A:** All Azure AI Foundry models including GPT-4o, Claude-3.5, o1-mini/preview, deepseek-r1, and multimodal models. Configure your deployed model name in settings.

### **Q: How do I enable multimodal capabilities?**
**A:** Enable "Multimodal" in `/settings` and ensure your model supports vision/audio (like gpt-4o, phi-4-multimodal). Upload images/audio via the 📎 button.

### **Q: How do I use reasoning model capabilities?**
**A:** Enable "Reasoning" in `/settings` and use models like `o1-mini`, `o1-preview`, or `deepseek-r1`. These models provide advanced problem-solving and step-by-step reasoning. Set "Reasoning Effort" to control depth (low/medium/high) and enable "Show Reasoning" to see the thinking process.

### **Q: How do I use structured input/output capabilities?**
**A:** Enable "Structured Output" in `/settings`, set "Response Format" to "JSON", and define a JSON schema in the "JSON Schema" field. The AI will return responses matching your specified schema structure, perfect for system integration and data processing workflows.

### **Troubleshooting Common Deployment Issues**

**❌ "Endpoint not found" or 401 Authentication errors:**
- Verify your Azure AI Foundry endpoint URL ends with `/models` 
- Ensure Managed Identity has proper permissions (Cognitive Services OpenAI User role)
- Use the "🧪 Test Config" button to validate connection
- Check that your model deployment is active in Azure AI Foundry

**❌ Azure deployment fails with "azd up" command:**
- Ensure you have Contributor access to your Azure subscription
- Check if you've reached subscription limits for App Service or AI services
- Try running `azd auth login` to refresh your authentication
- Clear previous deployments with `azd down` before retrying

**❌ Application not starting after deployment:**
- Check App Service logs in Azure portal for detailed errors (under Monitoring > Log stream)
- Verify Managed Identity permissions are properly configured for AI resources
- Ensure all required environment variables are set in App Service Configuration
- Review deployment logs for any missing dependencies or configuration issues

**❌ "ModuleNotFoundError" or dependency issues:**
- Verify all files from `requirements.txt` were properly deployed
- Check Python version compatibility (requires Python 3.8+)
- Review deployment logs in Azure App Service for package installation errors

**❌ File upload failures (multimodal scenarios):**
- Check file size limits (images: 5MB, audio: 10MB by default)
- Verify supported file formats (JPEG, PNG for images; MP3, WAV for audio)
- Ensure "Enable Multimodal" is checked in settings
- Confirm your model supports multimodal capabilities

---



## 📊 Guidance

### Costs
Pricing varies per region and usage, so it isn't possible to predict exact costs for your usage. The majority of Azure resources used in this infrastructure are on usage-based pricing tiers.

You can try the [Azure pricing calculator](https://azure.microsoft.com/pricing/calculator) for the resources:

- **Azure App Service**: Basic B2 tier with 3.5 GB RAM, 10 GB storage. [Pricing](https://azure.microsoft.com/pricing/details/app-service/windows/)
- **Azure AI Services**: Consumption-based pricing for model usage (tokens). [Pricing](https://azure.microsoft.com/pricing/details/cognitive-services/openai-service/)
- **Azure Storage Account**: Standard LRS for AI project data (minimal cost). [Pricing](https://azure.microsoft.com/pricing/details/storage/)

⚠️ **Cost Management**: To avoid unnecessary costs, remember to clean up your resources when no longer needed by running `azd down` or deleting the resource group in the Azure Portal.

### Security Guidelines
This template uses [Managed Identity](https://learn.microsoft.com/entra/identity/managed-identities-azure-resources/overview) for secure authentication between Azure services.

**Additional Security Measures to Consider:**
- Enable [Microsoft Defender for Cloud](https://learn.microsoft.com/azure/defender-for-cloud/) to secure your Azure resources
- Implement network security with [Virtual Networks](https://learn.microsoft.com/azure/app-service/networking-features) for App Service
- Configure [Azure Web Application Firewall](https://learn.microsoft.com/azure/web-application-firewall/) for additional protection
- Enable [GitHub secret scanning](https://docs.github.com/code-security/secret-scanning/about-secret-scanning) in your repository

> **⚠️ Important Security Notice**  
> This template has been built to showcase Azure AI services and tools. We strongly recommend implementing additional security features before using this code in production environments.

For comprehensive security best practices for AI applications, visit our [official documentation](https://learn.microsoft.com/azure/ai-foundry/).

---

## ⚖️ Disclaimers

**Software Usage and Compliance:**
To the extent that this software includes components or code used in or derived from Microsoft products or services, including Microsoft Azure Services, you must comply with the Product Terms applicable to such Microsoft Products and Services. Nothing in this license will serve to supersede, amend, terminate, or modify any terms in the Product Terms for any Microsoft Products and Services.

**Export Regulations:**
You must comply with all domestic and international export laws and regulations that apply to the software, which include restrictions on destinations, end users, and end use. For further information on export restrictions, visit [https://aka.ms/exporting](https://aka.ms/exporting).

**Medical and Financial Services Disclaimer:**
This software is not designed, intended, or made available as a medical device, and should not be used as a substitute for professional medical advice, diagnosis, treatment, or judgment. Similarly, it is not intended as a substitute for professional financial advice or judgment.

**High-Risk Use:**
BY ACCESSING OR USING THE SOFTWARE, YOU ACKNOWLEDGE THAT THE SOFTWARE IS NOT DESIGNED OR INTENDED TO SUPPORT ANY USE IN WHICH A SERVICE INTERRUPTION, DEFECT, ERROR, OR OTHER FAILURE COULD RESULT IN DEATH OR SERIOUS BODILY INJURY OF ANY PERSON OR IN PHYSICAL OR ENVIRONMENTAL DAMAGE. YOUR HIGH-RISK USE OF THE SOFTWARE IS AT YOUR OWN RISK.

---

## 🎯 Support and Feedback

- 🐛 **Issues**: Report bugs or request features via [GitHub Issues](https://github.com/Azure-Samples/azure-app-service-ai-scenarios-integrated-sample/issues)
- 💬 **Questions**: Use [GitHub Discussions](https://github.com/Azure-Samples/azure-app-service-ai-scenarios-integrated-sample/discussions) for implementation questions  
- ⭐ **Rate the Sample**: Star the [repository](https://github.com/Azure-Samples/azure-app-service-ai-scenarios-integrated-sample) if this helped your project

---

## �📚 References

### **Implementation Guides**
- **[Project Structure](docs/PROJECT_STRUCTURE.md)** - Learn the high-level constructs and architecture
- **[Configuration Guide](docs/CONFIGURATION_GUIDE.md)** - Understand configuration options and environment setup
- **[Testing Guide](docs/TESTING_GUIDE.md)** - Learn how to test the application locally and on Azure

### **Azure AI Foundry Documentation**
- **[Chat Completions](https://learn.microsoft.com/en-us/azure/ai-foundry/foundry-models/how-to/use-chat-completions?tabs=python)** - Basic conversational AI implementation
- **[Reasoning Models](https://learn.microsoft.com/en-us/azure/ai-foundry/foundry-models/how-to/use-chat-reasoning?tabs=openai&pivots=programming-language-python)** - Advanced reasoning capabilities  
- **[Multimodal AI](https://learn.microsoft.com/en-us/azure/ai-foundry/foundry-models/how-to/use-chat-multi-modal?pivots=programming-language-python)** - Image and audio processing
- **[Structured Outputs](https://learn.microsoft.com/en-us/azure/ai-foundry/foundry-models/how-to/use-structured-outputs?pivots=programming-language-python)** - JSON schema validation

---

**� Ready to implement AI scenarios in your application? Start with the Quick Start guide above!**