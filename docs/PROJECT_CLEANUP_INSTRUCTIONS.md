# 🧹 Project Cleanup Instructions

> **Guide for cleaning up AIPlaygroundCode-based projects for production deployment**

## 📋 Overview

This document provides instructions for cleaning up a TechMart AI Chatbot project built on the **AIPlaygroundCode** architecture, removing development artifacts, and preparing it for production deployment.

## 🎯 Cleanup Objectives

- **Reduce package size** for faster Azure deployments
- **Remove development artifacts** that don't belong in production  
- **Maintain AIPlaygroundCode structure** integrity
- **Prepare optimized deployment package** for Azure App Service

---

## 🤖 Automated Cleanup (Recommended)

### ✅ **Quick Cleanup with PowerShell Script**
```powershell
# Automated cleanup - handles most cleanup tasks
.\scripts\cleanup_project.ps1 -Confirm:$false

# Preview changes first (dry run)
.\scripts\cleanup_project.ps1 -DryRun

# Selective cleanup by phase
.\scripts\cleanup_project.ps1 -Phase Runtime  # Just cache/temp files
.\scripts\cleanup_project.ps1 -Phase Docs     # Documentation cleanup
```

**What the script handles automatically:**
• **Python cache cleanup** - Removes all `__pycache__` directories and `.pyc/.pyo` files
• **Log file removal** - Cleans up `app.log`, `cleanup_log.txt`, and other log files  
• **Upload folder management** - Removes root `uploads/` (keeps `AIPlaygroundCode/uploads/`)
• **Backup file cleanup** - Removes `*.backup`, `*.bak`, `*.test` files
• **Documentation consolidation** - Removes redundant docs, keeps 5 essential files
• **Test artifact removal** - Cleans analysis files from `tests/azd-tests/`
• **Empty directory removal** - Finds and removes empty directories
• **Application integrity testing** - Verifies core files remain intact

---

## � Manual Cleanup Tasks

### **Files that Should NOT Exist After Cleanup**

**Removed Files (no longer in codebase):**
- ❌ Root `config.py` - Moved to `AIPlaygroundCode/config.py`
- ❌ `clean_environment_detection.py` - Removed (functionality integrated)
- ❌ `test_config_detection.py` - Removed (redundant testing)
- ❌ `AIPlaygroundCode/config/` folder - Consolidated into single config.py
- ❌ Root `uploads/` directory - Upload folder now in `AIPlaygroundCode/uploads/`
- ❌ All `__pycache__` directories and `.pyc` files - Cleaned by script
- ❌ `docs/archive/` directory - Removed completely (13 redundant files)

### **Files that Should Exist (AIPlaygroundCode Structure)**

**✅ Core Application:**
- `app.py` - Main Flask application with AIPlaygroundCode integration
- `wsgi.py` - Production WSGI entry point with Azure AI Foundry support
- `requirements.txt` - Python dependencies including Azure Identity SDK
- `azure.yaml` - Azure deployment configuration with Azure AI Foundry integration

**✅ AIPlaygroundCode Package:**
- `AIPlaygroundCode/__init__.py` - Package initialization
- `AIPlaygroundCode/config.py` - **SINGLE** configuration file with Azure AI Foundry support
- `AIPlaygroundCode/settings.json` - Configuration with Azure AI Foundry endpoint and `upload_folder: "AIPlaygroundCode/uploads"`
- `AIPlaygroundCode/scenarios/` - AI scenario handlers with multimodal support
- `AIPlaygroundCode/utils/` - Helper utilities with Managed Identity support
- `AIPlaygroundCode/templates/` - Web interface templates

**✅ Essential Documentation (5 files only):**
- `docs/AGENT_INSTRUCTIONS.md`
- `docs/CONFIGURATION_GUIDE.md` 
- `docs/PROJECT_CLEANUP_INSTRUCTIONS.md`
- `docs/PROJECT_STRUCTURE.md`
- `docs/TESTING_GUIDE.md`

---

## 📋 Verification Checklist

### ✅ **Post-Cleanup Verification**

```powershell
# 1. Test application imports and runs
python -c "import sys; sys.path.append('.'); import app; print('✅ Application imports successfully')"
python app.py  # Should start without errors

# 2. Verify AIPlaygroundCode structure integrity
python -c "from AIPlaygroundCode import register_ai_routes; print('✅ AIPlaygroundCode imports correctly')"

# 3. Check upload folder configuration
python -c "from AIPlaygroundCode.config import get_model_config; print(f'Upload folder: {get_model_config().upload_folder}')"
# Should show: AIPlaygroundCode/uploads

# 4. Verify Azure AI Foundry configuration (if configured)
python -c "from AIPlaygroundCode.config import get_model_config; config = get_model_config(); print(f'Endpoint: {config.azure_endpoint}'); print('✅ Configuration loaded')"

# 4. Run core tests
python tests/test_simple_chat.py popup local basic
```

### ✅ **File Structure Validation**

**Required AIPlaygroundCode files:**
- [ ] `AIPlaygroundCode/config.py` exists (single config file)
- [ ] `AIPlaygroundCode/settings.json` has correct upload_folder path
- [ ] No `__pycache__` directories anywhere in project
- [ ] No root `uploads/` directory (should be in AIPlaygroundCode only)
- [ ] Only 5 files in `docs/` directory

**Commands to verify:**
```powershell
# Check for any remaining __pycache__ directories
Get-ChildItem -Recurse -Directory -Name "__pycache__"  # Should return nothing

# Verify single config.py location
Get-ChildItem -Recurse -Name "config.py"  # Should only show AIPlaygroundCode/config.py

# Check upload folder setting
Select-String -Path "AIPlaygroundCode/settings.json" -Pattern "upload_folder"
```

---

## 🚀 Deployment Preparation

### **Azure Deployment Package**
```powershell
# Test Azure packaging
azd package --environment dev --output-path "test-package"

# Verify package contents (should exclude development files)
Expand-Archive "test-package\*.zip" -DestinationPath "test-package\extracted" -Force
Get-ChildItem "test-package\extracted" -Recurse | Select-Object Name, Length
```

### **Expected Package Contents:**
✅ **Include**: `app.py`, `wsgi.py`, `requirements.txt`, entire `AIPlaygroundCode/` folder, `infra/` folder  
❌ **Exclude**: `.git/`, `.vscode/`, `.venv/`, `__pycache__/`, `*.log`, development analysis files

---

## 🎯 Success Criteria

**Cleanup is successful when:**
- ✅ `python app.py` runs without import errors
- ✅ AIPlaygroundCode package imports correctly: `from AIPlaygroundCode import register_ai_routes`
- ✅ Upload folder correctly configured: `AIPlaygroundCode/uploads` (not root)
- ✅ Single config.py location: `AIPlaygroundCode/config.py` only
- ✅ Clean deployment package: No `__pycache__`, logs, or development artifacts
- ✅ Documentation streamlined: Exactly 5 files in `docs/` directory

---

## 📚 Related Files

- `docs/PROJECT_STRUCTURE.md` - AIPlaygroundCode architecture reference
- `scripts/cleanup_project.ps1` - **Primary cleanup tool** (use this for most tasks)
- `AIPlaygroundCode/settings.json` - Configuration with upload_folder path

---

## 📊 **Cleanup Results (Nov 2025)**

**Automated Script Results:**
- **Project size reduction**: 87.58MB → 54.41MB (37.7% reduction)  
- **Files removed**: 49 total files (Python cache, logs, redundant docs, analysis files)
- **Structure optimization**: Single config.py, consolidated documentation, clean AIPlaygroundCode package

**Key Architecture Changes:**
- ✅ **Single Config**: Root config.py removed, only `AIPlaygroundCode/config.py` remains
- ✅ **Upload Management**: Root uploads/ removed, `AIPlaygroundCode/uploads/` configured in settings
- ✅ **Documentation**: 5 essential files only (removed archive/ and 13 redundant documents)  
- ✅ **Package Structure**: Clean AIPlaygroundCode portable integration package

*Use `.\scripts\cleanup_project.ps1` for automated cleanup that maintains AIPlaygroundCode structure integrity.*