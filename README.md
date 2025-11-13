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
- [Azure AI Foundry](https://ai.azure.com) access with model deployments

### One-Command Deployment

1. **Clone and Deploy**
   ```bash
   git clone <repository-url>
   cd ChatBotOpenAIAppService
   azd up
   ```

2. **Configure AI Settings**
   After deployment, open `https://[your-app-name].azurewebsites.net/settings` and configure:
   - ✅ **Azure AI Endpoint**: Your Azure AI Foundry endpoint URL  
   - ✅ **API Key**: Your Azure AI Foundry API key
   - ✅ **Model Name**: Your deployed model (e.g., `gpt-4o-mini`)
   - ✅ **Model Name (Audio)**: Your audio model (e.g., `gpt-4o-mini-audio-preview`)

3. **Test Your Application**
   - Click "🧪 Test Config" to verify connection, then start using AI scenarios!
   - Refer to Usage Examples section below to test manually with sample scenarios

### What Gets Deployed
- ✅ **Azure App Service** (Basic B1 SKU) with Python 3.11 - Estimated cost: ~$13/month
- ✅ **Azure Key Vault** (Standard tier) for secure credential storage - Estimated cost: ~$0.03/month  
- ✅ **Managed Identity** with proper RBAC permissions - No additional cost
- ✅ **Application Insights** (Pay-as-you-go) for monitoring - Estimated cost: ~$2/month for typical usage
- ✅ All necessary Azure resources configured automatically

**Total estimated monthly cost: ~$15/month** (costs may vary based on usage and region)

## 🖥️ Local Development Setup

### Prerequisites
- Python 3.8+ 
- [Azure AI Foundry](https://ai.azure.com) access with model deployments

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
   - ✅ **API Key**: Your Azure AI Foundry API key  
   - ✅ **Model Name**: Your deployed model name (e.g., `gpt-4o-mini`)
   - ✅ **Model Name (Audio)**: Your audio model (e.g., `gpt-4o-mini-audio-preview`)

4. **Test Your Application**
   - Click "🧪 Test Config" to verify connection, then start using AI scenarios!
   - Refer to Usage Examples section below to test manually with sample scenarios

## 💡 Usage Examples

**🤖 Conversational AI**: 
- **Test Message**: "Who are you and what can you help with?"
- **Expected Response**: AI identifies as TechMart Enterprise AI Assistant, explains customer service and business intelligence capabilities

**🛍️ Product Inquiry**:
- **Test Message**: "Tell me about features and price for Pro Gaming X1" 
- **Expected Response**: Details about $1699 price, RTX 4070, Intel i7, 16GB RAM, 1TB SSD specifications

**� Customer Service**:
- **Test Message**: "What is TechMart's return policy and how do I process a customer refund?"
- **Expected Response**: 30-day return policy, receipt requirements, customer service contact information

**🎭 Multimodal Processing**: 
- **Image Analysis**: Upload product images from `tests/test_inputs/laptop.jpeg` for detailed specifications
- **Audio Processing**: Upload audio files from `tests/test_inputs/test_customer_service_audio.mp3` for transcription

**Sample Test Files Available**: Browse `tests/test_inputs/` folder for sample images and audio files to test multimodal capabilities.

## 🎯 Easy Integration for Existing Apps

**Step 1: Copy Required Files**
```bash
# Copy the AIPlaygroundCode folder to your existing Flask app
cp -r AIPlaygroundCode/ /path/to/your-existing-app/

# Copy requirements.txt and wsgi.py if they don't exist in your app
cp requirements.txt /path/to/your-existing-app/  # If not already present
cp wsgi.py /path/to/your-existing-app/          # If not already present  
```

**Step 2: Add AI Routes to Your Flask App**
Add the following route imports to your main Flask application file (e.g., `app.py`):
```python
# Add these imports to your existing app.py
from AIPlaygroundCode.config import get_model_config, update_model_config, is_configured
from AIPlaygroundCode.scenarios.chat import handle_chat_message
from AIPlaygroundCode.scenarios.multimodal import handle_multimodal_message

# Add this route for settings configuration
@app.route('/settings')
def settings():
    from flask import render_template
    config = get_model_config()
    return render_template('AIPlaygroundCode/templates/settings.html', config=config)

@app.route('/settings', methods=['POST'])
def update_settings():
    # Add settings update logic from the sample app.py
    pass
```

**Step 3: Add Popup Interface to Your Templates**
Copy this code snippet into your existing HTML templates where you want the AI chat button:
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

#### What You Get:
- 🎯 **New Routes**: `/settings` for AI configuration
- ⚙️ **Settings Page**: Self-service configuration interface for AI credentials  
- 💬 **Popup Chat Interface**: Floating AI assistant accessible from any page  

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

### **Troubleshooting Common Deployment Issues**

**❌ "Endpoint not found" or 401 Authentication errors:**
- Verify your Azure AI Foundry endpoint URL ends with `/models` 
- Ensure your API key is correct and active
- Use the "🧪 Test Config" button to validate credentials
- Check that your model deployment is active in Azure AI Foundry

**❌ Azure deployment fails with "azd up" command:**
- Ensure you have Contributor access to your Azure subscription
- Check if you've reached subscription limits for App Service or AI services
- Try running `azd auth login` to refresh your authentication
- Clear previous deployments with `azd down` before retrying

**❌ Application not starting after deployment:**
- Check Application Insights logs in Azure portal for detailed errors
- Verify Key Vault permissions are properly configured
- Ensure all required environment variables are set in App Service Configuration

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

- **Azure App Service**: Basic B1 tier with 1.75 GB RAM, 10 GB storage. [Pricing](https://azure.microsoft.com/pricing/details/app-service/windows/)
- **Azure Key Vault**: Standard tier for secure credential storage. [Pricing](https://azure.microsoft.com/pricing/details/key-vault/)  
- **Application Insights**: Pay-as-you-go tier for monitoring and telemetry. [Pricing](https://azure.microsoft.com/pricing/details/monitor/)
- **Azure AI Services**: Consumption-based pricing for model usage (tokens). [Pricing](https://azure.microsoft.com/pricing/details/cognitive-services/openai-service/)

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

## � Support and Feedback

- 🐛 **Issues**: Report bugs or request features via [GitHub issues](https://github.com/Azure-Samples/azure-app-service-ai-scenarios-integrated-sample/issues)
- 💬 **Questions**: Use [GitHub Discussions](https://github.com/Azure-Samples/azure-app-service-ai-scenarios-integrated-sample/discussions) for implementation questions
- ⭐ **Rate the Sample**: Star the repository if this helped your project

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