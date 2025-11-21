# Files to Remove for Production Optimization

This document provides a comprehensive analysis of files and code sections that should be removed or optimized for production deployment.

## Critical Removals (Must Remove Before Production)

### Complete Directories to Remove

#### 1. `temp-logs/` Directory
**Reason**: Should not be in source control
**Files**: All deployment logs, status files
**Action**: Remove entire directory, add to `.gitignore`
```bash
# Remove directory
rm -rf temp-logs/
# Add to .gitignore
echo "temp-logs/" >> .gitignore
```

#### 2. `to_be_deleted/` Directory  
**Reason**: Explicitly marked for deletion
**Files**: 
- `postdeploy.ps1` (4 lines)
- `postdeploy.sh` (4 lines)  
- `setup-keyvault-secrets.ps1` (119 lines)
- `setup-keyvault-secrets.sh` (108 lines)
**Action**: Remove entire directory
```bash
rm -rf to_be_deleted/
```

#### 3. `infra/archive/` Directory
**Reason**: Archived/outdated infrastructure templates
**Files**:
- `api-update.bicep` (116 lines)
- `main.json` (outdated ARM template)
- `managed-identity.bicep` (22 lines)
- `keyvault/` subdirectory (2 files, 167 total lines)
- `search/` subdirectory (1 file, 61 lines)
**Action**: Remove entire directory
```bash
rm -rf infra/archive/
```
**Impact**: Removes ~366 lines of outdated infrastructure code

#### 4. `__pycache__/` Directories
**Reason**: Python bytecode should not be in source control
**Locations**: 
- Root `__pycache__/`
- `AIPlaygroundCode/__pycache__/`
- `AIPlaygroundCode/scenarios/__pycache__/`
- `AIPlaygroundCode/utils/__pycache__/`
**Action**: Remove all and update `.gitignore`
```bash
find . -name "__pycache__" -type d -exec rm -rf {} +
echo "__pycache__/" >> .gitignore
echo "*.pyc" >> .gitignore
```

### Individual Files to Remove

#### 5. Development/Testing Files
- `test_setup.py` - Basic setup test, redundant with main test suite
- `setup.py` - Manual setup script, replaced by automated deployment
- `wsgi.py` - Not used (Flask runs directly)

## Code Sections to Remove from Existing Files

### app.py Optimizations

#### Remove Development Routes (Lines 380-429)
```python
# REMOVE: Debug and testing routes
@app.route('/debug_config')
@app.route('/reset-config', methods=['POST']) 
@app.route('/testing_interface')
@app.route('/testing_interface/<scenario>')
```
**Impact**: Removes 50 lines of debug-only functionality

#### Remove Administrative Routes  
```python
# REMOVE: Admin functionality not needed in production
@app.route('/admin')
@app.route('/clear_uploads', methods=['POST'])
```
**Impact**: Removes administrative overhead

### AIPlaygroundCode/config.py Optimizations

#### Remove Deprecated Configuration Methods (Lines 450-580)
```python
# REMOVE: Legacy Key Vault integration (archived)
def _try_keyvault_config(self) -> Optional[Dict[str, Any]]:
    # ~50 lines of outdated Key Vault logic

# REMOVE: Environment variable migration logic  
def _migrate_legacy_env_vars(self) -> Dict[str, str]:
    # ~80 lines of migration code for old environment variables
```
**Impact**: Removes 130 lines of deprecated functionality

#### Simplify Environment Detection (Lines 200-350)
```python
# SIMPLIFY: Overly complex environment detection
# Current: 150 lines of environment detection logic
# Target: 30 lines with clear hierarchy
```
**Impact**: Reduces complexity by ~120 lines

### AIPlaygroundCode/scenarios/ Optimizations  

#### Remove Fallback Azure AI Inference Code
**Files**: `chat.py`, `multimodal.py`, `reasoning.py`, `structured_output.py`
```python
# REMOVE: Fallback to azure.ai.inference in all scenario files
# Use OpenAI SDK consistently
try:
    # OpenAI SDK code
except ImportError:
    # Remove this entire fallback block (~20 lines per file)
    pass
```
**Impact**: Removes ~80 lines across 4 files, simplifies dependencies

### Infrastructure Optimizations

#### infra/main.bicep Simplifications
```bicep
// REMOVE: Unused parameters (Lines 15-40)
param enableAIFoundryIntegration bool = false  // Not used
param searchServiceName string = ''             // Archived feature  
param keyVaultName string = ''                 // Deprecated approach

// REMOVE: Complex conditional deployments (Lines 100-150)
// Simplify AI service deployment logic

// REMOVE: Search service module reference (Lines 180-200)
// This was moved to archive
```
**Impact**: Removes ~100 lines of unused Bicep code

#### infra/api.bicep Optimizations
```bicep
// REMOVE: Complex app settings conditional logic (Lines 50-90)
// Simplify to essential app settings only

// REMOVE: Key Vault secret references (Lines 120-140)  
// Use Managed Identity with direct service connection
```
**Impact**: Removes ~60 lines of complex configuration logic

## Dependency Optimizations

### requirements.txt Cleanup
```requirements.txt
# REMOVE: Unused dependencies
python-dotenv==1.0.0      # Not needed with proper config
requests==2.31.0          # Not directly used

# CONSIDER REMOVING: Redundant AI libraries  
azure-ai-inference==1.0.0b4  # Use OpenAI SDK only for consistency

# KEEP ESSENTIAL ONLY:
Flask==3.0.0
openai==1.54.4
azure-identity==1.19.0
azure-cognitiveservices-speech==1.40.0
Pillow==10.4.0
```
**Impact**: Reduces dependencies from 8 to 5, simplifies deployment

### Package Import Optimizations
```python
# In multiple files, remove unused imports:
# from azure.ai.inference import ChatCompletionsClient  # Not used consistently
# import requests  # Not used directly
# from dotenv import load_dotenv  # Remove with python-dotenv
```

## Test File Optimizations  

### Move Test Data Out of Source Control
**Current**: `tests/test_inputs/` contains binary test files
**Action**: Move to external storage or generate test data dynamically
```bash
# Move test inputs to Azure Storage or external location
# Keep test structure but remove binary files from repository
```

### Consolidate Test Files
**Current**: 6 separate test files with similar patterns
**Optimize**: 
- Keep `test_simple_chat.py` as integration test example
- Consolidate multimodal tests into single file
- Move complex scenario tests to unit test structure

## File Size Impact Summary

| Category | Current Lines | After Removal | Reduction |
|----------|---------------|---------------|-----------|
| Infrastructure | ~800 lines | ~500 lines | 37% |
| Application Code | ~1200 lines | ~900 lines | 25% |  
| Configuration | ~680 lines | ~400 lines | 41% |
| Test Files | ~400 lines | ~300 lines | 25% |
| **Total** | **~3080 lines** | **~2100 lines** | **32%** |

## Implementation Priority

### Phase 1: Safe Removals (No Risk)
1. ✅ Remove `__pycache__` directories  
2. ✅ Remove `temp-logs/` directory
3. ✅ Remove `to_be_deleted/` directory
4. ✅ Remove `infra/archive/` directory
5. ✅ Update `.gitignore`

### Phase 2: Code Cleanup (Low Risk)
1. ✅ Remove debug routes from `app.py`
2. ✅ Remove unused imports across all files
3. ✅ Clean up `requirements.txt` dependencies
4. ✅ Remove fallback Azure AI Inference code

### Phase 3: Configuration Simplification (Medium Risk)
1. ✅ Simplify `config.py` environment detection
2. ✅ Remove deprecated Key Vault integration
3. ✅ Simplify Bicep templates
4. ✅ Remove unused Bicep parameters

### Phase 4: Structural Changes (Higher Risk - Test Thoroughly)
1. ✅ Reorganize test file structure
2. ✅ Move test data to external storage  
3. ✅ Validate all functionality after cleanup

## Validation Checklist

After each removal phase:

- [ ] Run all existing tests to ensure functionality  
- [ ] Deploy to staging environment and validate
- [ ] Check that all AI scenarios still work
- [ ] Verify configuration loading works in all environments
- [ ] Confirm Azure deployment still functions
- [ ] Test file upload/multimodal functionality
- [ ] Validate that no critical features were accidentally removed

## Rollback Plan

For each phase, maintain:
1. **Git commits** with clear messages for each removal
2. **Backup branches** before major structural changes  
3. **Documentation** of what was removed and why
4. **Test results** showing functionality before and after

---

*This removal plan reduces codebase size by ~32% while maintaining all production functionality and improving maintainability.*