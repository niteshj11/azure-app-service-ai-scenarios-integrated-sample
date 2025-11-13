# 🤖 AI Agent Instructions

**Quick reference guide for AI agents working on this AIPlaygroundCode-based Azure AI project.**

## � Core Architecture

**Key Structure:**
- `AIPlaygroundCode/` - Portable AI package with config.py, scenarios/, utils/, templates/
- `app.py` - Main Flask app with `register_ai_routes(app)`
- Single configuration: `AIPlaygroundCode/settings.json`
- Upload folder: `AIPlaygroundCode/uploads`

**Before Making Changes:**
1. Read `docs/PROJECT_STRUCTURE.md` - Understand current architecture
2. Test locally first, then Azure
3. Use `scripts/cleanup_project.ps1` for cleanup

## 🧪 Testing Protocol

**Local Testing:**
```powershell
# Start app
python app.py

# Test core scenarios (in new terminal)
python tests/test_simple_chat.py popup local basic
python tests/test_multimodal_image.py popup local basic
```

**Azure Testing:**
```powershell
# Deploy
azd up

# Configure at https://[app].azurewebsites.net/settings
# Test
python tests/test_simple_chat.py popup azure basic
```

**Validation:** All tests show "PASSED", check `tests/reports/` for HTML reports

## ⚙️ Configuration Management

**Local:** All settings in `AIPlaygroundCode/settings.json`
**Azure:** Sensitive data → Key Vault, non-sensitive → settings.json
**Settings Page:** `/settings` - configure via web interface with testing

**Key Files:**
- `AIPlaygroundCode/config.py` - Configuration logic
- `AIPlaygroundCode/settings.json` - Main config (upload_folder: "AIPlaygroundCode/uploads")  
- `AIPlaygroundCode/settings.local.json` - Local override (not committed)

## 🧹 Project Cleanup

**Automated cleanup:**
```powershell
.\scripts\cleanup_project.ps1 -Confirm:$false
```

**What it handles:**
- Removes `__pycache__`, `.pyc` files
- Cleans logs, uploads folder
- Removes empty directories  
- Tests application integrity

**Manual checks:**
- Single config.py in `AIPlaygroundCode/` only
- Upload folder at `AIPlaygroundCode/uploads`
- No redundant files

## 🚨 Common Issues

**App won't start:** Check port 5000, stop existing processes
**Tests failing:** Ensure app running, check `/settings` page configuration  
**Config issues:** Verify endpoint URL ends with `/models`, test API key
**Deploy issues:** Clean with `.\scripts\clean-azd-environment.ps1`, retry `azd up`

## � Quick References

**Key Docs:**
- `docs/PROJECT_STRUCTURE.md` - Architecture overview
- `docs/CONFIGURATION_GUIDE.md` - Settings and environment management  
- `docs/PROJECT_CLEANUP_INSTRUCTIONS.md` - Cleanup procedures

**Success Criteria:**
- ✅ Local tests pass
- ✅ Azure tests pass  
- ✅ Clean project structure (use cleanup script)
- ✅ AIPlaygroundCode structure maintained